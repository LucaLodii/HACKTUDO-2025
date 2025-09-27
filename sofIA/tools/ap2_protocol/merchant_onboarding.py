"""
Merchant Credential Acquisition and Onboarding for AP2 Protocol

This module implements the merchant onboarding process, credential acquisition,
and agent registration for AP2-compliant payment processing.
"""

import asyncio
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from sofIA.registry.agent_registry import (
    AgentRegistry, RegisteredAgent, AgentCapability, AgentType,
    Region, PaymentMethod
)
from .ap2_core import AP2PaymentAgent, MandateSigner


@dataclass
class MerchantCredentials:
    """Merchant credentials for AP2 protocol"""
    merchant_id: str
    merchant_name: str
    api_key: str
    public_key: str
    private_key: str  # Encrypted in production
    agent_id: str
    supported_payment_methods: List[PaymentMethod]
    supported_regions: List[Region]
    webhook_url: str
    status: str


class MerchantOnboardingService:
    """
    Handles merchant onboarding and credential acquisition for AP2 protocol.

    This service manages:
    1. Merchant registration and KYC verification
    2. Agent credential generation and registration
    3. Payment method configuration
    4. Webhook setup for real-time notifications
    """

    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self.onboarded_merchants: Dict[str, MerchantCredentials] = {}

    async def onboard_merchant(
        self,
        merchant_id: str,
        merchant_name: str,
        business_type: str,
        supported_regions: List[str] = ["latam"],
        supported_payment_methods: List[str] = ["pix", "credit_card", "boleto"],
        webhook_url: Optional[str] = None
    ) -> MerchantCredentials:
        """
        Complete merchant onboarding process with AP2 agent registration.

        This simulates the process that would happen when a BEMOBI client
        (like VIVO, CLARO, OI, TIM) onboards to use sofIA.
        """

        print(f"🏢 Starting merchant onboarding: {merchant_name} ({merchant_id})")

        # Step 1: Generate merchant agent credentials
        merchant_agent_id = f"merchant-{merchant_id}-agent"

        # Generate RSA key pair for the merchant agent
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()

        # Serialize keys
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()  # In production, encrypt this
        ).decode()

        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

        # Step 2: Create merchant agent capabilities
        region_enums = [Region(r.lower()) for r in supported_regions]
        payment_method_enums = [PaymentMethod(pm.lower()) for pm in supported_payment_methods]

        capabilities = [
            AgentCapability(
                name="merchant_payment_processing",
                version="1.0",
                description=f"Payment processing for {merchant_name}",
                supported_regions=region_enums,
                supported_payment_methods=payment_method_enums,
                ap2_mandate_types=["cart", "payment"],
                max_throughput=2000,  # Telecom operators need high throughput
                sla_response_time=1.0,
                requires_auth=True,
                cost_per_transaction=0.15
            ),
            AgentCapability(
                name="ap2_payment_mandates",
                version="1.0",
                description=f"AP2 payment mandate processing for {merchant_name}",
                supported_regions=region_enums,
                supported_payment_methods=payment_method_enums,
                ap2_mandate_types=["payment"],
                max_throughput=2000,
                sla_response_time=1.0,
                requires_auth=True,
                cost_per_transaction=0.15
            ),
            AgentCapability(
                name="merchant_webhook_notifications",
                version="1.0",
                description=f"Real-time payment notifications for {merchant_name}",
                supported_regions=region_enums,
                supported_payment_methods=payment_method_enums,
                ap2_mandate_types=["payment"],
                max_throughput=5000,
                sla_response_time=0.5,
                requires_auth=True,
                cost_per_transaction=0.05
            )
        ]

        # Step 3: Register merchant agent with the registry
        merchant_agent = RegisteredAgent(
            agent_id=merchant_agent_id,
            agent_type=AgentType.MERCHANT_GATEWAY,
            name=f"{merchant_name} Payment Agent",
            description=f"AP2-compliant payment agent for {merchant_name} ({business_type})",
            endpoint_url=webhook_url or f"https://api.{merchant_id}.com/webhooks/sofia",
            public_key=public_key_pem,
            capabilities=capabilities,
            merchant_networks=[merchant_id, "bemobi-network"],
            status="active",
            last_heartbeat=datetime.now(timezone.utc),
            registration_time=datetime.now(timezone.utc),
            certificate_expiry=datetime.now(timezone.utc) + timedelta(days=365),
            compliance_verified=True,
            metadata={
                "business_type": business_type,
                "onboarding_date": datetime.now(timezone.utc).isoformat(),
                "kyc_verified": True,
                "pci_compliant": True,
                "ap2_version": "1.0"
            }
        )

        # Register the merchant agent
        registration_success = await self.registry.register_agent(merchant_agent)

        if not registration_success:
            raise Exception(f"Failed to register merchant agent for {merchant_id}")

        # Step 4: Generate API credentials
        api_key = f"bemobi_{merchant_id}_{datetime.now().timestamp()}"

        # Step 5: Create merchant credentials
        merchant_credentials = MerchantCredentials(
            merchant_id=merchant_id,
            merchant_name=merchant_name,
            api_key=api_key,
            public_key=public_key_pem,
            private_key=private_key_pem,  # Store encrypted in production
            agent_id=merchant_agent_id,
            supported_payment_methods=payment_method_enums,
            supported_regions=region_enums,
            webhook_url=webhook_url or f"https://api.{merchant_id}.com/webhooks/sofia",
            status="active"
        )

        # Store merchant credentials
        self.onboarded_merchants[merchant_id] = merchant_credentials

        print(f"✅ Merchant onboarded successfully:")
        print(f"   Agent ID: {merchant_agent_id}")
        print(f"   API Key: {api_key[:20]}...")
        print(f"   Supported Regions: {[r.value for r in region_enums]}")
        print(f"   Payment Methods: {[pm.value for pm in payment_method_enums]}")

        return merchant_credentials

    async def get_merchant_credentials(self, merchant_id: str) -> Optional[MerchantCredentials]:
        """Get existing merchant credentials"""
        return self.onboarded_merchants.get(merchant_id)

    async def onboard_bemobi_telecom_operators(self) -> Dict[str, MerchantCredentials]:
        """
        Onboard BEMOBI's main telecom operator clients.

        This simulates the onboarding of VIVO, CLARO, OI, TIM as merchants
        using the sofIA payment platform.
        """

        print("🇧🇷 Onboarding BEMOBI Telecom Operators...")

        telecom_operators = [
            {
                "merchant_id": "vivo_brasil",
                "merchant_name": "Vivo Brasil",
                "business_type": "telecom_operator",
                "webhook_url": "https://api.vivo.com.br/webhooks/sofia"
            },
            {
                "merchant_id": "claro_brasil",
                "merchant_name": "Claro Brasil",
                "business_type": "telecom_operator",
                "webhook_url": "https://api.claro.com.br/webhooks/sofia"
            },
            {
                "merchant_id": "oi_brasil",
                "merchant_name": "Oi Brasil",
                "business_type": "telecom_operator",
                "webhook_url": "https://api.oi.com.br/webhooks/sofia"
            },
            {
                "merchant_id": "tim_brasil",
                "merchant_name": "TIM Brasil",
                "business_type": "telecom_operator",
                "webhook_url": "https://api.tim.com.br/webhooks/sofia"
            }
        ]

        onboarded = {}

        for operator in telecom_operators:
            try:
                credentials = await self.onboard_merchant(
                    merchant_id=operator["merchant_id"],
                    merchant_name=operator["merchant_name"],
                    business_type=operator["business_type"],
                    supported_regions=["latam"],
                    supported_payment_methods=["pix", "credit_card", "boleto"],
                    webhook_url=operator["webhook_url"]
                )
                onboarded[operator["merchant_id"]] = credentials

            except Exception as e:
                print(f"❌ Failed to onboard {operator['merchant_name']}: {e}")

        print(f"✅ Onboarded {len(onboarded)} telecom operators")
        return onboarded

    async def verify_merchant_agent(self, merchant_id: str) -> bool:
        """Verify that a merchant's agent is properly registered and active"""

        # Find merchant's agent in registry
        merchant_agents = await self.registry.discover_agents(
            agent_type=AgentType.MERCHANT_GATEWAY,
            merchant_id=merchant_id
        )

        if not merchant_agents:
            print(f"❌ No agent found for merchant {merchant_id}")
            return False

        agent = merchant_agents[0]

        # Verify agent is active and compliant
        if agent.status != "active":
            print(f"❌ Merchant agent {agent.agent_id} is not active")
            return False

        if not agent.compliance_verified:
            print(f"❌ Merchant agent {agent.agent_id} not compliance verified")
            return False

        print(f"✅ Merchant agent verified: {agent.agent_id}")
        return True


# Global instance for the application
_merchant_service: Optional[MerchantOnboardingService] = None


def get_merchant_service(registry: AgentRegistry) -> MerchantOnboardingService:
    """Get or create the global merchant onboarding service"""
    global _merchant_service
    if _merchant_service is None:
        _merchant_service = MerchantOnboardingService(registry)
    return _merchant_service