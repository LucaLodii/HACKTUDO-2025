"""
Agent Capability Negotiation Protocol

Implements sophisticated capability negotiation between agents in the sofIA
ecosystem, supporting dynamic pricing, SLA agreements, and resource allocation.
"""

import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
from cryptography.hazmat.primitives import hashes
import jwt

from .agent_registry import AgentRegistry, AgentCapability, RegisteredAgent, PaymentMethod, Region


class NegotiationStatus(Enum):
    """Status of capability negotiation."""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COUNTER_PROPOSED = "counter_proposed"
    AGREED = "agreed"
    REJECTED = "rejected"
    EXPIRED = "expired"


class PricingModel(Enum):
    """Pricing models for agent capabilities."""
    FIXED_PER_TRANSACTION = "fixed_per_transaction"
    TIERED_VOLUME = "tiered_volume"
    SUBSCRIPTION = "subscription"
    PERFORMANCE_BASED = "performance_based"
    AUCTION = "auction"


@dataclass
class CapabilityRequest:
    """Represents a capability request from an agent."""
    request_id: str
    requester_id: str
    capability_name: str
    required_sla: Dict[str, Any]  # response_time, availability, throughput
    context: Dict[str, Any]  # merchant_id, region, payment_method, volume
    max_price: Optional[float] = None
    preferred_providers: Optional[List[str]] = None
    deadline: Optional[datetime] = None


@dataclass
class CapabilityOffer:
    """Represents a capability offer from a provider agent."""
    offer_id: str
    provider_id: str
    capability_name: str
    offered_sla: Dict[str, Any]
    pricing: Dict[str, Any]  # model, base_price, volume_discounts
    terms: Dict[str, Any]  # contract_duration, penalties, guarantees
    valid_until: datetime


@dataclass
class NegotiationSession:
    """Represents an active negotiation session."""
    session_id: str
    request: CapabilityRequest
    offers: List[CapabilityOffer]
    status: NegotiationStatus
    current_round: int
    created_at: datetime
    last_activity: datetime
    final_agreement: Optional[Dict[str, Any]] = None


class CapabilityNegotiator:
    """
    Advanced Capability Negotiation Engine

    Handles complex multi-party negotiations between agents with support for:
    - Dynamic pricing models
    - SLA negotiations
    - Performance-based contracts
    - Real-time bidding for high-volume transactions
    """

    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self.active_sessions: Dict[str, NegotiationSession] = {}
        self.negotiation_history: List[NegotiationSession] = []

    async def initiate_negotiation(
        self,
        request: CapabilityRequest,
        target_providers: Optional[List[str]] = None
    ) -> str:
        """
        Initiate capability negotiation process.

        Args:
            request: Capability request details
            target_providers: Specific providers to negotiate with (optional)

        Returns:
            session_id: Unique identifier for the negotiation session
        """
        session_id = f"neg_{request.request_id}_{int(datetime.now().timestamp())}"

        # Discover suitable providers if not specified
        if not target_providers:
            providers = await self._discover_capable_providers(request)
            target_providers = [p.agent_id for p in providers]

        # Create negotiation session
        session = NegotiationSession(
            session_id=session_id,
            request=request,
            offers=[],
            status=NegotiationStatus.INITIATED,
            current_round=1,
            created_at=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc)
        )

        self.active_sessions[session_id] = session

        # Send capability requests to providers
        await self._broadcast_capability_request(session, target_providers)

        print(f"🤝 Negotiation initiated: {session_id} with {len(target_providers)} providers")
        return session_id

    async def submit_offer(
        self,
        session_id: str,
        offer: CapabilityOffer
    ) -> bool:
        """
        Submit a capability offer for a negotiation session.

        Args:
            session_id: Active negotiation session
            offer: Capability offer from provider

        Returns:
            bool: Success status
        """
        if session_id not in self.active_sessions:
            return False

        session = self.active_sessions[session_id]

        # Validate offer
        if not await self._validate_offer(session.request, offer):
            return False

        # Add offer to session
        session.offers.append(offer)
        session.last_activity = datetime.now(timezone.utc)
        session.status = NegotiationStatus.IN_PROGRESS

        print(f"💰 Offer received: {offer.provider_id} -> {session_id}")

        # Check if negotiation can be concluded
        await self._evaluate_negotiation_status(session)

        return True

    async def evaluate_offers(
        self,
        session_id: str,
        evaluation_criteria: Dict[str, float]
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluate all offers in a negotiation session.

        Args:
            session_id: Negotiation session to evaluate
            evaluation_criteria: Weights for different criteria (price, sla, reputation)

        Returns:
            Evaluation results with ranked offers
        """
        if session_id not in self.active_sessions:
            return None

        session = self.active_sessions[session_id]

        if not session.offers:
            return {"error": "No offers to evaluate"}

        # Score each offer
        scored_offers = []
        for offer in session.offers:
            score = await self._score_offer(offer, session.request, evaluation_criteria)
            scored_offers.append({
                "offer": offer,
                "score": score,
                "breakdown": score.get("breakdown", {})
            })

        # Sort by score
        scored_offers.sort(key=lambda x: x["score"]["total"], reverse=True)

        return {
            "session_id": session_id,
            "total_offers": len(scored_offers),
            "best_offer": scored_offers[0] if scored_offers else None,
            "all_offers": scored_offers,
            "evaluation_criteria": evaluation_criteria
        }

    async def accept_offer(
        self,
        session_id: str,
        offer_id: str,
        terms_modifications: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Accept a capability offer and create binding agreement.

        Args:
            session_id: Negotiation session
            offer_id: Specific offer to accept
            terms_modifications: Any final terms modifications

        Returns:
            Final agreement details
        """
        if session_id not in self.active_sessions:
            return None

        session = self.active_sessions[session_id]

        # Find the accepted offer
        accepted_offer = None
        for offer in session.offers:
            if offer.offer_id == offer_id:
                accepted_offer = offer
                break

        if not accepted_offer:
            return None

        # Create final agreement
        agreement = await self._create_capability_agreement(
            session.request,
            accepted_offer,
            terms_modifications
        )

        # Update session
        session.status = NegotiationStatus.AGREED
        session.final_agreement = agreement
        session.last_activity = datetime.now(timezone.utc)

        # Archive session
        self.negotiation_history.append(session)
        del self.active_sessions[session_id]

        # Notify all parties
        await self._notify_negotiation_completion(session, agreement)

        print(f"✅ Negotiation completed: {session_id} -> {accepted_offer.provider_id}")
        return agreement

    async def counter_propose(
        self,
        session_id: str,
        offer_id: str,
        counter_terms: Dict[str, Any]
    ) -> bool:
        """
        Submit a counter-proposal for an existing offer.

        Args:
            session_id: Negotiation session
            offer_id: Original offer to counter
            counter_terms: Modified terms for counter-proposal

        Returns:
            bool: Success status
        """
        if session_id not in self.active_sessions:
            return False

        session = self.active_sessions[session_id]

        # Find original offer
        original_offer = None
        for offer in session.offers:
            if offer.offer_id == offer_id:
                original_offer = offer
                break

        if not original_offer:
            return False

        # Send counter-proposal to provider
        await self._send_counter_proposal(
            session,
            original_offer.provider_id,
            counter_terms
        )

        session.status = NegotiationStatus.COUNTER_PROPOSED
        session.current_round += 1
        session.last_activity = datetime.now(timezone.utc)

        return True

    async def get_negotiation_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a negotiation session."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
        else:
            # Check history
            session = next(
                (s for s in self.negotiation_history if s.session_id == session_id),
                None
            )

        if not session:
            return None

        return {
            "session_id": session.session_id,
            "status": session.status.value,
            "current_round": session.current_round,
            "total_offers": len(session.offers),
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "request": asdict(session.request),
            "final_agreement": session.final_agreement
        }

    async def cleanup_expired_sessions(self, timeout_hours: int = 24):
        """Clean up expired negotiation sessions."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=timeout_hours)

        expired_sessions = [
            session_id for session_id, session in self.active_sessions.items()
            if session.last_activity < cutoff_time
        ]

        for session_id in expired_sessions:
            session = self.active_sessions[session_id]
            session.status = NegotiationStatus.EXPIRED

            # Archive expired session
            self.negotiation_history.append(session)
            del self.active_sessions[session_id]

            print(f"⏰ Expired negotiation session: {session_id}")

    # Private helper methods

    async def _discover_capable_providers(
        self,
        request: CapabilityRequest
    ) -> List[RegisteredAgent]:
        """Discover agents capable of providing the requested capability."""
        # Extract context for filtering
        region = request.context.get("region")
        payment_method = request.context.get("payment_method")

        # Use registry discovery
        providers = await self.registry.discover_agents(
            capability=request.capability_name,
            region=Region(region) if region else None,
            payment_method=PaymentMethod(payment_method) if payment_method else None
        )

        # Filter by SLA requirements
        qualified_providers = []
        for provider in providers:
            for capability in provider.capabilities:
                if capability.name == request.capability_name:
                    # Check SLA compatibility
                    if self._check_sla_compatibility(request.required_sla, capability):
                        qualified_providers.append(provider)
                    break

        return qualified_providers

    def _check_sla_compatibility(
        self,
        required_sla: Dict[str, Any],
        capability: AgentCapability
    ) -> bool:
        """Check if agent capability meets required SLA."""
        # Response time check
        required_response_time = required_sla.get("response_time", float('inf'))
        if capability.sla_response_time > required_response_time:
            return False

        # Throughput check
        required_throughput = required_sla.get("throughput", 0)
        if capability.max_throughput < required_throughput:
            return False

        return True

    async def _broadcast_capability_request(
        self,
        session: NegotiationSession,
        target_providers: List[str]
    ):
        """Send capability request to target providers."""
        request_data = {
            "session_id": session.session_id,
            "request": asdict(session.request),
            "deadline": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        }

        # Send to each provider
        for provider_id in target_providers:
            if provider_id in self.registry.agents:
                provider = self.registry.agents[provider_id]
                await self._send_to_agent(
                    provider.endpoint_url,
                    "/negotiate/capability-request",
                    request_data
                )

    async def _validate_offer(
        self,
        request: CapabilityRequest,
        offer: CapabilityOffer
    ) -> bool:
        """Validate that an offer meets basic requirements."""
        # Check capability name match
        if offer.capability_name != request.capability_name:
            return False

        # Check price limits
        if request.max_price and offer.pricing.get("base_price", 0) > request.max_price:
            return False

        # Check deadline
        if request.deadline and offer.valid_until < request.deadline:
            return False

        # Check SLA requirements
        required_sla = request.required_sla
        offered_sla = offer.offered_sla

        response_time_ok = (
            offered_sla.get("response_time", float('inf')) <=
            required_sla.get("response_time", float('inf'))
        )

        throughput_ok = (
            offered_sla.get("throughput", 0) >=
            required_sla.get("throughput", 0)
        )

        return response_time_ok and throughput_ok

    async def _score_offer(
        self,
        offer: CapabilityOffer,
        request: CapabilityRequest,
        criteria: Dict[str, float]
    ) -> Dict[str, Any]:
        """Score an offer based on evaluation criteria."""
        scores = {}

        # Price score (lower is better)
        base_price = offer.pricing.get("base_price", 0)
        max_acceptable_price = request.max_price or base_price * 2
        price_score = max(0, (max_acceptable_price - base_price) / max_acceptable_price)
        scores["price"] = price_score

        # SLA score
        offered_response_time = offer.offered_sla.get("response_time", float('inf'))
        required_response_time = request.required_sla.get("response_time", offered_response_time)
        sla_score = max(0, (required_response_time - offered_response_time) / required_response_time)
        scores["sla"] = min(1.0, sla_score)

        # Provider reputation score (based on historical performance)
        reputation_score = await self._get_provider_reputation(offer.provider_id)
        scores["reputation"] = reputation_score

        # Contract terms score
        terms_score = self._evaluate_contract_terms(offer.terms)
        scores["terms"] = terms_score

        # Calculate weighted total
        total_score = sum(
            scores[criterion] * weight
            for criterion, weight in criteria.items()
            if criterion in scores
        )

        return {
            "total": total_score,
            "breakdown": scores
        }

    async def _get_provider_reputation(self, provider_id: str) -> float:
        """Get reputation score for a provider based on history."""
        # In a real implementation, this would query historical performance data
        # For now, return a default score
        return 0.8

    def _evaluate_contract_terms(self, terms: Dict[str, Any]) -> float:
        """Evaluate contract terms and return a score."""
        score = 0.5  # Base score

        # Penalty terms (lower penalties = higher score)
        penalties = terms.get("penalties", {})
        if not penalties:
            score += 0.2

        # Contract duration flexibility
        duration = terms.get("contract_duration", "1_month")
        if duration in ["1_month", "3_months"]:
            score += 0.2

        # Guarantees (more guarantees = higher score)
        guarantees = terms.get("guarantees", [])
        score += min(0.1, len(guarantees) * 0.05)

        return min(1.0, score)

    async def _create_capability_agreement(
        self,
        request: CapabilityRequest,
        offer: CapabilityOffer,
        modifications: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a binding capability agreement."""
        agreement = {
            "agreement_id": f"cap_agreement_{int(datetime.now().timestamp())}",
            "requester_id": request.requester_id,
            "provider_id": offer.provider_id,
            "capability_name": offer.capability_name,
            "agreed_sla": offer.offered_sla,
            "pricing": offer.pricing,
            "terms": offer.terms,
            "context": request.context,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "status": "active"
        }

        # Apply any modifications
        if modifications:
            agreement.update(modifications)

        # Sign agreement with registry key
        agreement_token = await self.registry._sign_capability_agreement(agreement)
        agreement["signature"] = agreement_token

        return agreement

    async def _send_counter_proposal(
        self,
        session: NegotiationSession,
        provider_id: str,
        counter_terms: Dict[str, Any]
    ):
        """Send counter-proposal to provider."""
        if provider_id not in self.registry.agents:
            return

        provider = self.registry.agents[provider_id]
        counter_data = {
            "session_id": session.session_id,
            "counter_terms": counter_terms,
            "round": session.current_round
        }

        await self._send_to_agent(
            provider.endpoint_url,
            "/negotiate/counter-proposal",
            counter_data
        )

    async def _notify_negotiation_completion(
        self,
        session: NegotiationSession,
        agreement: Dict[str, Any]
    ):
        """Notify all parties of negotiation completion."""
        notification_data = {
            "session_id": session.session_id,
            "status": "completed",
            "agreement": agreement
        }

        # Notify requester
        requester = self.registry.agents.get(session.request.requester_id)
        if requester:
            await self._send_to_agent(
                requester.endpoint_url,
                "/negotiate/completion",
                notification_data
            )

        # Notify accepted provider
        provider = self.registry.agents.get(agreement["provider_id"])
        if provider:
            await self._send_to_agent(
                provider.endpoint_url,
                "/negotiate/completion",
                notification_data
            )

    async def _evaluate_negotiation_status(self, session: NegotiationSession):
        """Evaluate if negotiation can be concluded automatically."""
        # Check if we have enough offers to auto-conclude
        if len(session.offers) >= 3:  # Configurable threshold
            # Auto-evaluate and potentially conclude
            evaluation = await self.evaluate_offers(
                session.session_id,
                {"price": 0.4, "sla": 0.3, "reputation": 0.2, "terms": 0.1}
            )

            # If there's a clearly superior offer, could auto-accept
            if evaluation and evaluation.get("best_offer"):
                best_score = evaluation["best_offer"]["score"]["total"]
                if best_score > 0.8:  # High threshold for auto-acceptance
                    print(f"🎯 High-quality offer detected in {session.session_id}")

    async def _send_to_agent(
        self,
        endpoint_url: str,
        path: str,
        data: Dict[str, Any]
    ):
        """Send HTTP request to agent endpoint."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{endpoint_url}{path}",
                    json=data,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            print(f"❌ Failed to send to agent {endpoint_url}: {e}")

        return None