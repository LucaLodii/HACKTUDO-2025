"""
Verifiable Credentials System for sofIA

Implements W3C Verifiable Credentials standard for user authorization
and commercial identity management in the payment ecosystem.
"""

from .credential_issuer import CredentialIssuer, CredentialType, CredentialStatus
from .credential_verifier import CredentialVerifier
from .did_resolver import DIDResolver, DIDDocument
from .credential_schemas import PaymentCredentialSchema, MerchantCredentialSchema

__all__ = [
    "CredentialIssuer",
    "CredentialType",
    "CredentialStatus",
    "CredentialVerifier",
    "DIDResolver",
    "DIDDocument",
    "PaymentCredentialSchema",
    "MerchantCredentialSchema"
]