"""
Vertex AI OAuth2/OpenID Connect Authentication

Implements proper Google Cloud service account authentication for Vertex AI
instead of basic API key authentication for production deployment.
"""

import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import os
from pathlib import Path
import aiohttp
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from google.auth import jwt as google_jwt
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import google.auth


class VertexAIAuthenticator:
    """
    Vertex AI Authentication with OAuth2/OpenID Connect

    Implements proper Google Cloud service account authentication
    for production Vertex AI usage instead of basic API key auth.
    """

    def __init__(
        self,
        service_account_path: Optional[str] = None,
        project_id: Optional[str] = None,
        scopes: Optional[List[str]] = None
    ):
        self.service_account_path = service_account_path
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")

        # Default scopes for Vertex AI
        self.scopes = scopes or [
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/cloud-platform.read-only",
            "https://www.googleapis.com/auth/generative-language"
        ]

        # Authentication state
        self.credentials = None
        self.access_token = None
        self.token_expires_at = None
        self.service_account_info = None

        # Token refresh settings
        self.token_refresh_buffer_minutes = 5

    async def initialize(self) -> bool:
        """
        Initialize Vertex AI authentication.

        Returns:
            Success status
        """
        try:
            # Try different authentication methods in order of preference

            # 1. Service account file (most secure for production)
            if self.service_account_path and os.path.exists(self.service_account_path):
                await self._initialize_service_account_file()

            # 2. Service account from environment variable
            elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                await self._initialize_from_environment()

            # 3. Application Default Credentials (for development)
            elif await self._try_application_default_credentials():
                pass  # Already initialized

            # 4. Create service account if none exists (development only)
            else:
                await self._create_development_service_account()

            # Validate credentials
            if await self._validate_credentials():
                print("✅ Vertex AI authentication initialized successfully")
                return True
            else:
                print("❌ Failed to validate Vertex AI credentials")
                return False

        except Exception as e:
            print(f"❌ Vertex AI authentication initialization failed: {e}")
            return False

    async def get_access_token(self) -> Optional[str]:
        """
        Get valid access token for Vertex AI API calls.

        Returns:
            Access token if available
        """
        # Check if token needs refresh
        if await self._needs_token_refresh():
            await self._refresh_access_token()

        return self.access_token

    async def get_authenticated_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers with authentication for Vertex AI API calls.

        Returns:
            Headers dictionary with authorization
        """
        token = await self.get_access_token()
        if not token:
            raise ValueError("No valid access token available")

        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "sofIA-Platform/1.0"
        }

    async def create_service_account(
        self,
        account_name: str,
        display_name: str,
        description: str,
        key_file_path: str
    ) -> bool:
        """
        Create a new service account for Vertex AI access.

        Args:
            account_name: Service account name
            display_name: Human-readable display name
            description: Account description
            key_file_path: Path to save the service account key

        Returns:
            Success status
        """
        try:
            if not self.project_id:
                raise ValueError("Project ID required to create service account")

            # Get current credentials for IAM API
            token = await self.get_access_token()
            if not token:
                raise ValueError("Valid credentials required to create service account")

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # Create service account
            create_url = f"https://iam.googleapis.com/v1/projects/{self.project_id}/serviceAccounts"
            create_data = {
                "accountId": account_name,
                "serviceAccount": {
                    "displayName": display_name,
                    "description": description
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(create_url, json=create_data, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ValueError(f"Failed to create service account: {error_text}")

                    account_data = await response.json()
                    account_email = account_data["email"]

            # Create and download key
            key_url = f"https://iam.googleapis.com/v1/projects/{self.project_id}/serviceAccounts/{account_email}/keys"
            key_data = {
                "keyAlgorithm": "KEY_ALG_RSA_2048",
                "privateKeyType": "TYPE_GOOGLE_CREDENTIALS_FILE"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(key_url, json=key_data, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ValueError(f"Failed to create service account key: {error_text}")

                    key_response = await response.json()
                    private_key_data = key_response["privateKeyData"]

            # Decode and save key file
            import base64
            key_content = base64.b64decode(private_key_data).decode('utf-8')

            Path(key_file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(key_file_path, 'w') as f:
                f.write(key_content)

            # Grant necessary IAM roles
            await self._grant_vertex_ai_roles(account_email)

            print(f"✅ Created service account: {account_email}")
            print(f"📄 Saved key file: {key_file_path}")

            return True

        except Exception as e:
            print(f"❌ Failed to create service account: {e}")
            return False

    async def validate_vertex_ai_access(self) -> bool:
        """
        Validate that current credentials have Vertex AI access.

        Returns:
            True if Vertex AI access is available
        """
        try:
            if not self.project_id:
                print("❌ Project ID not configured")
                return False

            headers = await self.get_authenticated_headers()

            # Test Vertex AI API access
            test_url = f"https://aiplatform.googleapis.com/v1/projects/{self.project_id}/locations"

            async with aiohttp.ClientSession() as session:
                async with session.get(test_url, headers=headers) as response:
                    if response.status == 200:
                        print("✅ Vertex AI API access validated")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ Vertex AI API access failed: {response.status} - {error_text}")
                        return False

        except Exception as e:
            print(f"❌ Vertex AI validation error: {e}")
            return False

    async def get_vertex_ai_endpoint(self, location: str = "us-central1") -> str:
        """
        Get Vertex AI endpoint URL for API calls.

        Args:
            location: GCP region for Vertex AI

        Returns:
            Vertex AI endpoint URL
        """
        if not self.project_id:
            raise ValueError("Project ID required for Vertex AI endpoint")

        return f"https://{location}-aiplatform.googleapis.com/v1/projects/{self.project_id}/locations/{location}"

    async def create_vertex_ai_request(
        self,
        endpoint_path: str,
        request_data: Dict[str, Any],
        location: str = "us-central1"
    ) -> Optional[Dict[str, Any]]:
        """
        Make authenticated request to Vertex AI API.

        Args:
            endpoint_path: API endpoint path
            request_data: Request payload
            location: GCP region

        Returns:
            API response data
        """
        try:
            base_url = await self.get_vertex_ai_endpoint(location)
            full_url = f"{base_url}/{endpoint_path}"
            headers = await self.get_authenticated_headers()

            async with aiohttp.ClientSession() as session:
                async with session.post(full_url, json=request_data, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        print(f"❌ Vertex AI API request failed: {response.status} - {error_text}")
                        return None

        except Exception as e:
            print(f"❌ Vertex AI request error: {e}")
            return None

    async def get_authentication_info(self) -> Dict[str, Any]:
        """Get information about current authentication state."""
        return {
            "authenticated": self.credentials is not None,
            "project_id": self.project_id,
            "service_account_email": self.service_account_info.get("client_email") if self.service_account_info else None,
            "token_expires_at": self.token_expires_at.isoformat() if self.token_expires_at else None,
            "scopes": self.scopes,
            "auth_method": self._get_auth_method()
        }

    # Private methods

    async def _initialize_service_account_file(self):
        """Initialize using service account file."""
        with open(self.service_account_path, 'r') as f:
            self.service_account_info = json.load(f)

        self.credentials = service_account.Credentials.from_service_account_file(
            self.service_account_path,
            scopes=self.scopes
        )

        if not self.project_id:
            self.project_id = self.service_account_info.get("project_id")

        await self._refresh_access_token()
        print(f"✅ Initialized with service account file: {self.service_account_path}")

    async def _initialize_from_environment(self):
        """Initialize using GOOGLE_APPLICATION_CREDENTIALS environment variable."""
        self.service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        await self._initialize_service_account_file()

    async def _try_application_default_credentials(self) -> bool:
        """Try to use Application Default Credentials."""
        try:
            credentials, project = google.auth.default(scopes=self.scopes)
            self.credentials = credentials
            if not self.project_id:
                self.project_id = project

            await self._refresh_access_token()
            print("✅ Initialized with Application Default Credentials")
            return True

        except Exception as e:
            print(f"⚠️ Application Default Credentials not available: {e}")
            return False

    async def _create_development_service_account(self):
        """Create a development service account (for development only)."""
        print("⚠️ No authentication configured - creating development service account")

        if not self.project_id:
            self.project_id = input("Enter your Google Cloud Project ID: ").strip()

        # This would guide the user through creating a service account
        account_name = "sofia-dev-service-account"
        key_file = "sofia-dev-credentials.json"

        print(f"""
🔧 Development Setup Required:

1. Go to Google Cloud Console: https://console.cloud.google.com/
2. Select project: {self.project_id}
3. Navigate to IAM & Admin > Service Accounts
4. Create a new service account named: {account_name}
5. Grant the following roles:
   - AI Platform Developer
   - Vertex AI User
6. Create and download a JSON key file
7. Save the key file as: {key_file}
8. Set environment variable: GOOGLE_APPLICATION_CREDENTIALS={key_file}

Or use this command to set it up automatically:
gcloud iam service-accounts create {account_name} --project={self.project_id}
gcloud projects add-iam-policy-binding {self.project_id} --member="serviceAccount:{account_name}@{self.project_id}.iam.gserviceaccount.com" --role="roles/aiplatform.user"
gcloud iam service-accounts keys create {key_file} --iam-account="{account_name}@{self.project_id}.iam.gserviceaccount.com"
""")

        raise ValueError("Manual service account setup required")

    async def _needs_token_refresh(self) -> bool:
        """Check if access token needs to be refreshed."""
        if not self.access_token or not self.token_expires_at:
            return True

        # Refresh if token expires within buffer time
        buffer_time = timedelta(minutes=self.token_refresh_buffer_minutes)
        refresh_time = self.token_expires_at - buffer_time

        return datetime.now(timezone.utc) >= refresh_time

    async def _refresh_access_token(self):
        """Refresh the access token."""
        if not self.credentials:
            raise ValueError("No credentials available for token refresh")

        # Refresh token
        request = Request()
        self.credentials.refresh(request)

        self.access_token = self.credentials.token

        # Calculate expiry time
        if hasattr(self.credentials, 'expiry') and self.credentials.expiry:
            self.token_expires_at = self.credentials.expiry.replace(tzinfo=timezone.utc)
        else:
            # Default to 1 hour if no expiry available
            self.token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        print("🔄 Refreshed Vertex AI access token")

    async def _validate_credentials(self) -> bool:
        """Validate that credentials are working."""
        try:
            if not self.access_token:
                return False

            # Test token with a simple API call
            headers = await self.get_authenticated_headers()
            test_url = f"https://cloudresourcemanager.googleapis.com/v1/projects/{self.project_id}"

            async with aiohttp.ClientSession() as session:
                async with session.get(test_url, headers=headers) as response:
                    return response.status == 200

        except Exception:
            return False

    async def _grant_vertex_ai_roles(self, service_account_email: str):
        """Grant necessary IAM roles to service account."""
        roles_to_grant = [
            "roles/aiplatform.user",
            "roles/ml.developer",
            "roles/serviceusage.serviceUsageConsumer"
        ]

        token = await self.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        for role in roles_to_grant:
            try:
                # Get current IAM policy
                policy_url = f"https://cloudresourcemanager.googleapis.com/v1/projects/{self.project_id}:getIamPolicy"

                async with aiohttp.ClientSession() as session:
                    async with session.post(policy_url, headers=headers) as response:
                        if response.status != 200:
                            continue

                        policy = await response.json()

                # Add binding
                binding = {
                    "role": role,
                    "members": [f"serviceAccount:{service_account_email}"]
                }

                if "bindings" not in policy:
                    policy["bindings"] = []

                # Check if binding already exists
                existing_binding = None
                for b in policy["bindings"]:
                    if b["role"] == role:
                        existing_binding = b
                        break

                if existing_binding:
                    if f"serviceAccount:{service_account_email}" not in existing_binding["members"]:
                        existing_binding["members"].append(f"serviceAccount:{service_account_email}")
                else:
                    policy["bindings"].append(binding)

                # Set updated policy
                set_policy_url = f"https://cloudresourcemanager.googleapis.com/v1/projects/{self.project_id}:setIamPolicy"
                set_policy_data = {"policy": policy}

                async with aiohttp.ClientSession() as session:
                    async with session.post(set_policy_url, json=set_policy_data, headers=headers) as response:
                        if response.status == 200:
                            print(f"✅ Granted role {role} to {service_account_email}")
                        else:
                            print(f"⚠️ Failed to grant role {role}")

            except Exception as e:
                print(f"⚠️ Error granting role {role}: {e}")

    def _get_auth_method(self) -> str:
        """Get description of current authentication method."""
        if self.service_account_path:
            return f"Service Account File: {self.service_account_path}"
        elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            return f"Environment Variable: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}"
        elif self.credentials:
            return "Application Default Credentials"
        else:
            return "Not Authenticated"


# Integration helper functions

async def setup_vertex_ai_authentication(
    project_id: Optional[str] = None,
    service_account_path: Optional[str] = None
) -> VertexAIAuthenticator:
    """
    Set up Vertex AI authentication for the sofIA platform.

    Args:
        project_id: Google Cloud Project ID
        service_account_path: Path to service account JSON file

    Returns:
        Configured VertexAIAuthenticator instance
    """
    authenticator = VertexAIAuthenticator(
        service_account_path=service_account_path,
        project_id=project_id
    )

    if await authenticator.initialize():
        return authenticator
    else:
        raise ValueError("Failed to initialize Vertex AI authentication")


async def create_vertex_ai_agent_credentials(
    agent_name: str,
    project_id: str,
    key_output_path: str
) -> bool:
    """
    Create service account credentials for a sofIA agent.

    Args:
        agent_name: Name of the agent
        project_id: Google Cloud Project ID
        key_output_path: Where to save the credentials file

    Returns:
        Success status
    """
    authenticator = VertexAIAuthenticator(project_id=project_id)

    if not await authenticator.initialize():
        print("❌ Failed to initialize authentication for credential creation")
        return False

    account_name = f"sofia-agent-{agent_name.lower().replace('_', '-')}"
    display_name = f"sofIA Agent: {agent_name}"
    description = f"Service account for sofIA agent {agent_name} with Vertex AI access"

    return await authenticator.create_service_account(
        account_name=account_name,
        display_name=display_name,
        description=description,
        key_file_path=key_output_path
    )


# Environment configuration helper

def configure_vertex_ai_environment():
    """Configure environment variables for Vertex AI authentication."""
    print("""
🔧 Vertex AI Authentication Configuration

Add these environment variables to your .env file:

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json

# Vertex AI Configuration
GOOGLE_GENAI_USE_VERTEXAI=1
VERTEX_AI_LOCATION=us-central1

# Remove legacy API key (replace with service account)
# GOOGLE_API_KEY=your-api-key  # Remove this line

For production deployment, also set:
GOOGLE_CLOUD_REGION=us-central1
VERTEX_AI_ENDPOINT_ID=your-endpoint-id
""")


# Migration helper from API key to service account

async def migrate_from_api_key_to_service_account(
    current_api_key: str,
    project_id: str,
    output_credentials_path: str
) -> bool:
    """
    Help migrate from API key authentication to service account.

    Args:
        current_api_key: Current API key (will be deprecated)
        project_id: Google Cloud Project ID
        output_credentials_path: Where to save new service account credentials

    Returns:
        Success status of migration
    """
    print("🔄 Migrating from API key to service account authentication...")

    # Validate current API key still works
    test_url = "https://generativelanguage.googleapis.com/v1/models"
    headers = {"x-goog-api-key": current_api_key}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(test_url, headers=headers) as response:
                if response.status != 200:
                    print("⚠️ Current API key appears to be invalid")
                    return False
    except Exception as e:
        print(f"⚠️ Error testing current API key: {e}")
        return False

    # Create new service account
    success = await create_vertex_ai_agent_credentials(
        agent_name="sofia-main",
        project_id=project_id,
        key_output_path=output_credentials_path
    )

    if success:
        print(f"""
✅ Migration successful!

Next steps:
1. Update your .env file:
   - Remove: GOOGLE_API_KEY={current_api_key}
   - Add: GOOGLE_APPLICATION_CREDENTIALS={output_credentials_path}
   - Add: GOOGLE_CLOUD_PROJECT={project_id}
   - Add: GOOGLE_GENAI_USE_VERTEXAI=1

2. Test the new authentication:
   python -c "from sofIA.auth.vertex_ai_auth import setup_vertex_ai_authentication; import asyncio; asyncio.run(setup_vertex_ai_authentication())"

3. Update your agent initialization code to use VertexAIAuthenticator

4. Revoke the old API key from Google Cloud Console for security
""")
        return True
    else:
        print("❌ Migration failed - keeping current API key configuration")
        return False