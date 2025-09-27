"""
Agent Registry System for sofIA Multi-Agent Payment Platform

This module implements the agent discovery and capability negotiation system
for commercial deployment with merchant networks.
"""

from .agent_registry import AgentRegistry, AgentCapability, RegisteredAgent
from .discovery_service import AgentDiscoveryService
from .capability_negotiation import CapabilityNegotiator

__all__ = [
    "AgentRegistry",
    "AgentCapability",
    "RegisteredAgent",
    "AgentDiscoveryService",
    "CapabilityNegotiator"
]