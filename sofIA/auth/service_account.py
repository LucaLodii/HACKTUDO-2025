"""
Service Account Authentication System

Implements enterprise-grade service account management with proper
credential rotation, access control, and audit trails for production deployment.
"""

import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import hashlib
import secrets
from pathlib import Path
import aiosqlite
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import jwt


class AccountType(Enum):
    """Types of service accounts."""
    AGENT = "agent"
    MERCHANT = "merchant"
    PAYMENT_GATEWAY = "payment_gateway"
    COMPLIANCE_SERVICE = "compliance_service"
    MONITORING_SERVICE = "monitoring_service"
    ADMIN = "admin"


class Permission(Enum):
    """Granular permissions for service accounts."""
    # Agent permissions
    AGENT_DISCOVERY = "agent:discovery"
    AGENT_COMMUNICATION = "agent:communication"
    AGENT_REGISTRATION = "agent:registration"

    # Payment permissions
    PAYMENT_PROCESSING = "payment:processing"
    PAYMENT_REFUND = "payment:refund"
    PAYMENT_DISPUTE = "payment:dispute"

    # Mandate permissions
    MANDATE_CREATE = "mandate:create"
    MANDATE_VERIFY = "mandate:verify"
    MANDATE_SIGN = "mandate:sign"

    # Credential permissions
    CREDENTIAL_ISSUE = "credential:issue"
    CREDENTIAL_VERIFY = "credential:verify"
    CREDENTIAL_REVOKE = "credential:revoke"

    # Ledger permissions
    LEDGER_READ = "ledger:read"
    LEDGER_WRITE = "ledger:write"
    LEDGER_AUDIT = "ledger:audit"

    # Admin permissions
    ADMIN_USER_MANAGEMENT = "admin:user_management"
    ADMIN_SYSTEM_CONFIG = "admin:system_config"
    ADMIN_SECURITY_AUDIT = "admin:security_audit"


@dataclass
class ServiceAccount:
    """Service account with credentials and permissions."""
    account_id: str
    account_type: AccountType
    name: str
    description: str

    # Credentials
    client_id: str
    client_secret_hash: str
    private_key_pem: Optional[str]
    public_key_pem: Optional[str]

    # Access control
    permissions: Set[Permission]
    scopes: Set[str]
    allowed_origins: List[str]

    # Lifecycle
    created_at: datetime
    expires_at: Optional[datetime]
    last_rotation: datetime
    rotation_interval_days: int

    # Status
    is_active: bool
    is_locked: bool
    failed_auth_count: int
    last_used: Optional[datetime]

    # Metadata
    metadata: Dict[str, Any]


class ServiceAccountManager:
    """
    Enterprise Service Account Management System

    Provides secure service account lifecycle management with proper
    credential rotation, access control, and comprehensive audit trails.
    """

    def __init__(
        self,
        database_path: str = "service_accounts.db",
        default_rotation_days: int = 90
    ):
        self.database_path = database_path
        self.default_rotation_days = default_rotation_days

        # In-memory cache for active accounts
        self.account_cache: Dict[str, ServiceAccount] = {}

        # Security configuration
        self.max_failed_attempts = 5
        self.lockout_duration_hours = 24
        self.token_lifetime_hours = 1

        # Initialize system
        asyncio.create_task(self._initialize_system())

    async def create_service_account(
        self,
        account_type: AccountType,
        name: str,
        description: str,
        permissions: Set[Permission],
        scopes: Optional[Set[str]] = None,
        allowed_origins: Optional[List[str]] = None,
        expires_in_days: Optional[int] = None,
        rotation_interval_days: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Create a new service account.

        Args:
            account_type: Type of service account
            name: Human-readable name
            description: Account description
            permissions: Set of permissions
            scopes: OAuth2 scopes (optional)
            allowed_origins: Allowed origin domains
            expires_in_days: Account expiration (optional)
            rotation_interval_days: Credential rotation interval
            metadata: Additional metadata

        Returns:
            Dict containing account credentials (client_id, client_secret, etc.)
        """
        # Generate account ID
        account_id = f"sa_{account_type.value}_{uuid.uuid4().hex[:12]}"

        # Generate credentials
        client_id = f"client_{uuid.uuid4().hex[:16]}"
        client_secret = secrets.token_urlsafe(32)
        client_secret_hash = self._hash_secret(client_secret)

        # Generate RSA key pair for JWT signing
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()

        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()

        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

        # Set expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        # Create service account
        service_account = ServiceAccount(
            account_id=account_id,
            account_type=account_type,
            name=name,
            description=description,
            client_id=client_id,
            client_secret_hash=client_secret_hash,
            private_key_pem=private_key_pem,
            public_key_pem=public_key_pem,
            permissions=permissions,
            scopes=scopes or set(),
            allowed_origins=allowed_origins or [],
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            last_rotation=datetime.now(timezone.utc),
            rotation_interval_days=rotation_interval_days or self.default_rotation_days,
            is_active=True,
            is_locked=False,
            failed_auth_count=0,
            last_used=None,
            metadata=metadata or {}
        )

        # Store account
        await self._store_service_account(service_account)
        self.account_cache[client_id] = service_account

        print(f"✅ Created service account: {name} ({account_type.value})")

        # Return credentials (client_secret is only returned once)
        return {
            "account_id": account_id,
            "client_id": client_id,
            "client_secret": client_secret,
            "public_key": public_key_pem,
            "token_endpoint": "/auth/token",
            "expires_at": expires_at.isoformat() if expires_at else None
        }

    async def authenticate_service_account(
        self,
        client_id: str,
        client_secret: str,
        origin: Optional[str] = None
    ) -> Optional[str]:
        """
        Authenticate a service account and return JWT token.

        Args:
            client_id: Client identifier
            client_secret: Client secret
            origin: Request origin for validation

        Returns:
            JWT access token if authentication successful
        """
        # Get service account
        account = await self._get_service_account(client_id)
        if not account:
            print(f"❌ Service account not found: {client_id}")
            return None

        # Check if account is active
        if not account.is_active or account.is_locked:
            print(f"❌ Service account inactive or locked: {client_id}")
            return None

        # Check expiration
        if account.expires_at and account.expires_at < datetime.now(timezone.utc):
            print(f"❌ Service account expired: {client_id}")
            await self._deactivate_account(account)
            return None

        # Verify client secret
        if not self._verify_secret(client_secret, account.client_secret_hash):
            await self._record_failed_auth(account)
            print(f"❌ Invalid credentials for: {client_id}")
            return None

        # Verify origin if specified
        if origin and account.allowed_origins:
            if not any(origin.endswith(allowed) for allowed in account.allowed_origins):
                print(f"❌ Origin not allowed: {origin} for {client_id}")
                return None

        # Generate JWT token
        token = await self._generate_access_token(account)

        # Update last used
        account.last_used = datetime.now(timezone.utc)
        account.failed_auth_count = 0
        await self._update_service_account(account)

        print(f"✅ Authenticated service account: {client_id}")
        return token

    async def verify_access_token(
        self,
        token: str,
        required_permission: Optional[Permission] = None,
        required_scope: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Verify JWT access token and check permissions.

        Args:
            token: JWT access token
            required_permission: Required permission (optional)
            required_scope: Required OAuth2 scope (optional)

        Returns:
            Token claims if valid, None otherwise
        """
        try:
            # Decode token (we need to get the account to verify signature)
            unverified_claims = jwt.decode(token, options={"verify_signature": False})
            client_id = unverified_claims.get("sub")

            if not client_id:
                return None

            # Get service account for signature verification
            account = await self._get_service_account(client_id)
            if not account or not account.is_active:
                return None

            # Verify token signature
            public_key = serialization.load_pem_public_key(
                account.public_key_pem.encode(),
                backend=default_backend()
            )

            claims = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience="sofia-platform"
            )

            # Check permission if required
            if required_permission:
                account_permissions = {p.value for p in account.permissions}
                if required_permission.value not in account_permissions:
                    print(f"❌ Permission denied: {required_permission.value} for {client_id}")
                    return None

            # Check scope if required
            if required_scope:
                token_scopes = claims.get("scope", "").split()
                if required_scope not in token_scopes:
                    print(f"❌ Scope not granted: {required_scope} for {client_id}")
                    return None

            return claims

        except jwt.ExpiredSignatureError:
            print("❌ Token expired")
            return None
        except jwt.InvalidTokenError as e:
            print(f"❌ Invalid token: {e}")
            return None

    async def rotate_credentials(self, client_id: str) -> Optional[Dict[str, str]]:
        """
        Rotate credentials for a service account.

        Args:
            client_id: Client identifier

        Returns:
            New credentials if successful
        """
        account = await self._get_service_account(client_id)
        if not account:
            return None

        # Generate new credentials
        new_client_secret = secrets.token_urlsafe(32)
        new_client_secret_hash = self._hash_secret(new_client_secret)

        # Generate new RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()

        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()

        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

        # Update account
        account.client_secret_hash = new_client_secret_hash
        account.private_key_pem = private_key_pem
        account.public_key_pem = public_key_pem
        account.last_rotation = datetime.now(timezone.utc)

        await self._update_service_account(account)

        print(f"🔄 Rotated credentials for: {client_id}")

        return {
            "client_id": client_id,
            "client_secret": new_client_secret,
            "public_key": public_key_pem,
            "rotated_at": account.last_rotation.isoformat()
        }

    async def update_permissions(
        self,
        client_id: str,
        permissions: Set[Permission],
        scopes: Optional[Set[str]] = None
    ) -> bool:
        """
        Update permissions for a service account.

        Args:
            client_id: Client identifier
            permissions: New set of permissions
            scopes: New set of scopes (optional)

        Returns:
            Success status
        """
        account = await self._get_service_account(client_id)
        if not account:
            return False

        account.permissions = permissions
        if scopes is not None:
            account.scopes = scopes

        await self._update_service_account(account)

        print(f"🔑 Updated permissions for: {client_id}")
        return True

    async def deactivate_service_account(self, client_id: str) -> bool:
        """Deactivate a service account."""
        account = await self._get_service_account(client_id)
        if not account:
            return False

        await self._deactivate_account(account)
        print(f"🔴 Deactivated service account: {client_id}")
        return True

    async def list_service_accounts(
        self,
        account_type: Optional[AccountType] = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List service accounts with filtering.

        Args:
            account_type: Filter by account type
            active_only: Only return active accounts

        Returns:
            List of service account summaries
        """
        accounts = []

        async with aiosqlite.connect(self.database_path) as db:
            query = "SELECT account_data FROM service_accounts"
            conditions = []
            params = []

            if active_only:
                conditions.append("is_active = 1")

            if account_type:
                conditions.append("account_type = ?")
                params.append(account_type.value)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()

            for row in rows:
                account_data = json.loads(row[0])
                accounts.append({
                    "account_id": account_data["account_id"],
                    "client_id": account_data["client_id"],
                    "name": account_data["name"],
                    "account_type": account_data["account_type"],
                    "created_at": account_data["created_at"],
                    "last_used": account_data.get("last_used"),
                    "is_active": account_data["is_active"],
                    "permissions_count": len(account_data.get("permissions", []))
                })

        return accounts

    async def get_account_usage_stats(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get usage statistics for a service account."""
        account = await self._get_service_account(client_id)
        if not account:
            return None

        # Calculate stats
        days_since_creation = (datetime.now(timezone.utc) - account.created_at).days
        days_since_rotation = (datetime.now(timezone.utc) - account.last_rotation).days

        return {
            "account_id": account.account_id,
            "client_id": client_id,
            "days_active": days_since_creation,
            "last_used": account.last_used.isoformat() if account.last_used else None,
            "failed_auth_count": account.failed_auth_count,
            "credentials_age_days": days_since_rotation,
            "rotation_due": days_since_rotation >= account.rotation_interval_days,
            "permissions": [p.value for p in account.permissions],
            "scopes": list(account.scopes)
        }

    # Private methods

    async def _initialize_system(self):
        """Initialize the service account system."""
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS service_accounts (
                    client_id TEXT PRIMARY KEY,
                    account_id TEXT UNIQUE NOT NULL,
                    account_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    account_data TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    last_used TEXT
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS auth_events (
                    event_id TEXT PRIMARY KEY,
                    client_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    details TEXT,
                    FOREIGN KEY (client_id) REFERENCES service_accounts (client_id)
                )
            """)

            await db.commit()

    def _hash_secret(self, secret: str) -> str:
        """Hash a client secret using SHA-256."""
        return hashlib.sha256(secret.encode()).hexdigest()

    def _verify_secret(self, secret: str, secret_hash: str) -> bool:
        """Verify a client secret against its hash."""
        return hashlib.sha256(secret.encode()).hexdigest() == secret_hash

    async def _generate_access_token(self, account: ServiceAccount) -> str:
        """Generate JWT access token for service account."""
        now = datetime.now(timezone.utc)
        expiry = now + timedelta(hours=self.token_lifetime_hours)

        claims = {
            "iss": "sofia-platform",
            "sub": account.client_id,
            "aud": "sofia-platform",
            "exp": expiry.timestamp(),
            "iat": now.timestamp(),
            "account_type": account.account_type.value,
            "permissions": [p.value for p in account.permissions],
            "scope": " ".join(account.scopes)
        }

        # Sign with account's private key
        private_key = serialization.load_pem_private_key(
            account.private_key_pem.encode(),
            password=None,
            backend=default_backend()
        )

        token = jwt.encode(claims, private_key, algorithm="RS256")
        return token

    async def _get_service_account(self, client_id: str) -> Optional[ServiceAccount]:
        """Get service account by client ID."""
        # Check cache first
        if client_id in self.account_cache:
            return self.account_cache[client_id]

        # Load from database
        async with aiosqlite.connect(self.database_path) as db:
            cursor = await db.execute(
                "SELECT account_data FROM service_accounts WHERE client_id = ?",
                (client_id,)
            )
            row = await cursor.fetchone()

            if row:
                account_data = json.loads(row[0])
                account = self._deserialize_account(account_data)
                self.account_cache[client_id] = account
                return account

        return None

    def _deserialize_account(self, data: Dict[str, Any]) -> ServiceAccount:
        """Deserialize service account from JSON data."""
        permissions = {Permission(p) for p in data.get("permissions", [])}
        scopes = set(data.get("scopes", []))

        return ServiceAccount(
            account_id=data["account_id"],
            account_type=AccountType(data["account_type"]),
            name=data["name"],
            description=data["description"],
            client_id=data["client_id"],
            client_secret_hash=data["client_secret_hash"],
            private_key_pem=data.get("private_key_pem"),
            public_key_pem=data.get("public_key_pem"),
            permissions=permissions,
            scopes=scopes,
            allowed_origins=data.get("allowed_origins", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            last_rotation=datetime.fromisoformat(data["last_rotation"]),
            rotation_interval_days=data.get("rotation_interval_days", 90),
            is_active=data["is_active"],
            is_locked=data.get("is_locked", False),
            failed_auth_count=data.get("failed_auth_count", 0),
            last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None,
            metadata=data.get("metadata", {})
        )

    async def _store_service_account(self, account: ServiceAccount):
        """Store service account in database."""
        account_data = asdict(account)

        # Convert sets and enums to serializable format
        account_data["permissions"] = [p.value for p in account.permissions]
        account_data["scopes"] = list(account.scopes)
        account_data["account_type"] = account.account_type.value

        # Convert datetimes to strings
        account_data["created_at"] = account.created_at.isoformat()
        account_data["expires_at"] = account.expires_at.isoformat() if account.expires_at else None
        account_data["last_rotation"] = account.last_rotation.isoformat()
        account_data["last_used"] = account.last_used.isoformat() if account.last_used else None

        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO service_accounts
                (client_id, account_id, account_type, name, account_data, is_active, created_at, expires_at, last_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                account.client_id,
                account.account_id,
                account.account_type.value,
                account.name,
                json.dumps(account_data),
                account.is_active,
                account.created_at.isoformat(),
                account.expires_at.isoformat() if account.expires_at else None,
                account.last_used.isoformat() if account.last_used else None
            ))
            await db.commit()

    async def _update_service_account(self, account: ServiceAccount):
        """Update service account in database and cache."""
        await self._store_service_account(account)
        self.account_cache[account.client_id] = account

    async def _deactivate_account(self, account: ServiceAccount):
        """Deactivate a service account."""
        account.is_active = False
        await self._update_service_account(account)

        # Remove from cache
        if account.client_id in self.account_cache:
            del self.account_cache[account.client_id]

    async def _record_failed_auth(self, account: ServiceAccount):
        """Record failed authentication attempt."""
        account.failed_auth_count += 1

        # Lock account if too many failures
        if account.failed_auth_count >= self.max_failed_attempts:
            account.is_locked = True
            print(f"🔒 Locked service account due to failed attempts: {account.client_id}")

        await self._update_service_account(account)

        # Log auth event
        await self._log_auth_event(account.client_id, "failed_auth", {
            "failed_count": account.failed_auth_count,
            "locked": account.is_locked
        })

    async def _log_auth_event(self, client_id: str, event_type: str, details: Dict[str, Any]):
        """Log authentication event."""
        event_id = str(uuid.uuid4())

        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                INSERT INTO auth_events (event_id, client_id, event_type, timestamp, details)
                VALUES (?, ?, ?, ?, ?)
            """, (
                event_id,
                client_id,
                event_type,
                datetime.now(timezone.utc).isoformat(),
                json.dumps(details)
            ))
            await db.commit()