"""
Decentralized Identity (DID) Resolver

Implements DID resolution for the sofIA ecosystem following W3C DID specification.
"""

import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import aiohttp
from cryptography.hazmat.primitives import serialization


@dataclass
class DIDDocument:
    """
    W3C DID Document representation.

    Follows the W3C Decentralized Identifiers (DIDs) v1.0 specification
    https://www.w3.org/TR/did-core/
    """
    context: List[str]  # @context
    id: str  # DID
    verification_method: List[Dict[str, Any]]
    authentication: List[str]
    assertion_method: Optional[List[str]] = None
    key_agreement: Optional[List[str]] = None
    capability_invocation: Optional[List[str]] = None
    capability_delegation: Optional[List[str]] = None
    service: Optional[List[Dict[str, Any]]] = None
    controller: Optional[str] = None
    also_known_as: Optional[List[str]] = None


class DIDResolver:
    """
    DID Resolver for sofIA Ecosystem

    Resolves DIDs to DID Documents for identity verification and
    cryptographic key discovery in the payment ecosystem.
    """

    def __init__(self):
        # Local DID registry for the sofIA ecosystem
        self.local_registry: Dict[str, DIDDocument] = {}

        # Supported DID methods
        self.supported_methods = {
            "did:sofia": self._resolve_sofia_did,
            "did:key": self._resolve_key_did,
            "did:web": self._resolve_web_did,
            "did:ion": self._resolve_ion_did
        }

        # Service endpoints for different DID methods
        self.method_endpoints = {
            "did:ion": "https://ion.network",
            "did:elem": "https://element-did.com"
        }

    async def resolve(self, did: str) -> Optional[DIDDocument]:
        """
        Resolve a DID to its DID Document.

        Args:
            did: Decentralized Identifier to resolve

        Returns:
            DID Document if resolution successful, None otherwise
        """
        if not self._is_valid_did(did):
            print(f"❌ Invalid DID format: {did}")
            return None

        # Check local registry first
        if did in self.local_registry:
            return self.local_registry[did]

        # Determine method and resolve
        method = self._extract_method(did)
        resolver = self.supported_methods.get(method)

        if not resolver:
            print(f"❌ Unsupported DID method: {method}")
            return None

        try:
            did_document = await resolver(did)
            if did_document:
                # Cache in local registry
                self.local_registry[did] = did_document
                print(f"✅ Resolved DID: {did}")
            return did_document

        except Exception as e:
            print(f"❌ DID resolution failed for {did}: {e}")
            return None

    async def create_sofia_did(
        self,
        public_key_pem: str,
        service_endpoints: Optional[List[Dict[str, Any]]] = None,
        controller: Optional[str] = None
    ) -> DIDDocument:
        """
        Create a new sofIA DID and register it locally.

        Args:
            public_key_pem: Public key in PEM format
            service_endpoints: Service endpoints for the DID
            controller: Controller DID (optional)

        Returns:
            Created DID Document
        """
        # Generate unique identifier
        import hashlib
        import uuid

        key_hash = hashlib.sha256(public_key_pem.encode()).hexdigest()[:16]
        did_id = f"did:sofia:{key_hash}"

        # Create verification method
        verification_method = {
            "id": f"{did_id}#key-1",
            "type": "RsaVerificationKey2018",
            "controller": controller or did_id,
            "publicKeyPem": public_key_pem
        }

        # Create DID Document
        did_document = DIDDocument(
            context=[
                "https://www.w3.org/ns/did/v1",
                "https://w3id.org/security/suites/rsa-2018/v1"
            ],
            id=did_id,
            verification_method=[verification_method],
            authentication=[f"{did_id}#key-1"],
            assertion_method=[f"{did_id}#key-1"],
            capability_invocation=[f"{did_id}#key-1"],
            service=service_endpoints or [],
            controller=controller
        )

        # Register in local registry
        self.local_registry[did_id] = did_document

        print(f"✅ Created sofIA DID: {did_id}")
        return did_document

    async def register_agent_did(
        self,
        agent_id: str,
        public_key_pem: str,
        endpoint_url: str,
        capabilities: List[str]
    ) -> DIDDocument:
        """Register a DID for an agent in the sofIA ecosystem."""
        service_endpoints = [
            {
                "id": f"#agent-endpoint",
                "type": "AgentService",
                "serviceEndpoint": endpoint_url,
                "description": f"sofIA Agent: {agent_id}",
                "capabilities": capabilities
            },
            {
                "id": f"#a2a-messaging",
                "type": "MessagingService",
                "serviceEndpoint": f"{endpoint_url}/a2a/receive",
                "description": "Agent-to-Agent messaging endpoint"
            }
        ]

        return await self.create_sofia_did(
            public_key_pem=public_key_pem,
            service_endpoints=service_endpoints
        )

    async def register_user_did(
        self,
        user_id: str,
        public_key_pem: str,
        whatsapp_number: Optional[str] = None
    ) -> DIDDocument:
        """Register a DID for a user in the sofIA ecosystem."""
        service_endpoints = []

        if whatsapp_number:
            service_endpoints.append({
                "id": "#whatsapp-contact",
                "type": "ContactService",
                "serviceEndpoint": f"whatsapp:{whatsapp_number}",
                "description": "WhatsApp contact for payment notifications"
            })

        return await self.create_sofia_did(
            public_key_pem=public_key_pem,
            service_endpoints=service_endpoints
        )

    async def register_merchant_did(
        self,
        merchant_id: str,
        public_key_pem: str,
        business_info: Dict[str, Any],
        payment_endpoint: str
    ) -> DIDDocument:
        """Register a DID for a merchant in the sofIA ecosystem."""
        service_endpoints = [
            {
                "id": "#payment-endpoint",
                "type": "PaymentService",
                "serviceEndpoint": payment_endpoint,
                "description": "BEMOBI payment processing endpoint",
                "paymentMethods": business_info.get("payment_methods", [])
            },
            {
                "id": "#business-info",
                "type": "BusinessService",
                "serviceEndpoint": f"https://sofia.ai/merchants/{merchant_id}",
                "description": "Business information and verification status",
                "businessName": business_info.get("name", ""),
                "registrationNumber": business_info.get("registration", "")
            }
        ]

        return await self.create_sofia_did(
            public_key_pem=public_key_pem,
            service_endpoints=service_endpoints
        )

    async def update_did_document(
        self,
        did: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update a DID Document (only for locally managed DIDs).

        Args:
            did: DID to update
            updates: Fields to update

        Returns:
            Success status
        """
        if did not in self.local_registry:
            return False

        if not did.startswith("did:sofia:"):
            print(f"❌ Cannot update non-Sofia DID: {did}")
            return False

        did_document = self.local_registry[did]

        # Update allowed fields
        if "service" in updates:
            did_document.service = updates["service"]

        if "also_known_as" in updates:
            did_document.also_known_as = updates["also_known_as"]

        print(f"✅ Updated DID: {did}")
        return True

    async def deactivate_did(self, did: str) -> bool:
        """Deactivate a DID (remove from local registry)."""
        if did in self.local_registry:
            del self.local_registry[did]
            print(f"🔴 Deactivated DID: {did}")
            return True
        return False

    async def get_public_key(self, did: str, key_id: Optional[str] = None) -> Optional[str]:
        """
        Get public key for a DID.

        Args:
            did: DID to get key for
            key_id: Specific key ID (optional, uses first key if not specified)

        Returns:
            Public key in PEM format
        """
        did_document = await self.resolve(did)
        if not did_document:
            return None

        # Find the verification method
        if key_id:
            for vm in did_document.verification_method:
                if vm["id"] == key_id or vm["id"].endswith(f"#{key_id}"):
                    return vm.get("publicKeyPem")
        else:
            # Return first key
            if did_document.verification_method:
                return did_document.verification_method[0].get("publicKeyPem")

        return None

    async def get_service_endpoint(
        self,
        did: str,
        service_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get service endpoint by type for a DID."""
        did_document = await self.resolve(did)
        if not did_document or not did_document.service:
            return None

        for service in did_document.service:
            if service.get("type") == service_type:
                return service

        return None

    async def export_registry(self) -> Dict[str, Any]:
        """Export the local DID registry."""
        return {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_dids": len(self.local_registry),
            "dids": {
                did: asdict(doc) for did, doc in self.local_registry.items()
            }
        }

    async def import_registry(self, registry_data: Dict[str, Any]) -> int:
        """Import DIDs into the local registry."""
        imported_count = 0

        for did, doc_data in registry_data.get("dids", {}).items():
            try:
                # Reconstruct DID Document
                did_document = DIDDocument(**doc_data)
                self.local_registry[did] = did_document
                imported_count += 1
            except Exception as e:
                print(f"❌ Failed to import DID {did}: {e}")

        print(f"✅ Imported {imported_count} DIDs")
        return imported_count

    # Private methods

    def _is_valid_did(self, did: str) -> bool:
        """Validate DID format according to W3C specification."""
        if not did.startswith("did:"):
            return False

        parts = did.split(":")
        if len(parts) < 3:
            return False

        # Method and method-specific-id should not be empty
        return all(part.strip() for part in parts[1:3])

    def _extract_method(self, did: str) -> str:
        """Extract DID method from DID string."""
        parts = did.split(":")
        if len(parts) >= 2:
            return f"did:{parts[1]}"
        return ""

    async def _resolve_sofia_did(self, did: str) -> Optional[DIDDocument]:
        """Resolve sofIA DID from local registry."""
        return self.local_registry.get(did)

    async def _resolve_key_did(self, did: str) -> Optional[DIDDocument]:
        """
        Resolve did:key method.

        did:key is a static method where the DID is derived from a public key.
        """
        try:
            # Extract the key from the DID
            # Format: did:key:zDnaekGZTbQBerwcehBSXLqAg6s55hVEBms1zFy89VHXtJSa9
            if not did.startswith("did:key:z"):
                return None

            # For simplicity, create a basic DID document
            # In production, this would involve proper multibase/multicodec decoding
            key_id = f"{did}#key-1"

            return DIDDocument(
                context=["https://www.w3.org/ns/did/v1"],
                id=did,
                verification_method=[{
                    "id": key_id,
                    "type": "Ed25519VerificationKey2018",
                    "controller": did,
                    "publicKeyBase58": did.split(":")[-1]  # Simplified
                }],
                authentication=[key_id],
                assertion_method=[key_id],
                capability_invocation=[key_id]
            )

        except Exception as e:
            print(f"❌ Failed to resolve did:key {did}: {e}")
            return None

    async def _resolve_web_did(self, did: str) -> Optional[DIDDocument]:
        """
        Resolve did:web method.

        did:web resolves to a DID document hosted on a web domain.
        """
        try:
            # Extract domain from DID
            # Format: did:web:example.com or did:web:example.com:path:to:doc
            if not did.startswith("did:web:"):
                return None

            parts = did.split(":")[2:]  # Remove 'did:web:'
            domain = parts[0]
            path = ":".join(parts[1:]) if len(parts) > 1 else ""

            # Construct URL
            if path:
                url = f"https://{domain}/{path.replace(':', '/')}/did.json"
            else:
                url = f"https://{domain}/.well-known/did.json"

            # Fetch DID document
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        doc_data = await response.json()
                        return DIDDocument(**doc_data)

        except Exception as e:
            print(f"❌ Failed to resolve did:web {did}: {e}")

        return None

    async def _resolve_ion_did(self, did: str) -> Optional[DIDDocument]:
        """
        Resolve did:ion method (Microsoft ION network).

        This would connect to the ION network for resolution.
        """
        try:
            if not did.startswith("did:ion:"):
                return None

            # In production, this would query the ION network
            # For now, return None as it requires ION network connectivity
            print(f"⚠️ ION DID resolution not implemented: {did}")
            return None

        except Exception as e:
            print(f"❌ Failed to resolve did:ion {did}: {e}")
            return None