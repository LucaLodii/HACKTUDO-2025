"""
Agent Registry Implementation for Commercial Deployment

Implements a distributed agent registry system for merchant networks
following AP2 protocol specifications.
"""

import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from enum import Enum
from pydantic import BaseModel, Field
import asyncio
import aiohttp
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt


class AgentType(Enum):
    """Types of agents in the sofIA ecosystem."""
    ORCHESTRATOR = "orchestrator"
    PAYMENT_PROCESSOR = "payment_processor"
    MERCHANT_GATEWAY = "merchant_gateway"
    COMPLIANCE_VALIDATOR = "compliance_validator"
    FRAUD_DETECTOR = "fraud_detector"
    WHATSAPP_INTERFACE = "whatsapp_interface"
    BEMOBI_INTEGRATION = "bemobi_integration"


class PaymentMethod(Enum):
    """Supported payment methods by region."""
    PIX = "pix"  # Brazil
    BOLETO = "boleto"  # Brazil
    CREDIT_CARD = "credit_card"  # Global
    DEBIT_CARD = "debit_card"  # Global
    BANK_TRANSFER = "bank_transfer"  # Global
    MOBILE_MONEY = "mobile_money"  # Africa
    DIGITAL_WALLET = "digital_wallet"  # Asia


class Region(Enum):
    """Supported regions for merchant networks."""
    LATAM = "latam"
    AFRICA = "africa"
    ASIA = "asia"
    GLOBAL = "global"


@dataclass
class AgentCapability:
    """Represents a specific capability of an agent."""
    name: str
    version: str
    description: str
    supported_regions: List[Region]
    supported_payment_methods: List[PaymentMethod]
    ap2_mandate_types: List[str]  # intent, cart, payment
    max_throughput: int  # transactions per minute
    sla_response_time: float  # seconds
    requires_auth: bool
    cost_per_transaction: Optional[float] = None


@dataclass
class RegisteredAgent:
    """Represents a registered agent in the network."""
    agent_id: str
    agent_type: AgentType
    name: str
    description: str
    endpoint_url: str
    public_key: str  # PEM format RSA public key
    capabilities: List[AgentCapability]
    merchant_networks: List[str]  # BEMOBI client IDs
    status: str  # active, inactive, maintenance
    last_heartbeat: datetime
    registration_time: datetime
    certificate_expiry: datetime
    compliance_verified: bool
    metadata: Dict[str, Any]


class AgentRegistry:
    """
    Distributed Agent Registry for Commercial Deployment

    Manages agent discovery, capability negotiation, and network coordination
    for BEMOBI's merchant ecosystem.
    """

    def __init__(self, registry_id: str, private_key: Optional[rsa.RSAPrivateKey] = None):
        self.registry_id = registry_id
        self.agents: Dict[str, RegisteredAgent] = {}
        self.capabilities_index: Dict[str, Set[str]] = {}  # capability -> agent_ids
        self.region_index: Dict[Region, Set[str]] = {}  # region -> agent_ids
        self.merchant_index: Dict[str, Set[str]] = {}  # merchant_id -> agent_ids

        # Initialize cryptographic keys for registry security
        if private_key:
            self.private_key = private_key
        else:
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
        self.public_key = self.private_key.public_key()

        # Registry metadata
        self.created_at = datetime.now(timezone.utc)
        self.last_cleanup = datetime.now(timezone.utc)

    async def register_agent(self, agent: RegisteredAgent) -> bool:
        """
        Register a new agent in the network.

        Args:
            agent: Agent to register

        Returns:
            bool: Success status
        """
        try:
            # Validate agent registration
            if not await self._validate_agent_registration(agent):
                return False

            # Store agent
            self.agents[agent.agent_id] = agent

            # Update indices
            await self._update_indices(agent)

            # Generate registration certificate
            cert = await self._generate_registration_certificate(agent)
            agent.metadata["registration_certificate"] = cert

            print(f"✅ Agent registered: {agent.agent_id} ({agent.agent_type.value})")
            return True

        except Exception as e:
            print(f"❌ Agent registration failed for {agent.agent_id}: {e}")
            return False

    async def discover_agents(
        self,
        agent_type: Optional[AgentType] = None,
        capability: Optional[str] = None,
        region: Optional[Region] = None,
        merchant_id: Optional[str] = None,
        payment_method: Optional[PaymentMethod] = None
    ) -> List[RegisteredAgent]:
        """
        Discover agents based on criteria.

        Args:
            agent_type: Filter by agent type
            capability: Filter by capability name
            region: Filter by supported region
            merchant_id: Filter by merchant network
            payment_method: Filter by payment method support

        Returns:
            List of matching agents
        """
        matching_agents = set(self.agents.keys())

        # Filter by agent type
        if agent_type:
            type_filter = {
                agent_id for agent_id, agent in self.agents.items()
                if agent.agent_type == agent_type and agent.status == "active"
            }
            matching_agents &= type_filter

        # Filter by capability
        if capability:
            cap_filter = self.capabilities_index.get(capability, set())
            matching_agents &= cap_filter

        # Filter by region
        if region:
            region_filter = self.region_index.get(region, set())
            matching_agents &= region_filter

        # Filter by merchant
        if merchant_id:
            merchant_filter = self.merchant_index.get(merchant_id, set())
            matching_agents &= merchant_filter

        # Filter by payment method
        if payment_method:
            payment_filter = {
                agent_id for agent_id in matching_agents
                if any(
                    payment_method in cap.supported_payment_methods
                    for cap in self.agents[agent_id].capabilities
                )
            }
            matching_agents &= payment_filter

        # Return active agents only
        return [
            self.agents[agent_id] for agent_id in matching_agents
            if self.agents[agent_id].status == "active"
        ]

    async def negotiate_capabilities(
        self,
        requester_id: str,
        target_agent_id: str,
        required_capabilities: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Negotiate capabilities between agents.

        Args:
            requester_id: ID of requesting agent
            target_agent_id: ID of target agent
            required_capabilities: List of required capability names
            context: Negotiation context (merchant_id, transaction_type, etc.)

        Returns:
            Negotiation result with agreed capabilities and terms
        """
        if target_agent_id not in self.agents:
            return {"success": False, "error": "Target agent not found"}

        target_agent = self.agents[target_agent_id]

        # Check if target agent supports required capabilities
        agent_capabilities = {cap.name: cap for cap in target_agent.capabilities}

        agreed_capabilities = []
        for req_cap in required_capabilities:
            if req_cap in agent_capabilities:
                cap = agent_capabilities[req_cap]

                # Validate region compatibility
                merchant_region = context.get("region")
                if merchant_region and Region(merchant_region) not in cap.supported_regions:
                    continue

                # Validate payment method compatibility
                payment_method = context.get("payment_method")
                if payment_method and PaymentMethod(payment_method) not in cap.supported_payment_methods:
                    continue

                agreed_capabilities.append({
                    "name": cap.name,
                    "version": cap.version,
                    "sla_response_time": cap.sla_response_time,
                    "max_throughput": cap.max_throughput,
                    "cost_per_transaction": cap.cost_per_transaction
                })

        if not agreed_capabilities:
            return {"success": False, "error": "No compatible capabilities found"}

        # Generate capability agreement token
        agreement = {
            "requester_id": requester_id,
            "provider_id": target_agent_id,
            "capabilities": agreed_capabilities,
            "context": context,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        }

        # Sign agreement
        agreement_token = await self._sign_capability_agreement(agreement)

        return {
            "success": True,
            "agreement": agreement,
            "agreement_token": agreement_token,
            "provider_endpoint": target_agent.endpoint_url
        }

    async def heartbeat(self, agent_id: str, status_data: Dict[str, Any]) -> bool:
        """
        Process agent heartbeat to maintain registry.

        Args:
            agent_id: ID of agent sending heartbeat
            status_data: Current status information

        Returns:
            bool: Success status
        """
        if agent_id not in self.agents:
            return False

        agent = self.agents[agent_id]
        agent.last_heartbeat = datetime.now(timezone.utc)
        agent.status = status_data.get("status", "active")

        # Update metadata with current metrics
        agent.metadata.update({
            "current_load": status_data.get("current_load", 0),
            "response_time_avg": status_data.get("response_time_avg", 0),
            "error_rate": status_data.get("error_rate", 0),
            "last_heartbeat_data": status_data
        })

        return True

    async def cleanup_stale_agents(self, timeout_minutes: int = 15):
        """Remove agents that haven't sent heartbeat within timeout."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)

        stale_agents = [
            agent_id for agent_id, agent in self.agents.items()
            if agent.last_heartbeat < cutoff_time
        ]

        for agent_id in stale_agents:
            await self.unregister_agent(agent_id)
            print(f"🧹 Removed stale agent: {agent_id}")

        self.last_cleanup = datetime.now(timezone.utc)

    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the network."""
        if agent_id not in self.agents:
            return False

        agent = self.agents[agent_id]

        # Remove from indices
        await self._remove_from_indices(agent)

        # Remove from registry
        del self.agents[agent_id]

        print(f"🔴 Agent unregistered: {agent_id}")
        return True

    async def get_network_stats(self) -> Dict[str, Any]:
        """Get comprehensive network statistics."""
        active_agents = [a for a in self.agents.values() if a.status == "active"]

        return {
            "registry_id": self.registry_id,
            "total_agents": len(self.agents),
            "active_agents": len(active_agents),
            "agent_types": {
                agent_type.value: len([
                    a for a in active_agents if a.agent_type == agent_type
                ])
                for agent_type in AgentType
            },
            "supported_regions": list(self.region_index.keys()),
            "merchant_networks": len(self.merchant_index),
            "last_cleanup": self.last_cleanup.isoformat(),
            "registry_uptime": (datetime.now(timezone.utc) - self.created_at).total_seconds()
        }

    # Private helper methods

    async def _validate_agent_registration(self, agent: RegisteredAgent) -> bool:
        """Validate agent registration data."""
        # Check required fields
        if not all([agent.agent_id, agent.name, agent.endpoint_url, agent.public_key]):
            return False

        # Validate public key format
        try:
            serialization.load_pem_public_key(agent.public_key.encode())
        except Exception:
            return False

        # Check for duplicate agent ID
        if agent.agent_id in self.agents:
            return False

        # Validate endpoint accessibility
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{agent.endpoint_url}/health", timeout=5) as resp:
                    if resp.status != 200:
                        return False
        except Exception:
            return False

        return True

    async def _update_indices(self, agent: RegisteredAgent):
        """Update search indices with new agent."""
        # Capability index
        for capability in agent.capabilities:
            if capability.name not in self.capabilities_index:
                self.capabilities_index[capability.name] = set()
            self.capabilities_index[capability.name].add(agent.agent_id)

            # Region index
            for region in capability.supported_regions:
                if region not in self.region_index:
                    self.region_index[region] = set()
                self.region_index[region].add(agent.agent_id)

        # Merchant index
        for merchant_id in agent.merchant_networks:
            if merchant_id not in self.merchant_index:
                self.merchant_index[merchant_id] = set()
            self.merchant_index[merchant_id].add(agent.agent_id)

    async def _remove_from_indices(self, agent: RegisteredAgent):
        """Remove agent from search indices."""
        # Capability index
        for capability in agent.capabilities:
            if capability.name in self.capabilities_index:
                self.capabilities_index[capability.name].discard(agent.agent_id)
                if not self.capabilities_index[capability.name]:
                    del self.capabilities_index[capability.name]

            # Region index
            for region in capability.supported_regions:
                if region in self.region_index:
                    self.region_index[region].discard(agent.agent_id)
                    if not self.region_index[region]:
                        del self.region_index[region]

        # Merchant index
        for merchant_id in agent.merchant_networks:
            if merchant_id in self.merchant_index:
                self.merchant_index[merchant_id].discard(agent.agent_id)
                if not self.merchant_index[merchant_id]:
                    del self.merchant_index[merchant_id]

    async def _generate_registration_certificate(self, agent: RegisteredAgent) -> str:
        """Generate cryptographically signed registration certificate."""
        cert_data = {
            "agent_id": agent.agent_id,
            "agent_type": agent.agent_type.value,
            "registry_id": self.registry_id,
            "issued_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": agent.certificate_expiry.isoformat(),
            "capabilities": [cap.name for cap in agent.capabilities]
        }

        # Sign with registry private key
        token = jwt.encode(cert_data, self.private_key, algorithm="RS256")
        return token

    async def _sign_capability_agreement(self, agreement: Dict[str, Any]) -> str:
        """Sign capability agreement with registry key."""
        token = jwt.encode(agreement, self.private_key, algorithm="RS256")
        return token