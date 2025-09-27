"""
Agent Registry and Discovery Tool for sofIA Agent

Provides agent discovery, capability negotiation, and network coordination
capabilities for multi-agent payment ecosystems.
"""

from google.adk.tools import Tool
from typing import Dict, Any, List, Optional
import json

from ...registry import AgentRegistry, CapabilityNegotiator
from ...communication import A2AProtocol


def discover_agents(
    capabilities: List[str] = None,
    location: Optional[str] = None,
    max_results: int = 10
) -> Dict[str, Any]:
    """
    Discover payment agents in the network.

    Args:
        capabilities: Required agent capabilities
        location: Geographic location filter
        max_results: Maximum number of results

    Returns:
        List of discovered agents with their capabilities
    """
    try:
        registry = AgentRegistry()
        agents = registry.discover_agents(
            capabilities=capabilities,
            location=location,
            max_results=max_results
        )

        return {
            "success": True,
            "agents": [
                {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "capabilities": [cap.name for cap in agent.capabilities],
                    "location": agent.location,
                    "reputation_score": agent.reputation_score,
                    "last_seen": agent.last_seen.isoformat()
                }
                for agent in agents
            ],
            "total_found": len(agents)
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Agent discovery failed: {str(e)}"
        }


def negotiate_capabilities(
    target_agent_id: str,
    required_capabilities: List[str],
    preferred_terms: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Negotiate capabilities with another agent.

    Args:
        target_agent_id: Target agent identifier
        required_capabilities: Required capabilities for negotiation
        preferred_terms: Preferred terms (pricing, SLA, etc.)

    Returns:
        Negotiation result with agreed terms
    """
    try:
        negotiator = CapabilityNegotiator()

        session = negotiator.initiate_negotiation(
            target_agent_id=target_agent_id,
            required_capabilities=required_capabilities,
            preferred_terms=preferred_terms or {}
        )

        # Auto-negotiate using AI optimization
        result = negotiator.auto_negotiate(session.session_id)

        return {
            "success": True,
            "session_id": session.session_id,
            "negotiation_status": result.status.value,
            "agreed_terms": result.agreed_terms,
            "total_cost": result.total_cost,
            "sla_requirements": result.sla_requirements
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Capability negotiation failed: {str(e)}"
        }


def register_agent_capability(
    capability_name: str,
    capability_type: str,
    pricing_model: Dict[str, Any],
    sla_terms: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Register a new capability for this agent.

    Args:
        capability_name: Name of the capability
        capability_type: Type of capability (payment, verification, etc.)
        pricing_model: Pricing structure for the capability
        sla_terms: Service level agreement terms

    Returns:
        Registration status
    """
    try:
        registry = AgentRegistry()

        success = registry.register_capability(
            capability_name=capability_name,
            capability_type=capability_type,
            pricing_model=pricing_model,
            sla_terms=sla_terms or {}
        )

        if success:
            return {
                "success": True,
                "capability_name": capability_name,
                "message": "Capability registered successfully"
            }
        else:
            return {
                "success": False,
                "error": "Failed to register capability"
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Capability registration failed: {str(e)}"
        }


def send_a2a_message(
    target_agent_id: str,
    message_type: str,
    payload: Dict[str, Any],
    security_level: str = "standard"
) -> Dict[str, Any]:
    """
    Send an Agent-to-Agent protocol message.

    Args:
        target_agent_id: Target agent identifier
        message_type: Type of message (intent, cart, payment, etc.)
        payload: Message payload
        security_level: Security level (standard, high, critical)

    Returns:
        Message sending status and response
    """
    try:
        protocol = A2AProtocol()

        message_id = protocol.send_message(
            target_agent_id=target_agent_id,
            message_type=message_type,
            payload=payload,
            security_level=security_level
        )

        return {
            "success": True,
            "message_id": message_id,
            "target_agent": target_agent_id,
            "message_type": message_type,
            "security_level": security_level
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"A2A message sending failed: {str(e)}"
        }


registry_tool = Tool(
    name="agent_registry",
    description="Agent discovery, capability negotiation, and A2A communication for payment networks",
    function_declarations=[
        {
            "name": "discover_agents",
            "description": "Discover payment agents in the network with specific capabilities",
            "parameters": {
                "type": "object",
                "properties": {
                    "capabilities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Required agent capabilities"
                    },
                    "location": {
                        "type": "string",
                        "description": "Geographic location filter"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 10
                    }
                }
            }
        },
        {
            "name": "negotiate_capabilities",
            "description": "Negotiate capabilities and terms with another agent",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_agent_id": {
                        "type": "string",
                        "description": "Target agent identifier"
                    },
                    "required_capabilities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Required capabilities for negotiation"
                    },
                    "preferred_terms": {
                        "type": "object",
                        "description": "Preferred terms (pricing, SLA, etc.)"
                    }
                },
                "required": ["target_agent_id", "required_capabilities"]
            }
        },
        {
            "name": "register_agent_capability",
            "description": "Register a new capability for this agent",
            "parameters": {
                "type": "object",
                "properties": {
                    "capability_name": {
                        "type": "string",
                        "description": "Name of the capability"
                    },
                    "capability_type": {
                        "type": "string",
                        "description": "Type of capability (payment, verification, etc.)"
                    },
                    "pricing_model": {
                        "type": "object",
                        "description": "Pricing structure for the capability"
                    },
                    "sla_terms": {
                        "type": "object",
                        "description": "Service level agreement terms"
                    }
                },
                "required": ["capability_name", "capability_type", "pricing_model"]
            }
        },
        {
            "name": "send_a2a_message",
            "description": "Send an Agent-to-Agent protocol message",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_agent_id": {
                        "type": "string",
                        "description": "Target agent identifier"
                    },
                    "message_type": {
                        "type": "string",
                        "description": "Type of message (intent, cart, payment, etc.)"
                    },
                    "payload": {
                        "type": "object",
                        "description": "Message payload"
                    },
                    "security_level": {
                        "type": "string",
                        "description": "Security level (standard, high, critical)",
                        "default": "standard"
                    }
                },
                "required": ["target_agent_id", "message_type", "payload"]
            }
        }
    ],
    functions={
        "discover_agents": discover_agents,
        "negotiate_capabilities": negotiate_capabilities,
        "register_agent_capability": register_agent_capability,
        "send_a2a_message": send_a2a_message
    }
)