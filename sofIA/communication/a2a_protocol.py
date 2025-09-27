"""
Enhanced Agent-to-Agent Communication Protocol

Implements standardized, secure A2A communication with AP2 compliance,
message routing, encryption, and comprehensive audit trails.
"""

import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import aiohttp
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import jwt
import hashlib


class MessageType(Enum):
    """Types of A2A messages in the sofIA protocol."""
    # Core communication
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"

    # Payment flow
    PAYMENT_INTENT = "payment_intent"
    CART_CREATION = "cart_creation"
    PAYMENT_PROCESSING = "payment_processing"
    PAYMENT_CONFIRMATION = "payment_confirmation"

    # Agent coordination
    CAPABILITY_REQUEST = "capability_request"
    CAPABILITY_OFFER = "capability_offer"
    SERVICE_DISCOVERY = "service_discovery"
    HEALTH_CHECK = "health_check"

    # Security and compliance
    MANDATE_VERIFICATION = "mandate_verification"
    AUDIT_TRAIL = "audit_trail"
    COMPLIANCE_CHECK = "compliance_check"


class SecurityLevel(Enum):
    """Security levels for A2A messages."""
    PUBLIC = "public"          # No encryption, public information
    INTERNAL = "internal"      # Basic encryption, internal use
    CONFIDENTIAL = "confidential"  # Strong encryption, sensitive data
    RESTRICTED = "restricted"  # Maximum encryption, payment data


class MessagePriority(Enum):
    """Message priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


@dataclass
class A2AMessage:
    """
    Standardized Agent-to-Agent message format.

    Follows AP2 protocol specifications for secure agent communication.
    """
    # Message identification
    message_id: str
    correlation_id: Optional[str]  # Links related messages
    conversation_id: Optional[str]  # Groups messages in a conversation

    # Routing information
    sender_id: str
    receiver_id: str
    message_type: MessageType

    # Message content
    payload: Dict[str, Any]
    metadata: Dict[str, Any]

    # Security and compliance
    security_level: SecurityLevel
    priority: MessagePriority

    # Timestamps
    created_at: datetime
    expires_at: Optional[datetime]

    # Protocol information
    protocol_version: str = "1.0"

    # Cryptographic fields (added during transmission)
    signature: Optional[str] = None
    encrypted_payload: Optional[str] = None
    encryption_key_id: Optional[str] = None


class A2AProtocol:
    """
    Enhanced Agent-to-Agent Communication Protocol

    Provides secure, auditable, and standardized communication between
    agents in the sofIA ecosystem with full AP2 compliance.
    """

    def __init__(
        self,
        agent_id: str,
        private_key: rsa.RSAPrivateKey,
        registry_url: Optional[str] = None
    ):
        self.agent_id = agent_id
        self.private_key = private_key
        self.public_key = private_key.public_key()
        self.registry_url = registry_url

        # Message handling
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.middleware: List[Callable] = []

        # Security
        self.trusted_agents: Dict[str, rsa.RSAPublicKey] = {}
        self.encryption_keys: Dict[str, bytes] = {}

        # Audit and monitoring
        self.audit_logger = None
        self.message_queue: List[A2AMessage] = []
        self.retry_queue: List[Dict[str, Any]] = []

        # Performance metrics
        self.metrics = {
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0,
            "avg_response_time": 0.0
        }

    async def send_message(
        self,
        receiver_id: str,
        message_type: MessageType,
        payload: Dict[str, Any],
        security_level: SecurityLevel = SecurityLevel.INTERNAL,
        priority: MessagePriority = MessagePriority.NORMAL,
        correlation_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        expires_in_minutes: int = 60
    ) -> str:
        """
        Send an A2A message to another agent.

        Args:
            receiver_id: Target agent ID
            message_type: Type of message
            payload: Message content
            security_level: Required security level
            priority: Message priority
            correlation_id: Link to related messages
            conversation_id: Conversation context
            expires_in_minutes: Message expiry time

        Returns:
            message_id: Unique identifier for the sent message
        """
        # Create message
        message = A2AMessage(
            message_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            conversation_id=conversation_id,
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            message_type=message_type,
            payload=payload,
            metadata={
                "sender_capabilities": await self._get_sender_capabilities(),
                "protocol_compliance": "AP2_v1.0",
                "encryption_algorithms": ["RSA-2048", "AES-256-GCM"]
            },
            security_level=security_level,
            priority=priority,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
        )

        # Process message through middleware
        for middleware in self.middleware:
            message = await middleware(message, "outbound")

        # Apply security
        await self._apply_message_security(message)

        # Send message
        success = await self._transmit_message(message)

        if success:
            self.metrics["messages_sent"] += 1
            if self.audit_logger:
                await self.audit_logger.log_message_sent(message)
        else:
            # Add to retry queue
            self.retry_queue.append({
                "message": message,
                "attempts": 1,
                "next_retry": datetime.now(timezone.utc) + timedelta(seconds=30)
            })

        return message.message_id

    async def receive_message(self, raw_message: Dict[str, Any]) -> Optional[A2AMessage]:
        """
        Receive and process an A2A message.

        Args:
            raw_message: Raw message data from transport layer

        Returns:
            Processed A2A message or None if invalid
        """
        try:
            # Parse message
            message = self._parse_raw_message(raw_message)

            # Verify security
            if not await self._verify_message_security(message):
                print(f"❌ Security verification failed for message {message.message_id}")
                return None

            # Check expiry
            if message.expires_at and message.expires_at < datetime.now(timezone.utc):
                print(f"⏰ Message expired: {message.message_id}")
                return None

            # Process through middleware
            for middleware in self.middleware:
                message = await middleware(message, "inbound")

            # Update metrics
            self.metrics["messages_received"] += 1

            # Log audit trail
            if self.audit_logger:
                await self.audit_logger.log_message_received(message)

            # Route to handler
            await self._route_message(message)

            return message

        except Exception as e:
            self.metrics["errors"] += 1
            print(f"❌ Error receiving message: {e}")
            return None

    def register_handler(
        self,
        message_type: MessageType,
        handler: Callable[[A2AMessage], Any]
    ):
        """Register a handler for a specific message type."""
        self.message_handlers[message_type] = handler

    def add_middleware(self, middleware: Callable[[A2AMessage, str], A2AMessage]):
        """Add middleware for message processing."""
        self.middleware.append(middleware)

    async def request_response(
        self,
        receiver_id: str,
        request_type: MessageType,
        request_payload: Dict[str, Any],
        timeout_seconds: int = 30,
        security_level: SecurityLevel = SecurityLevel.INTERNAL
    ) -> Optional[A2AMessage]:
        """
        Send a request and wait for response.

        Args:
            receiver_id: Target agent ID
            request_type: Type of request
            request_payload: Request data
            timeout_seconds: Response timeout
            security_level: Security level

        Returns:
            Response message or None if timeout
        """
        correlation_id = str(uuid.uuid4())

        # Set up response handler
        response_event = asyncio.Event()
        response_message = None

        async def response_handler(message: A2AMessage):
            nonlocal response_message
            if message.correlation_id == correlation_id:
                response_message = message
                response_event.set()

        # Temporarily register response handler
        original_handler = self.message_handlers.get(MessageType.RESPONSE)
        self.message_handlers[MessageType.RESPONSE] = response_handler

        try:
            # Send request
            await self.send_message(
                receiver_id=receiver_id,
                message_type=request_type,
                payload=request_payload,
                security_level=security_level,
                correlation_id=correlation_id
            )

            # Wait for response
            await asyncio.wait_for(response_event.wait(), timeout=timeout_seconds)
            return response_message

        except asyncio.TimeoutError:
            print(f"⏰ Request timeout for {request_type.value} to {receiver_id}")
            return None

        finally:
            # Restore original handler
            if original_handler:
                self.message_handlers[MessageType.RESPONSE] = original_handler
            else:
                self.message_handlers.pop(MessageType.RESPONSE, None)

    async def broadcast_message(
        self,
        agent_ids: List[str],
        message_type: MessageType,
        payload: Dict[str, Any],
        security_level: SecurityLevel = SecurityLevel.INTERNAL
    ) -> Dict[str, str]:
        """
        Broadcast message to multiple agents.

        Args:
            agent_ids: List of target agent IDs
            message_type: Message type
            payload: Message content
            security_level: Security level

        Returns:
            Dict mapping agent_id to message_id
        """
        conversation_id = str(uuid.uuid4())
        results = {}

        for agent_id in agent_ids:
            message_id = await self.send_message(
                receiver_id=agent_id,
                message_type=message_type,
                payload=payload,
                security_level=security_level,
                conversation_id=conversation_id
            )
            results[agent_id] = message_id

        return results

    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 100
    ) -> List[A2AMessage]:
        """Get message history for a conversation."""
        if self.audit_logger:
            return await self.audit_logger.get_conversation_history(
                conversation_id, limit
            )
        return []

    async def get_metrics(self) -> Dict[str, Any]:
        """Get communication metrics."""
        return {
            **self.metrics,
            "queue_size": len(self.message_queue),
            "retry_queue_size": len(self.retry_queue),
            "registered_handlers": len(self.message_handlers),
            "middleware_count": len(self.middleware),
            "trusted_agents": len(self.trusted_agents)
        }

    # Private methods

    async def _apply_message_security(self, message: A2AMessage):
        """Apply security measures to outbound message."""
        # Sign message
        message_hash = self._compute_message_hash(message)
        signature = self.private_key.sign(
            message_hash.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        message.signature = signature.hex()

        # Encrypt payload if required
        if message.security_level in [SecurityLevel.CONFIDENTIAL, SecurityLevel.RESTRICTED]:
            # Get receiver's public key
            receiver_public_key = await self._get_agent_public_key(message.receiver_id)
            if receiver_public_key:
                # Generate symmetric key for payload
                symmetric_key = self._generate_symmetric_key()

                # Encrypt payload with symmetric key
                encrypted_payload = self._encrypt_payload(
                    json.dumps(message.payload),
                    symmetric_key
                )

                # Encrypt symmetric key with receiver's public key
                encrypted_key = receiver_public_key.encrypt(
                    symmetric_key,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )

                # Update message
                message.encrypted_payload = encrypted_payload.hex()
                message.encryption_key_id = encrypted_key.hex()
                message.payload = {}  # Clear original payload

    async def _verify_message_security(self, message: A2AMessage) -> bool:
        """Verify security of inbound message."""
        try:
            # Get sender's public key
            sender_public_key = await self._get_agent_public_key(message.sender_id)
            if not sender_public_key:
                return False

            # Verify signature
            message_hash = self._compute_message_hash(message)
            sender_public_key.verify(
                bytes.fromhex(message.signature),
                message_hash.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )

            # Decrypt payload if encrypted
            if message.encrypted_payload and message.encryption_key_id:
                # Decrypt symmetric key
                symmetric_key = self.private_key.decrypt(
                    bytes.fromhex(message.encryption_key_id),
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )

                # Decrypt payload
                decrypted_payload = self._decrypt_payload(
                    bytes.fromhex(message.encrypted_payload),
                    symmetric_key
                )

                # Restore payload
                message.payload = json.loads(decrypted_payload)

            return True

        except Exception as e:
            print(f"❌ Security verification failed: {e}")
            return False

    def _compute_message_hash(self, message: A2AMessage) -> str:
        """Compute hash of message for signature."""
        # Create canonical representation
        canonical_data = {
            "message_id": message.message_id,
            "sender_id": message.sender_id,
            "receiver_id": message.receiver_id,
            "message_type": message.message_type.value,
            "created_at": message.created_at.isoformat(),
            "payload_hash": hashlib.sha256(
                json.dumps(message.payload, sort_keys=True).encode()
            ).hexdigest()
        }

        canonical_string = json.dumps(canonical_data, sort_keys=True)
        return hashlib.sha256(canonical_string.encode()).hexdigest()

    def _generate_symmetric_key(self) -> bytes:
        """Generate symmetric encryption key."""
        return os.urandom(32)  # 256-bit key

    def _encrypt_payload(self, payload: str, key: bytes) -> bytes:
        """Encrypt payload with symmetric key."""
        import os
        iv = os.urandom(16)  # 128-bit IV
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(payload.encode()) + encryptor.finalize()
        return iv + encryptor.tag + ciphertext

    def _decrypt_payload(self, encrypted_data: bytes, key: bytes) -> str:
        """Decrypt payload with symmetric key."""
        iv = encrypted_data[:16]
        tag = encrypted_data[16:32]
        ciphertext = encrypted_data[32:]

        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv, tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext.decode()

    async def _get_agent_public_key(self, agent_id: str) -> Optional[rsa.RSAPublicKey]:
        """Get public key for an agent."""
        if agent_id in self.trusted_agents:
            return self.trusted_agents[agent_id]

        # Query registry for public key
        if self.registry_url:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.registry_url}/agents/{agent_id}/public-key"
                    ) as response:
                        if response.status == 200:
                            key_data = await response.json()
                            public_key = serialization.load_pem_public_key(
                                key_data["public_key"].encode(),
                                backend=default_backend()
                            )
                            self.trusted_agents[agent_id] = public_key
                            return public_key
            except Exception as e:
                print(f"❌ Failed to get public key for {agent_id}: {e}")

        return None

    def _parse_raw_message(self, raw_message: Dict[str, Any]) -> A2AMessage:
        """Parse raw message data into A2AMessage."""
        return A2AMessage(
            message_id=raw_message["message_id"],
            correlation_id=raw_message.get("correlation_id"),
            conversation_id=raw_message.get("conversation_id"),
            sender_id=raw_message["sender_id"],
            receiver_id=raw_message["receiver_id"],
            message_type=MessageType(raw_message["message_type"]),
            payload=raw_message.get("payload", {}),
            metadata=raw_message.get("metadata", {}),
            security_level=SecurityLevel(raw_message["security_level"]),
            priority=MessagePriority(raw_message["priority"]),
            created_at=datetime.fromisoformat(raw_message["created_at"]),
            expires_at=datetime.fromisoformat(raw_message["expires_at"]) if raw_message.get("expires_at") else None,
            protocol_version=raw_message.get("protocol_version", "1.0"),
            signature=raw_message.get("signature"),
            encrypted_payload=raw_message.get("encrypted_payload"),
            encryption_key_id=raw_message.get("encryption_key_id")
        )

    async def _route_message(self, message: A2AMessage):
        """Route message to appropriate handler."""
        handler = self.message_handlers.get(message.message_type)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                print(f"❌ Handler error for {message.message_type.value}: {e}")
                # Send error response if this was a request
                if message.message_type in [MessageType.REQUEST, MessageType.CAPABILITY_REQUEST]:
                    await self.send_message(
                        receiver_id=message.sender_id,
                        message_type=MessageType.ERROR,
                        payload={"error": str(e), "original_message_id": message.message_id},
                        correlation_id=message.message_id
                    )
        else:
            print(f"⚠️ No handler for message type: {message.message_type.value}")

    async def _transmit_message(self, message: A2AMessage) -> bool:
        """Transmit message to receiver."""
        try:
            # Get receiver endpoint
            receiver_endpoint = await self._get_agent_endpoint(message.receiver_id)
            if not receiver_endpoint:
                return False

            # Prepare message for transmission
            message_data = {
                "message_id": message.message_id,
                "correlation_id": message.correlation_id,
                "conversation_id": message.conversation_id,
                "sender_id": message.sender_id,
                "receiver_id": message.receiver_id,
                "message_type": message.message_type.value,
                "payload": message.payload,
                "metadata": message.metadata,
                "security_level": message.security_level.value,
                "priority": message.priority.value,
                "created_at": message.created_at.isoformat(),
                "expires_at": message.expires_at.isoformat() if message.expires_at else None,
                "protocol_version": message.protocol_version,
                "signature": message.signature,
                "encrypted_payload": message.encrypted_payload,
                "encryption_key_id": message.encryption_key_id
            }

            # Send via HTTP
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{receiver_endpoint}/a2a/receive",
                    json=message_data,
                    timeout=30
                ) as response:
                    return response.status == 200

        except Exception as e:
            print(f"❌ Failed to transmit message {message.message_id}: {e}")
            return False

    async def _get_agent_endpoint(self, agent_id: str) -> Optional[str]:
        """Get endpoint URL for an agent."""
        if self.registry_url:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.registry_url}/agents/{agent_id}/endpoint"
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            return data["endpoint_url"]
            except Exception as e:
                print(f"❌ Failed to get endpoint for {agent_id}: {e}")

        return None

    async def _get_sender_capabilities(self) -> List[str]:
        """Get current agent's capabilities."""
        # This would be populated from the agent's capability registry
        return ["payment_processing", "ap2_compliance", "mandate_verification"]