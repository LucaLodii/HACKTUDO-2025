"""
Verifiable Credentials and DID Tool for sofIA Agent

Provides W3C Verifiable Credentials issuance, verification, and DID resolution
for secure payment authorization and merchant verification.
"""

from google.adk.tools import Tool
from typing import Dict, Any, List, Optional
import json

from ...credentials import CredentialIssuer, DIDResolver
from ...ledger import MandateLedger


def issue_payment_credential(
    subject_did: str,
    payment_amount: float,
    currency: str,
    merchant_id: str,
    expiry_hours: int = 24
) -> Dict[str, Any]:
    """
    Issue a payment authorization credential.

    Args:
        subject_did: DID of the payment subject
        payment_amount: Amount to authorize
        currency: Currency code (USD, EUR, etc.)
        merchant_id: Merchant identifier
        expiry_hours: Credential expiry in hours

    Returns:
        Issued verifiable credential
    """
    try:
        issuer = CredentialIssuer()

        credential = issuer.issue_payment_credential(
            subject_did=subject_did,
            payment_amount=payment_amount,
            currency=currency,
            merchant_id=merchant_id,
            expiry_hours=expiry_hours
        )

        return {
            "success": True,
            "credential": {
                "id": credential.id,
                "type": credential.type,
                "issuer": credential.issuer,
                "subject": credential.subject,
                "claims": credential.claims,
                "proof": credential.proof,
                "expires_at": credential.expires_at.isoformat()
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Credential issuance failed: {str(e)}"
        }


def verify_credential(
    credential_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify a verifiable credential.

    Args:
        credential_data: Credential data to verify

    Returns:
        Verification result with status and details
    """
    try:
        issuer = CredentialIssuer()
        is_valid, details = issuer.verify_credential(credential_data)

        return {
            "success": True,
            "is_valid": is_valid,
            "verification_details": details,
            "verified_at": details.get("verified_at"),
            "issuer_trusted": details.get("issuer_trusted", False)
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Credential verification failed: {str(e)}"
        }


def resolve_did(
    did: str
) -> Dict[str, Any]:
    """
    Resolve a Decentralized Identifier (DID).

    Args:
        did: DID to resolve

    Returns:
        DID Document with verification methods and services
    """
    try:
        resolver = DIDResolver()
        did_document = resolver.resolve(did)

        if did_document:
            return {
                "success": True,
                "did_document": {
                    "id": did_document.id,
                    "verification_methods": [
                        {
                            "id": vm.id,
                            "type": vm.type,
                            "controller": vm.controller,
                            "public_key": vm.public_key_base58
                        }
                        for vm in did_document.verification_methods
                    ],
                    "services": [
                        {
                            "id": service.id,
                            "type": service.type,
                            "service_endpoint": service.service_endpoint
                        }
                        for service in did_document.services
                    ]
                }
            }
        else:
            return {
                "success": False,
                "error": f"DID {did} not found"
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"DID resolution failed: {str(e)}"
        }


def register_mandate_on_ledger(
    mandate_id: str,
    mandate_type: str,
    mandate_data: Dict[str, Any],
    merchant_did: str
) -> Dict[str, Any]:
    """
    Register an AP2 mandate on the distributed ledger.

    Args:
        mandate_id: Unique mandate identifier
        mandate_type: Type of mandate (intent, cart, payment)
        mandate_data: Mandate payload data
        merchant_did: Merchant's DID

    Returns:
        Ledger registration result with block information
    """
    try:
        ledger = MandateLedger()

        block_hash = ledger.add_mandate(
            mandate_id=mandate_id,
            mandate_type=mandate_type,
            mandate_data=mandate_data,
            merchant_did=merchant_did
        )

        return {
            "success": True,
            "mandate_id": mandate_id,
            "block_hash": block_hash,
            "ledger_height": ledger.get_chain_length(),
            "registration_time": ledger.get_latest_block().timestamp.isoformat()
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Mandate registration failed: {str(e)}"
        }


def verify_mandate_on_ledger(
    mandate_id: str
) -> Dict[str, Any]:
    """
    Verify a mandate exists on the distributed ledger.

    Args:
        mandate_id: Mandate identifier to verify

    Returns:
        Verification result with mandate details
    """
    try:
        ledger = MandateLedger()
        mandate_record = ledger.get_mandate(mandate_id)

        if mandate_record:
            return {
                "success": True,
                "mandate_verified": True,
                "mandate_data": {
                    "mandate_id": mandate_record.mandate_id,
                    "mandate_type": mandate_record.mandate_type,
                    "merchant_did": mandate_record.merchant_did,
                    "timestamp": mandate_record.timestamp.isoformat(),
                    "block_hash": mandate_record.block_hash
                }
            }
        else:
            return {
                "success": True,
                "mandate_verified": False,
                "error": f"Mandate {mandate_id} not found on ledger"
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Mandate verification failed: {str(e)}"
        }


credentials_tool = Tool(
    name="verifiable_credentials",
    description="W3C Verifiable Credentials, DID resolution, and mandate ledger management",
    function_declarations=[
        {
            "name": "issue_payment_credential",
            "description": "Issue a payment authorization credential",
            "parameters": {
                "type": "object",
                "properties": {
                    "subject_did": {
                        "type": "string",
                        "description": "DID of the payment subject"
                    },
                    "payment_amount": {
                        "type": "number",
                        "description": "Amount to authorize"
                    },
                    "currency": {
                        "type": "string",
                        "description": "Currency code (USD, EUR, etc.)"
                    },
                    "merchant_id": {
                        "type": "string",
                        "description": "Merchant identifier"
                    },
                    "expiry_hours": {
                        "type": "integer",
                        "description": "Credential expiry in hours",
                        "default": 24
                    }
                },
                "required": ["subject_did", "payment_amount", "currency", "merchant_id"]
            }
        },
        {
            "name": "verify_credential",
            "description": "Verify a verifiable credential",
            "parameters": {
                "type": "object",
                "properties": {
                    "credential_data": {
                        "type": "object",
                        "description": "Credential data to verify"
                    }
                },
                "required": ["credential_data"]
            }
        },
        {
            "name": "resolve_did",
            "description": "Resolve a Decentralized Identifier (DID)",
            "parameters": {
                "type": "object",
                "properties": {
                    "did": {
                        "type": "string",
                        "description": "DID to resolve"
                    }
                },
                "required": ["did"]
            }
        },
        {
            "name": "register_mandate_on_ledger",
            "description": "Register an AP2 mandate on the distributed ledger",
            "parameters": {
                "type": "object",
                "properties": {
                    "mandate_id": {
                        "type": "string",
                        "description": "Unique mandate identifier"
                    },
                    "mandate_type": {
                        "type": "string",
                        "description": "Type of mandate (intent, cart, payment)"
                    },
                    "mandate_data": {
                        "type": "object",
                        "description": "Mandate payload data"
                    },
                    "merchant_did": {
                        "type": "string",
                        "description": "Merchant's DID"
                    }
                },
                "required": ["mandate_id", "mandate_type", "mandate_data", "merchant_did"]
            }
        },
        {
            "name": "verify_mandate_on_ledger",
            "description": "Verify a mandate exists on the distributed ledger",
            "parameters": {
                "type": "object",
                "properties": {
                    "mandate_id": {
                        "type": "string",
                        "description": "Mandate identifier to verify"
                    }
                },
                "required": ["mandate_id"]
            }
        }
    ],
    functions={
        "issue_payment_credential": issue_payment_credential,
        "verify_credential": verify_credential,
        "resolve_did": resolve_did,
        "register_mandate_on_ledger": register_mandate_on_ledger,
        "verify_mandate_on_ledger": verify_mandate_on_ledger
    }
)