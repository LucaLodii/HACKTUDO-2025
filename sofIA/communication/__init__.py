"""
Enhanced Agent-to-Agent (A2A) Communication Protocol

Implements standardized, secure, and auditable communication protocol
for commercial deployment of the sofIA multi-agent system.
"""

from .a2a_protocol import A2AProtocol, A2AMessage, MessageType, SecurityLevel
from .message_router import MessageRouter
from .audit_logger import A2AAuditLogger

__all__ = [
    "A2AProtocol",
    "A2AMessage",
    "MessageType",
    "SecurityLevel",
    "MessageRouter",
    "A2AAuditLogger"
]