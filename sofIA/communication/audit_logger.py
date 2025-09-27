"""
A2A Communication Audit Logger

Implements comprehensive audit logging for Agent-to-Agent communications
with distributed ledger integration for mandate verification.
"""

import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import hashlib
import sqlite3
import aiosqlite
from pathlib import Path

from .a2a_protocol import A2AMessage, MessageType


@dataclass
class AuditLogEntry:
    """Single audit log entry for A2A communication."""
    log_id: str
    timestamp: datetime
    agent_id: str
    event_type: str  # message_sent, message_received, error, security_violation
    message_id: str
    conversation_id: Optional[str]
    correlation_id: Optional[str]
    counterparty_id: str
    message_type: str
    security_level: str
    payload_hash: str
    metadata: Dict[str, Any]
    block_hash: Optional[str] = None  # For distributed ledger integration
    previous_hash: Optional[str] = None


class A2AAuditLogger:
    """
    Comprehensive audit logging system for A2A communications.

    Provides immutable audit trails with distributed ledger integration
    for commercial deployment and regulatory compliance.
    """

    def __init__(
        self,
        agent_id: str,
        database_path: str = "sofia_audit.db",
        blockchain_enabled: bool = False
    ):
        self.agent_id = agent_id
        self.database_path = database_path
        self.blockchain_enabled = blockchain_enabled

        # Audit chain for immutability
        self.audit_chain: List[AuditLogEntry] = []
        self.last_block_hash: Optional[str] = None

        # Initialize database
        asyncio.create_task(self._initialize_database())

    async def log_message_sent(self, message: A2AMessage):
        """Log outbound message."""
        await self._create_audit_entry(
            event_type="message_sent",
            message=message,
            counterparty_id=message.receiver_id
        )

    async def log_message_received(self, message: A2AMessage):
        """Log inbound message."""
        await self._create_audit_entry(
            event_type="message_received",
            message=message,
            counterparty_id=message.sender_id
        )

    async def log_security_violation(
        self,
        message_id: str,
        violation_type: str,
        details: Dict[str, Any]
    ):
        """Log security violation."""
        entry = AuditLogEntry(
            log_id=f"audit_{int(datetime.now().timestamp() * 1000)}",
            timestamp=datetime.now(timezone.utc),
            agent_id=self.agent_id,
            event_type="security_violation",
            message_id=message_id,
            conversation_id=None,
            correlation_id=None,
            counterparty_id="unknown",
            message_type="security_event",
            security_level="critical",
            payload_hash="",
            metadata={
                "violation_type": violation_type,
                "details": details
            }
        )

        await self._add_to_audit_chain(entry)

    async def log_error(
        self,
        message_id: str,
        error_type: str,
        error_details: Dict[str, Any]
    ):
        """Log communication error."""
        entry = AuditLogEntry(
            log_id=f"audit_{int(datetime.now().timestamp() * 1000)}",
            timestamp=datetime.now(timezone.utc),
            agent_id=self.agent_id,
            event_type="error",
            message_id=message_id,
            conversation_id=None,
            correlation_id=None,
            counterparty_id="unknown",
            message_type="error_event",
            security_level="normal",
            payload_hash="",
            metadata={
                "error_type": error_type,
                "error_details": error_details
            }
        )

        await self._add_to_audit_chain(entry)

    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 100
    ) -> List[AuditLogEntry]:
        """Get audit history for a conversation."""
        async with aiosqlite.connect(self.database_path) as db:
            cursor = await db.execute(
                """
                SELECT * FROM audit_logs
                WHERE conversation_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (conversation_id, limit)
            )
            rows = await cursor.fetchall()

            return [self._row_to_audit_entry(row) for row in rows]

    async def get_agent_audit_trail(
        self,
        counterparty_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[AuditLogEntry]:
        """Get audit trail for specific agent interactions."""
        query = """
            SELECT * FROM audit_logs
            WHERE counterparty_id = ?
        """
        params = [counterparty_id]

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        async with aiosqlite.connect(self.database_path) as db:
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()

            return [self._row_to_audit_entry(row) for row in rows]

    async def verify_audit_chain_integrity(self) -> Dict[str, Any]:
        """Verify integrity of the audit chain."""
        async with aiosqlite.connect(self.database_path) as db:
            cursor = await db.execute(
                "SELECT * FROM audit_logs ORDER BY timestamp ASC"
            )
            rows = await cursor.fetchall()

        if not rows:
            return {"valid": True, "total_entries": 0}

        # Verify hash chain
        previous_hash = None
        corrupted_entries = []

        for i, row in enumerate(rows):
            entry = self._row_to_audit_entry(row)

            # Verify hash chain
            if i == 0:
                # First entry should have no previous hash
                if entry.previous_hash is not None:
                    corrupted_entries.append(entry.log_id)
            else:
                # Subsequent entries should link to previous
                if entry.previous_hash != previous_hash:
                    corrupted_entries.append(entry.log_id)

            # Verify block hash
            expected_hash = self._compute_block_hash(entry)
            if entry.block_hash != expected_hash:
                corrupted_entries.append(entry.log_id)

            previous_hash = entry.block_hash

        return {
            "valid": len(corrupted_entries) == 0,
            "total_entries": len(rows),
            "corrupted_entries": corrupted_entries,
            "last_verified_hash": previous_hash
        }

    async def export_audit_report(
        self,
        start_date: datetime,
        end_date: datetime,
        format: str = "json"
    ) -> str:
        """Export audit report for compliance."""
        query = """
            SELECT * FROM audit_logs
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp ASC
        """

        async with aiosqlite.connect(self.database_path) as db:
            cursor = await db.execute(
                query,
                (start_date.isoformat(), end_date.isoformat())
            )
            rows = await cursor.fetchall()

        entries = [self._row_to_audit_entry(row) for row in rows]

        if format == "json":
            return json.dumps({
                "report_generated": datetime.now(timezone.utc).isoformat(),
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "agent_id": self.agent_id,
                "total_entries": len(entries),
                "entries": [asdict(entry) for entry in entries]
            }, indent=2, default=str)

        elif format == "csv":
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Header
            writer.writerow([
                "log_id", "timestamp", "agent_id", "event_type",
                "message_id", "conversation_id", "counterparty_id",
                "message_type", "security_level", "payload_hash",
                "block_hash"
            ])

            # Data
            for entry in entries:
                writer.writerow([
                    entry.log_id, entry.timestamp.isoformat(),
                    entry.agent_id, entry.event_type,
                    entry.message_id, entry.conversation_id,
                    entry.counterparty_id, entry.message_type,
                    entry.security_level, entry.payload_hash,
                    entry.block_hash
                ])

            return output.getvalue()

        else:
            raise ValueError(f"Unsupported format: {format}")

    async def get_audit_statistics(
        self,
        time_period_days: int = 30
    ) -> Dict[str, Any]:
        """Get audit statistics for monitoring."""
        start_date = datetime.now(timezone.utc) - timedelta(days=time_period_days)

        async with aiosqlite.connect(self.database_path) as db:
            # Total entries
            cursor = await db.execute(
                "SELECT COUNT(*) FROM audit_logs WHERE timestamp >= ?",
                (start_date.isoformat(),)
            )
            total_entries = (await cursor.fetchone())[0]

            # By event type
            cursor = await db.execute(
                """
                SELECT event_type, COUNT(*)
                FROM audit_logs
                WHERE timestamp >= ?
                GROUP BY event_type
                """,
                (start_date.isoformat(),)
            )
            by_event_type = dict(await cursor.fetchall())

            # By message type
            cursor = await db.execute(
                """
                SELECT message_type, COUNT(*)
                FROM audit_logs
                WHERE timestamp >= ?
                GROUP BY message_type
                """,
                (start_date.isoformat(),)
            )
            by_message_type = dict(await cursor.fetchall())

            # Security violations
            cursor = await db.execute(
                """
                SELECT COUNT(*)
                FROM audit_logs
                WHERE timestamp >= ? AND event_type = 'security_violation'
                """,
                (start_date.isoformat(),)
            )
            security_violations = (await cursor.fetchone())[0]

            # Unique counterparties
            cursor = await db.execute(
                """
                SELECT COUNT(DISTINCT counterparty_id)
                FROM audit_logs
                WHERE timestamp >= ?
                """,
                (start_date.isoformat(),)
            )
            unique_counterparties = (await cursor.fetchone())[0]

        return {
            "period_days": time_period_days,
            "total_entries": total_entries,
            "by_event_type": by_event_type,
            "by_message_type": by_message_type,
            "security_violations": security_violations,
            "unique_counterparties": unique_counterparties,
            "audit_chain_length": len(self.audit_chain)
        }

    # Private methods

    async def _initialize_database(self):
        """Initialize SQLite database for audit logs."""
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    log_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    message_id TEXT NOT NULL,
                    conversation_id TEXT,
                    correlation_id TEXT,
                    counterparty_id TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    security_level TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    block_hash TEXT,
                    previous_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON audit_logs(timestamp)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversation
                ON audit_logs(conversation_id)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_counterparty
                ON audit_logs(counterparty_id)
            """)

            await db.commit()

    async def _create_audit_entry(
        self,
        event_type: str,
        message: A2AMessage,
        counterparty_id: str
    ):
        """Create audit entry for a message."""
        payload_hash = hashlib.sha256(
            json.dumps(message.payload, sort_keys=True).encode()
        ).hexdigest()

        entry = AuditLogEntry(
            log_id=f"audit_{int(datetime.now().timestamp() * 1000)}",
            timestamp=datetime.now(timezone.utc),
            agent_id=self.agent_id,
            event_type=event_type,
            message_id=message.message_id,
            conversation_id=message.conversation_id,
            correlation_id=message.correlation_id,
            counterparty_id=counterparty_id,
            message_type=message.message_type.value,
            security_level=message.security_level.value,
            payload_hash=payload_hash,
            metadata={
                "priority": message.priority.value,
                "protocol_version": message.protocol_version,
                "encrypted": bool(message.encrypted_payload),
                "expires_at": message.expires_at.isoformat() if message.expires_at else None
            }
        )

        await self._add_to_audit_chain(entry)

    async def _add_to_audit_chain(self, entry: AuditLogEntry):
        """Add entry to audit chain with blockchain-style hashing."""
        # Set previous hash
        entry.previous_hash = self.last_block_hash

        # Compute block hash
        entry.block_hash = self._compute_block_hash(entry)

        # Update chain
        self.audit_chain.append(entry)
        self.last_block_hash = entry.block_hash

        # Store in database
        await self._store_audit_entry(entry)

        # If blockchain is enabled, add to distributed ledger
        if self.blockchain_enabled:
            await self._add_to_blockchain(entry)

    def _compute_block_hash(self, entry: AuditLogEntry) -> str:
        """Compute hash for audit entry (blockchain-style)."""
        block_data = {
            "log_id": entry.log_id,
            "timestamp": entry.timestamp.isoformat(),
            "agent_id": entry.agent_id,
            "event_type": entry.event_type,
            "message_id": entry.message_id,
            "counterparty_id": entry.counterparty_id,
            "payload_hash": entry.payload_hash,
            "previous_hash": entry.previous_hash
        }

        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    async def _store_audit_entry(self, entry: AuditLogEntry):
        """Store audit entry in database."""
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                INSERT INTO audit_logs (
                    log_id, timestamp, agent_id, event_type,
                    message_id, conversation_id, correlation_id,
                    counterparty_id, message_type, security_level,
                    payload_hash, metadata, block_hash, previous_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.log_id,
                entry.timestamp.isoformat(),
                entry.agent_id,
                entry.event_type,
                entry.message_id,
                entry.conversation_id,
                entry.correlation_id,
                entry.counterparty_id,
                entry.message_type,
                entry.security_level,
                entry.payload_hash,
                json.dumps(entry.metadata),
                entry.block_hash,
                entry.previous_hash
            ))
            await db.commit()

    def _row_to_audit_entry(self, row) -> AuditLogEntry:
        """Convert database row to AuditLogEntry."""
        return AuditLogEntry(
            log_id=row[0],
            timestamp=datetime.fromisoformat(row[1]),
            agent_id=row[2],
            event_type=row[3],
            message_id=row[4],
            conversation_id=row[5],
            correlation_id=row[6],
            counterparty_id=row[7],
            message_type=row[8],
            security_level=row[9],
            payload_hash=row[10],
            metadata=json.loads(row[11]),
            block_hash=row[12],
            previous_hash=row[13]
        )

    async def _add_to_blockchain(self, entry: AuditLogEntry):
        """Add entry to distributed blockchain (implementation placeholder)."""
        # This would integrate with a distributed ledger system
        # For now, just log that it would be added
        print(f"🔗 Would add to blockchain: {entry.log_id} -> {entry.block_hash[:16]}...")