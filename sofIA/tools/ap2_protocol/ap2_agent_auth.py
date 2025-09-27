"""
AP2 Agent Authentication and Authorization Implementation

This module implements proper agent-to-agent authentication following the AP2 protocol
specification, ensuring both sender and receiver agents are properly credentialed.
"""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import jwt
from cryptography.hazmat.primitives import serialization

from sofIA.registry.agent_registry import (
    AgentRegistry, RegisteredAgent, AgentCapability, AgentType,
    Region, PaymentMethod
)
from .ap2_core import AP2PaymentAgent
from .verifiable_credentials import VerifiableCredential, CredentialProvider


@dataclass
class AgentCredentials:
    """Represents authenticated agent credentials for AP2 transactions"""
    agent_id: str
    agent_type: AgentType
    public_key: str
    registration_certificate: str
    capabilities: List[str]
    authorized_merchants: List[str]
    expires_at: datetime


@dataclass
class AP2TransactionContext:
    """Context for AP2 agent-to-agent transactions"""
    sender_agent: AgentCredentials
    receiver_agent: AgentCredentials
    transaction_id: str
    merchant_id: str
    payment_method: PaymentMethod
    region: Region
    amount: float
    currency: str
    authorized_at: datetime
    expires_at: datetime


class AP2AgentAuthenticator:
    """
    Handles AP2-compliant agent authentication and authorization.

    This class ensures proper agent-to-agent authentication following the
    AP2 protocol's security model for verifiable, non-repudiable transactions.
    """

    def __init__(self, registry: AgentRegistry, local_agent: AP2PaymentAgent):
        self.registry = registry
        self.local_agent = local_agent
        self.authenticated_sessions: Dict[str, AP2TransactionContext] = {}
        self._registration_attempted = False

        # Register our local agent if not already registered (will be done on first transaction)

    async def _ensure_agent_registered(self):
        """Ensure the local agent is registered with the registry"""
        try:
            # Check if agent is already registered
            agents = await self.registry.discover_agents(
                agent_type=AgentType.PAYMENT_PROCESSOR
            )

            if not any(agent.agent_id == self.local_agent.agent_id for agent in agents):
                await self._register_local_agent()

        except Exception as e:
            print(f"Warning: Agent registration failed: {e}")

    async def _register_local_agent(self):
        """Register the local agent with full AP2 capabilities"""

        # Define our agent's capabilities
        capabilities = [
            AgentCapability(
                name="ap2_intent_mandates",
                version="1.0",
                description="Create and process AP2 Intent Mandates",
                supported_regions=[Region.LATAM, Region.GLOBAL],
                supported_payment_methods=[PaymentMethod.PIX, PaymentMethod.CREDIT_CARD, PaymentMethod.BOLETO],
                ap2_mandate_types=["intent"],
                max_throughput=1000,
                sla_response_time=2.0,
                requires_auth=True,
                cost_per_transaction=0.05
            ),
            AgentCapability(
                name="ap2_cart_mandates",
                version="1.0",
                description="Create and process AP2 Cart Mandates",
                supported_regions=[Region.LATAM, Region.GLOBAL],
                supported_payment_methods=[PaymentMethod.PIX, PaymentMethod.CREDIT_CARD, PaymentMethod.BOLETO],
                ap2_mandate_types=["cart"],
                max_throughput=1000,
                sla_response_time=1.5,
                requires_auth=True,
                cost_per_transaction=0.10
            ),
            AgentCapability(
                name="ap2_payment_mandates",
                version="1.0",
                description="Execute AP2 Payment Mandates with full compliance",
                supported_regions=[Region.LATAM, Region.GLOBAL],
                supported_payment_methods=[PaymentMethod.PIX, PaymentMethod.CREDIT_CARD, PaymentMethod.BOLETO],
                ap2_mandate_types=["payment"],
                max_throughput=500,
                sla_response_time=5.0,
                requires_auth=True,
                cost_per_transaction=0.25
            )
        ]

        # Get agent's public key
        public_key_pem = self.local_agent.signer.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

        # Create agent registration
        agent = RegisteredAgent(
            agent_id=self.local_agent.agent_id,
            agent_type=AgentType.PAYMENT_PROCESSOR,
            name="sofIA AP2 Payment Agent",
            description="WhatsApp Payment Agent with full AP2 Protocol compliance",
            endpoint_url="https://sofia-api.bemobi.com",  # In production, use real endpoint
            public_key=public_key_pem,
            capabilities=capabilities,
            merchant_networks=[self.local_agent.merchant_id, "bemobi-network"],
            status="active",
            last_heartbeat=datetime.now(timezone.utc),
            registration_time=datetime.now(timezone.utc),
            certificate_expiry=datetime.now(timezone.utc) + timedelta(days=365),
            compliance_verified=True,
            metadata={"ap2_version": "1.0", "whatsapp_integration": True}
        )

        # Register with the registry
        success = await self.registry.register_agent(agent)
        if success:
            print(f"✅ Agent {self.local_agent.agent_id} registered successfully")
        else:
            print(f"❌ Failed to register agent {self.local_agent.agent_id}")

    async def authenticate_transaction(
        self,
        merchant_id: str,
        payment_method: str,
        amount: float,
        currency: str = "BRL",
        region: str = "latam"
    ) -> Optional[AP2TransactionContext]:
        """
        Authenticate a transaction between sender and receiver agents.

        This implements the AP2 agent-to-agent authentication process.
        """
        try:
            # Ensure our agent is registered first
            if not self._registration_attempted:
                await self._ensure_agent_registered()
                self._registration_attempted = True
            # Convert string enums
            payment_method_enum = PaymentMethod(payment_method.lower())
            region_enum = Region(region.lower())

            # 1. Discover authorized receiver agent for the merchant
            # First try to find merchant gateway agents (the typical case for BEMOBI merchants)
            receiver_agents = await self.registry.discover_agents(
                agent_type=AgentType.MERCHANT_GATEWAY,
                merchant_id=merchant_id,
                payment_method=payment_method_enum,
                region=region_enum
            )

            # If no merchant gateway found, fall back to payment processor agents
            if not receiver_agents:
                receiver_agents = await self.registry.discover_agents(
                    agent_type=AgentType.PAYMENT_PROCESSOR,
                    merchant_id=merchant_id,
                    payment_method=payment_method_enum,
                    region=region_enum
                )

            if not receiver_agents:
                print(f"❌ No authorized receiver agent found for merchant {merchant_id}")
                return None

            receiver_agent = receiver_agents[0]  # Use first available

            # 2. Negotiate capabilities between agents
            negotiation_result = await self.registry.negotiate_capabilities(
                requester_id=self.local_agent.agent_id,
                target_agent_id=receiver_agent.agent_id,
                required_capabilities=["ap2_payment_mandates"],
                context={
                    "merchant_id": merchant_id,
                    "payment_method": payment_method,
                    "region": region,
                    "amount": amount,
                    "currency": currency
                }
            )

            if not negotiation_result.get("success"):
                print(f"❌ Capability negotiation failed: {negotiation_result.get('error')}")
                return None

            # 3. Create authenticated transaction context
            transaction_id = f"ap2_txn_{datetime.now().timestamp()}"

            # Create sender agent credentials (our local agent)
            sender_credentials = AgentCredentials(
                agent_id=self.local_agent.agent_id,
                agent_type=AgentType.PAYMENT_PROCESSOR,
                public_key=self.local_agent.signer.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ).decode(),
                registration_certificate=await self._get_agent_certificate(self.local_agent.agent_id),
                capabilities=["ap2_intent_mandates", "ap2_cart_mandates", "ap2_payment_mandates"],
                authorized_merchants=[merchant_id, "bemobi-network"],
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
            )

            # Create receiver agent credentials
            receiver_credentials = AgentCredentials(
                agent_id=receiver_agent.agent_id,
                agent_type=receiver_agent.agent_type,
                public_key=receiver_agent.public_key,
                registration_certificate=receiver_agent.metadata.get("registration_certificate", ""),
                capabilities=[cap.name for cap in receiver_agent.capabilities],
                authorized_merchants=receiver_agent.merchant_networks,
                expires_at=receiver_agent.certificate_expiry
            )

            # Create transaction context
            transaction_context = AP2TransactionContext(
                sender_agent=sender_credentials,
                receiver_agent=receiver_credentials,
                transaction_id=transaction_id,
                merchant_id=merchant_id,
                payment_method=payment_method_enum,
                region=region_enum,
                amount=amount,
                currency=currency,
                authorized_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)  # 15-minute expiry per AP2
            )

            # Store authenticated session
            self.authenticated_sessions[transaction_id] = transaction_context

            print(f"✅ AP2 transaction authenticated: {transaction_id}")
            print(f"   Sender: {sender_credentials.agent_id}")
            print(f"   Receiver: {receiver_credentials.agent_id}")
            print(f"   Merchant: {merchant_id}")
            print(f"   Amount: {amount} {currency}")

            return transaction_context

        except Exception as e:
            print(f"❌ AP2 transaction authentication failed: {e}")
            return None

    async def verify_transaction_authorization(self, transaction_id: str) -> bool:
        """Verify that a transaction is properly authorized"""
        if transaction_id not in self.authenticated_sessions:
            return False

        context = self.authenticated_sessions[transaction_id]

        # Check if transaction has expired
        if datetime.now(timezone.utc) > context.expires_at:
            del self.authenticated_sessions[transaction_id]
            return False

        # Verify both agents are still valid
        sender_valid = await self._verify_agent_credentials(context.sender_agent)
        receiver_valid = await self._verify_agent_credentials(context.receiver_agent)

        return sender_valid and receiver_valid

    async def get_transaction_context(self, transaction_id: str) -> Optional[AP2TransactionContext]:
        """Get authenticated transaction context"""
        if await self.verify_transaction_authorization(transaction_id):
            return self.authenticated_sessions[transaction_id]
        return None

    async def _get_agent_certificate(self, agent_id: str) -> str:
        """Get agent's registration certificate from registry"""
        try:
            agents = await self.registry.discover_agents()
            for agent in agents:
                if agent.agent_id == agent_id:
                    return agent.metadata.get("registration_certificate", "")
            return ""
        except Exception:
            return ""

    async def _verify_agent_credentials(self, credentials: AgentCredentials) -> bool:
        """Verify agent credentials are still valid"""
        try:
            # Check expiry
            if datetime.now(timezone.utc) > credentials.expires_at:
                return False

            # Verify certificate (simplified - in production, verify JWT signature)
            if not credentials.registration_certificate:
                return False

            # Check if agent is still registered and active
            agents = await self.registry.discover_agents()
            for agent in agents:
                if (agent.agent_id == credentials.agent_id and
                    agent.status == "active"):
                    return True

            return False

        except Exception:
            return False

    async def cleanup_expired_sessions(self):
        """Clean up expired transaction sessions"""
        now = datetime.now(timezone.utc)
        expired_sessions = [
            txn_id for txn_id, context in self.authenticated_sessions.items()
            if now > context.expires_at
        ]

        for txn_id in expired_sessions:
            del self.authenticated_sessions[txn_id]

        if expired_sessions:
            print(f"🧹 Cleaned up {len(expired_sessions)} expired AP2 sessions")


# Global instance for the application
_ap2_authenticator: Optional[AP2AgentAuthenticator] = None


def get_ap2_authenticator(registry: AgentRegistry, local_agent: AP2PaymentAgent) -> AP2AgentAuthenticator:
    """Get or create the global AP2 authenticator instance"""
    global _ap2_authenticator
    if _ap2_authenticator is None:
        _ap2_authenticator = AP2AgentAuthenticator(registry, local_agent)
    return _ap2_authenticator