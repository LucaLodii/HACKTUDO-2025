"""
Authentication Management Tool for sofIA Agent

Provides enterprise authentication capabilities including service account
management and OAuth2/OpenID Connect integration with Vertex AI.
"""

from google.adk.tools import Tool
from typing import Dict, Any, Optional
import json

from ...auth import ServiceAccountManager, VertexAIAuthenticator


def authenticate_service_account(
    account_id: str,
    permissions: list[str] = None
) -> Dict[str, Any]:
    """
    Authenticate using service account credentials.

    Args:
        account_id: Service account identifier
        permissions: Required permissions for the operation

    Returns:
        Authentication status and token information
    """
    try:
        manager = ServiceAccountManager()
        account = manager.get_account(account_id)

        if not account:
            return {
                "success": False,
                "error": f"Service account {account_id} not found"
            }

        # Validate permissions if specified
        if permissions:
            missing_perms = [p for p in permissions if p not in account.permissions]
            if missing_perms:
                return {
                    "success": False,
                    "error": f"Missing permissions: {missing_perms}"
                }

        # Generate JWT token
        token = manager.generate_jwt_token(account_id)

        return {
            "success": True,
            "account_id": account_id,
            "account_type": account.account_type.value,
            "token": token,
            "expires_at": account.expires_at.isoformat() if account.expires_at else None
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Authentication failed: {str(e)}"
        }


def setup_vertex_ai_auth(
    project_id: str,
    service_account_email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Setup Vertex AI authentication with OAuth2/OpenID Connect.

    Args:
        project_id: Google Cloud project ID
        service_account_email: Optional service account email

    Returns:
        Authentication setup status
    """
    try:
        authenticator = VertexAIAuthenticator()

        # Setup authentication
        result = authenticator.setup_authentication(
            project_id=project_id,
            service_account_email=service_account_email
        )

        return {
            "success": True,
            "project_id": project_id,
            "service_account": result.get("service_account"),
            "vertex_ai_enabled": True,
            "token_info": result.get("token_info")
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Vertex AI authentication setup failed: {str(e)}"
        }


def rotate_credentials(account_id: str) -> Dict[str, Any]:
    """
    Rotate service account credentials.

    Args:
        account_id: Service account identifier

    Returns:
        Credential rotation status
    """
    try:
        manager = ServiceAccountManager()
        success = manager.rotate_credentials(account_id)

        if success:
            return {
                "success": True,
                "account_id": account_id,
                "message": "Credentials rotated successfully"
            }
        else:
            return {
                "success": False,
                "error": "Failed to rotate credentials"
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Credential rotation failed: {str(e)}"
        }


auth_tool = Tool(
    name="auth_management",
    description="Enterprise authentication management including service accounts and Vertex AI OAuth2",
    function_declarations=[
        {
            "name": "authenticate_service_account",
            "description": "Authenticate using service account credentials",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Service account identifier"
                    },
                    "permissions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Required permissions for the operation"
                    }
                },
                "required": ["account_id"]
            }
        },
        {
            "name": "setup_vertex_ai_auth",
            "description": "Setup Vertex AI authentication with OAuth2/OpenID Connect",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Google Cloud project ID"
                    },
                    "service_account_email": {
                        "type": "string",
                        "description": "Optional service account email"
                    }
                },
                "required": ["project_id"]
            }
        },
        {
            "name": "rotate_credentials",
            "description": "Rotate service account credentials",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": "Service account identifier"
                    }
                },
                "required": ["account_id"]
            }
        }
    ],
    functions={
        "authenticate_service_account": authenticate_service_account,
        "setup_vertex_ai_auth": setup_vertex_ai_auth,
        "rotate_credentials": rotate_credentials
    }
)