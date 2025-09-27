"""
Verifiable Credential Issuer

Implements W3C Verifiable Credentials specification for issuing
payment and identity credentials in the sofIA ecosystem.
"""

import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ed25519
from cryptography.hazmat.backends import default_backend
import jwt
import hashlib

from .did_resolver import DIDResolver, DIDDocument


class CredentialType(Enum):
    """Types of verifiable credentials issued."""
    PAYMENT_AUTHORIZATION = "PaymentAuthorizationCredential"
    MERCHANT_VERIFICATION = "MerchantVerificationCredential"
    USER_IDENTITY = "UserIdentityCredential"
    KYC_COMPLIANCE = "KYCComplianceCredential"
    TRANSACTION_MANDATE = "TransactionMandateCredential"
    AGENT_AUTHORIZATION = "AgentAuthorizationCredential"


class CredentialStatus(Enum):
    """Status of issued credentials."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass
class VerifiableCredential:
    """
    W3C Verifiable Credential implementation.

    Follows the W3C Verifiable Credentials Data Model v1.1
    https://www.w3.org/TR/vc-data-model/
    """
    # Standard W3C VC fields
    context: List[str]  # @context
    id: str
    type: List[str]
    issuer: str  # DID of issuer
    issuance_date: str  # ISO 8601
    expiration_date: Optional[str]  # ISO 8601

    # Credential subject
    credential_subject: Dict[str, Any]

    # Credential status (for revocation)
    credential_status: Optional[Dict[str, Any]]

    # Proof (cryptographic signature)
    proof: Optional[Dict[str, Any]]

    # sofIA-specific extensions
    sofia_metadata: Dict[str, Any]


@dataclass
class CredentialSchema:
    """Schema definition for credential types."""
    schema_id: str
    name: str
    version: str
    description: str
    required_fields: List[str]
    optional_fields: List[str]
    validation_rules: Dict[str, Any]


class CredentialIssuer:
    """
    Verifiable Credential Issuer for sofIA Ecosystem

    Issues W3C-compliant verifiable credentials for payment authorization,
    merchant verification, and compliance purposes.
    """

    def __init__(
        self,
        issuer_did: str,
        private_key: Union[rsa.RSAPrivateKey, ed25519.Ed25519PrivateKey],
        did_resolver: DIDResolver
    ):
        self.issuer_did = issuer_did
        self.private_key = private_key
        self.did_resolver = did_resolver

        # Credential registry
        self.issued_credentials: Dict[str, VerifiableCredential] = {}
        self.credential_status_list: Dict[str, CredentialStatus] = {}

        # Schemas
        self.credential_schemas: Dict[CredentialType, CredentialSchema] = {}
        self._initialize_schemas()

        # Revocation registry
        self.revocation_list: Dict[str, Dict[str, Any]] = {}

    async def issue_credential(
        self,
        credential_type: CredentialType,
        subject_did: str,
        claims: Dict[str, Any],
        valid_for_days: int = 365,
        additional_context: Optional[List[str]] = None
    ) -> VerifiableCredential:
        """
        Issue a verifiable credential.

        Args:
            credential_type: Type of credential to issue
            subject_did: DID of the credential subject
            claims: Claims to include in the credential
            valid_for_days: Validity period in days
            additional_context: Additional JSON-LD contexts

        Returns:
            Issued verifiable credential
        """
        # Validate subject DID
        subject_did_doc = await self.did_resolver.resolve(subject_did)
        if not subject_did_doc:
            raise ValueError(f"Cannot resolve subject DID: {subject_did}")

        # Validate claims against schema
        schema = self.credential_schemas.get(credential_type)
        if schema:
            self._validate_claims(claims, schema)

        # Generate credential ID
        credential_id = f"urn:uuid:{uuid.uuid4()}"

        # Calculate dates
        issuance_date = datetime.now(timezone.utc)
        expiration_date = issuance_date + timedelta(days=valid_for_days)

        # Build context
        context = [
            "https://www.w3.org/2018/credentials/v1",
            "https://sofia.ai/credentials/v1"
        ]
        if additional_context:
            context.extend(additional_context)

        # Create credential subject
        credential_subject = {
            "id": subject_did,
            **claims
        }

        # Create credential status entry for revocation
        status_list_id = f"{self.issuer_did}#revocation-list-2023"
        credential_status = {
            "id": f"{status_list_id}#{len(self.credential_status_list)}",
            "type": "RevocationList2020Status",
            "revocationListIndex": str(len(self.credential_status_list)),
            "revocationListCredential": status_list_id
        }

        # Create credential
        credential = VerifiableCredential(
            context=context,
            id=credential_id,
            type=["VerifiableCredential", credential_type.value],
            issuer=self.issuer_did,
            issuance_date=issuance_date.isoformat(),
            expiration_date=expiration_date.isoformat(),
            credential_subject=credential_subject,
            credential_status=credential_status,
            proof=None,  # Will be added by signing
            sofia_metadata={
                "schema_version": schema.version if schema else "1.0",
                "issued_by": "sofIA Payment Platform",
                "compliance_verified": True,
                "audit_trail_id": f"audit_{int(issuance_date.timestamp())}"
            }
        )

        # Sign credential
        await self._sign_credential(credential)

        # Register credential
        self.issued_credentials[credential_id] = credential
        self.credential_status_list[credential_id] = CredentialStatus.ACTIVE

        print(f"✅ Issued credential: {credential_type.value} for {subject_did}")
        return credential

    async def revoke_credential(
        self,
        credential_id: str,
        reason: str = "revoked"
    ) -> bool:
        """
        Revoke a previously issued credential.

        Args:
            credential_id: ID of credential to revoke
            reason: Reason for revocation

        Returns:
            Success status
        """
        if credential_id not in self.issued_credentials:
            return False

        # Update status
        self.credential_status_list[credential_id] = CredentialStatus.REVOKED

        # Add to revocation list
        self.revocation_list[credential_id] = {
            "revoked_at": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "issuer": self.issuer_did
        }

        print(f"🚫 Revoked credential: {credential_id} - {reason}")
        return True

    async def verify_credential_status(self, credential_id: str) -> CredentialStatus:
        """Check the current status of a credential."""
        if credential_id not in self.credential_status_list:
            return CredentialStatus.EXPIRED

        # Check expiration
        if credential_id in self.issued_credentials:
            credential = self.issued_credentials[credential_id]
            if credential.expiration_date:
                expiry = datetime.fromisoformat(credential.expiration_date)
                if expiry < datetime.now(timezone.utc):
                    self.credential_status_list[credential_id] = CredentialStatus.EXPIRED
                    return CredentialStatus.EXPIRED

        return self.credential_status_list[credential_id]

    async def issue_payment_authorization_credential(
        self,
        user_did: str,
        payment_methods: List[str],
        spending_limits: Dict[str, float],
        merchant_restrictions: Optional[List[str]] = None
    ) -> VerifiableCredential:
        """Issue payment authorization credential for a user."""
        claims = {
            "paymentMethods": payment_methods,
            "spendingLimits": spending_limits,
            "authorizedMerchants": merchant_restrictions or [],
            "complianceLevel": "KYC_VERIFIED",
            "issuedFor": "payment_authorization"
        }

        return await self.issue_credential(
            credential_type=CredentialType.PAYMENT_AUTHORIZATION,
            subject_did=user_did,
            claims=claims,
            valid_for_days=365
        )

    async def issue_merchant_verification_credential(
        self,
        merchant_did: str,
        business_registration: str,
        compliance_status: str,
        authorized_regions: List[str],
        payment_methods: List[str]
    ) -> VerifiableCredential:
        """Issue merchant verification credential."""
        claims = {
            "businessRegistration": business_registration,
            "complianceStatus": compliance_status,
            "authorizedRegions": authorized_regions,
            "acceptedPaymentMethods": payment_methods,
            "verificationLevel": "FULL_KYB",
            "issuedFor": "merchant_verification"
        }

        return await self.issue_credential(
            credential_type=CredentialType.MERCHANT_VERIFICATION,
            subject_did=merchant_did,
            claims=claims,
            valid_for_days=730  # 2 years for merchants
        )

    async def issue_transaction_mandate_credential(
        self,
        agent_did: str,
        mandate_id: str,
        transaction_details: Dict[str, Any],
        ap2_compliance: Dict[str, Any]
    ) -> VerifiableCredential:
        """Issue transaction mandate credential for AP2 compliance."""
        claims = {
            "mandateId": mandate_id,
            "transactionDetails": transaction_details,
            "ap2Compliance": ap2_compliance,
            "mandateType": "PAYMENT_MANDATE",
            "cryptographicProof": True,
            "issuedFor": "transaction_mandate"
        }

        return await self.issue_credential(
            credential_type=CredentialType.TRANSACTION_MANDATE,
            subject_did=agent_did,
            claims=claims,
            valid_for_days=1  # Short-lived for transactions
        )

    async def get_credential_by_id(self, credential_id: str) -> Optional[VerifiableCredential]:
        """Retrieve a credential by its ID."""
        return self.issued_credentials.get(credential_id)

    async def get_credentials_for_subject(
        self,
        subject_did: str,
        credential_type: Optional[CredentialType] = None
    ) -> List[VerifiableCredential]:
        """Get all credentials for a specific subject."""
        credentials = []

        for credential in self.issued_credentials.values():
            if credential.credential_subject.get("id") == subject_did:
                # Filter by type if specified
                if credential_type and credential_type.value not in credential.type:
                    continue

                # Check if still active
                status = await self.verify_credential_status(credential.id)
                if status == CredentialStatus.ACTIVE:
                    credentials.append(credential)

        return credentials

    async def create_revocation_list(self) -> Dict[str, Any]:
        """Create a revocation list credential."""
        revocation_list_id = f"{self.issuer_did}#revocation-list-2023"

        # Build bit string for revocation status
        bit_string = ""
        for credential_id in sorted(self.credential_status_list.keys()):
            status = self.credential_status_list[credential_id]
            bit_string += "1" if status == CredentialStatus.REVOKED else "0"

        revocation_list = {
            "@context": [
                "https://www.w3.org/2018/credentials/v1",
                "https://w3id.org/vc-revocation-list-2020/v1"
            ],
            "id": revocation_list_id,
            "type": ["VerifiableCredential", "RevocationList2020Credential"],
            "issuer": self.issuer_did,
            "issuanceDate": datetime.now(timezone.utc).isoformat(),
            "credentialSubject": {
                "id": revocation_list_id,
                "type": "RevocationList2020",
                "encodedList": bit_string
            }
        }

        return revocation_list

    async def get_issuer_statistics(self) -> Dict[str, Any]:
        """Get statistics about issued credentials."""
        total_issued = len(self.issued_credentials)
        by_type = {}
        by_status = {}

        for credential in self.issued_credentials.values():
            # Count by type
            for cred_type in credential.type:
                if cred_type != "VerifiableCredential":
                    by_type[cred_type] = by_type.get(cred_type, 0) + 1

        for status in self.credential_status_list.values():
            by_status[status.value] = by_status.get(status.value, 0) + 1

        return {
            "issuer_did": self.issuer_did,
            "total_issued": total_issued,
            "by_type": by_type,
            "by_status": by_status,
            "revoked_count": len(self.revocation_list),
            "schemas_available": len(self.credential_schemas)
        }

    # Private methods

    def _initialize_schemas(self):
        """Initialize credential schemas."""
        # Payment Authorization Schema
        self.credential_schemas[CredentialType.PAYMENT_AUTHORIZATION] = CredentialSchema(
            schema_id="https://sofia.ai/schemas/payment-authorization/v1",
            name="Payment Authorization Credential",
            version="1.0",
            description="Authorizes user for payment transactions",
            required_fields=["paymentMethods", "spendingLimits"],
            optional_fields=["authorizedMerchants", "complianceLevel"],
            validation_rules={
                "paymentMethods": {"type": "array", "minItems": 1},
                "spendingLimits": {"type": "object", "required": ["daily", "monthly"]}
            }
        )

        # Merchant Verification Schema
        self.credential_schemas[CredentialType.MERCHANT_VERIFICATION] = CredentialSchema(
            schema_id="https://sofia.ai/schemas/merchant-verification/v1",
            name="Merchant Verification Credential",
            version="1.0",
            description="Verifies merchant for accepting payments",
            required_fields=["businessRegistration", "complianceStatus"],
            optional_fields=["authorizedRegions", "acceptedPaymentMethods"],
            validation_rules={
                "businessRegistration": {"type": "string", "minLength": 1},
                "complianceStatus": {"enum": ["PENDING", "VERIFIED", "REJECTED"]}
            }
        )

        # Transaction Mandate Schema
        self.credential_schemas[CredentialType.TRANSACTION_MANDATE] = CredentialSchema(
            schema_id="https://sofia.ai/schemas/transaction-mandate/v1",
            name="Transaction Mandate Credential",
            version="1.0",
            description="AP2-compliant transaction mandate",
            required_fields=["mandateId", "transactionDetails", "ap2Compliance"],
            optional_fields=["cryptographicProof"],
            validation_rules={
                "mandateId": {"type": "string", "pattern": "^[a-zA-Z0-9_-]+$"},
                "ap2Compliance": {"type": "object", "required": ["mandateType", "signature"]}
            }
        )

    def _validate_claims(self, claims: Dict[str, Any], schema: CredentialSchema):
        """Validate claims against schema."""
        # Check required fields
        for field in schema.required_fields:
            if field not in claims:
                raise ValueError(f"Missing required field: {field}")

        # Apply validation rules
        for field, rules in schema.validation_rules.items():
            if field not in claims:
                continue

            value = claims[field]

            # Type validation
            if "type" in rules:
                expected_type = rules["type"]
                if expected_type == "array" and not isinstance(value, list):
                    raise ValueError(f"Field {field} must be an array")
                elif expected_type == "object" and not isinstance(value, dict):
                    raise ValueError(f"Field {field} must be an object")
                elif expected_type == "string" and not isinstance(value, str):
                    raise ValueError(f"Field {field} must be a string")

            # Enum validation
            if "enum" in rules and value not in rules["enum"]:
                raise ValueError(f"Field {field} must be one of: {rules['enum']}")

            # Length validation
            if "minLength" in rules and len(str(value)) < rules["minLength"]:
                raise ValueError(f"Field {field} is too short")

            # Array validation
            if "minItems" in rules and isinstance(value, list) and len(value) < rules["minItems"]:
                raise ValueError(f"Field {field} must have at least {rules['minItems']} items")

    async def _sign_credential(self, credential: VerifiableCredential):
        """Sign the credential with issuer's private key."""
        # Create proof
        proof = {
            "type": "RsaSignature2018" if isinstance(self.private_key, rsa.RSAPrivateKey) else "Ed25519Signature2018",
            "created": datetime.now(timezone.utc).isoformat(),
            "verificationMethod": f"{self.issuer_did}#key-1",
            "proofPurpose": "assertionMethod"
        }

        # Create canonical credential representation for signing
        credential_copy = asdict(credential)
        credential_copy.pop("proof", None)  # Remove proof field for signing

        canonical_data = json.dumps(credential_copy, sort_keys=True)

        # Sign the canonical data
        if isinstance(self.private_key, rsa.RSAPrivateKey):
            from cryptography.hazmat.primitives.asymmetric import padding
            signature = self.private_key.sign(
                canonical_data.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        else:  # Ed25519
            signature = self.private_key.sign(canonical_data.encode())

        proof["jws"] = signature.hex()

        # Add proof to credential
        credential.proof = proof