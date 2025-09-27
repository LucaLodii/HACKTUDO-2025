"""
Comprehensive Dispute Resolution System

Implements automated dispute resolution with escalation to human arbitration,
full audit trails, and integration with the AP2 mandate verification system.
"""

import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import aiosqlite
from pathlib import Path

from ..ledger.mandate_ledger import MandateLedger, MandateType, RecordStatus
from ..communication.a2a_protocol import A2AProtocol, MessageType, SecurityLevel


class DisputeType(Enum):
    """Types of disputes in the payment system."""
    UNAUTHORIZED_TRANSACTION = "unauthorized_transaction"
    GOODS_NOT_RECEIVED = "goods_not_received"
    GOODS_NOT_AS_DESCRIBED = "goods_not_as_described"
    MERCHANT_NON_DELIVERY = "merchant_non_delivery"
    PAYMENT_PROCESSING_ERROR = "payment_processing_error"
    MANDATE_VERIFICATION_FAILURE = "mandate_verification_failure"
    AGENT_MALFUNCTION = "agent_malfunction"
    FRAUD_DETECTION = "fraud_detection"
    REFUND_REQUEST = "refund_request"
    CHARGEBACK = "chargeback"


class DisputeStatus(Enum):
    """Status of dispute cases."""
    FILED = "filed"
    UNDER_REVIEW = "under_review"
    INVESTIGATING = "investigating"
    AWAITING_EVIDENCE = "awaiting_evidence"
    AUTOMATED_RESOLUTION = "automated_resolution"
    ESCALATED = "escalated"
    ARBITRATION = "arbitration"
    RESOLVED = "resolved"
    CLOSED = "closed"
    APPEALED = "appealed"


class DisputePriority(Enum):
    """Priority levels for dispute resolution."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


@dataclass
class DisputeEvidence:
    """Evidence submitted for a dispute case."""
    evidence_id: str
    evidence_type: str  # mandate, transaction_log, communication, document
    submitted_by: str  # DID of submitter
    content: Dict[str, Any]
    timestamp: datetime
    verified: bool = False


@dataclass
class DisputeCase:
    """Complete dispute case with all related information."""
    case_id: str
    dispute_type: DisputeType
    status: DisputeStatus
    priority: DisputePriority

    # Parties involved
    complainant_did: str
    respondent_did: str
    agent_did: Optional[str]

    # Transaction details
    mandate_id: str
    transaction_amount: Optional[float]
    currency: Optional[str]

    # Case details
    filed_at: datetime
    last_updated: datetime
    resolution_deadline: Optional[datetime]

    # Evidence and communications
    evidence: List[DisputeEvidence]
    case_notes: List[Dict[str, Any]]
    resolution_attempts: List[Dict[str, Any]]

    # Resolution
    resolution: Optional[Dict[str, Any]]
    resolution_amount: Optional[float]
    resolved_at: Optional[datetime]
    resolved_by: Optional[str]

    # Metadata
    metadata: Dict[str, Any]


class DisputeManager:
    """
    Comprehensive Dispute Resolution Manager

    Handles dispute lifecycle from filing to resolution with automated
    processing, escalation rules, and integration with mandate verification.
    """

    def __init__(
        self,
        node_id: str,
        mandate_ledger: MandateLedger,
        a2a_protocol: A2AProtocol,
        database_path: str = "disputes.db"
    ):
        self.node_id = node_id
        self.mandate_ledger = mandate_ledger
        self.a2a_protocol = a2a_protocol
        self.database_path = database_path

        # Active disputes
        self.active_disputes: Dict[str, DisputeCase] = {}

        # Resolution configuration
        self.auto_resolution_rules: List[Dict[str, Any]] = []
        self.escalation_rules: List[Dict[str, Any]] = []

        # Statistics
        self.resolution_stats = {
            "total_filed": 0,
            "auto_resolved": 0,
            "escalated": 0,
            "avg_resolution_time": 0.0
        }

        # Initialize
        asyncio.create_task(self._initialize_dispute_system())

    async def file_dispute(
        self,
        dispute_type: DisputeType,
        complainant_did: str,
        respondent_did: str,
        mandate_id: str,
        description: str,
        evidence: Optional[List[Dict[str, Any]]] = None,
        priority: DisputePriority = DisputePriority.NORMAL
    ) -> str:
        """
        File a new dispute case.

        Args:
            dispute_type: Type of dispute
            complainant_did: DID of the party filing the dispute
            respondent_did: DID of the party being disputed against
            mandate_id: Related mandate ID
            description: Description of the dispute
            evidence: Initial evidence (optional)
            priority: Case priority

        Returns:
            case_id: Unique identifier for the dispute case
        """
        case_id = f"dispute_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"

        # Verify mandate exists
        mandate_verification = await self.mandate_ledger.verify_mandate(mandate_id)
        if not mandate_verification["verified"]:
            raise ValueError(f"Cannot file dispute for unverified mandate: {mandate_id}")

        # Get transaction details from mandate
        mandate_history = await self.mandate_ledger.get_mandate_history(mandate_id)
        transaction_amount = None
        currency = None
        agent_did = None

        for record in mandate_history:
            if record.get("mandate_type") == "payment_mandate":
                # Extract from mandate data (would be in actual implementation)
                transaction_amount = 100.0  # Placeholder
                currency = "BRL"
                agent_did = record.get("agent_did")
                break

        # Create dispute case
        dispute_case = DisputeCase(
            case_id=case_id,
            dispute_type=dispute_type,
            status=DisputeStatus.FILED,
            priority=priority,
            complainant_did=complainant_did,
            respondent_did=respondent_did,
            agent_did=agent_did,
            mandate_id=mandate_id,
            transaction_amount=transaction_amount,
            currency=currency,
            filed_at=datetime.now(timezone.utc),
            last_updated=datetime.now(timezone.utc),
            resolution_deadline=self._calculate_resolution_deadline(priority),
            evidence=[],
            case_notes=[{
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "case_filed",
                "content": description,
                "author": complainant_did
            }],
            resolution_attempts=[],
            resolution=None,
            resolution_amount=None,
            resolved_at=None,
            resolved_by=None,
            metadata={
                "filing_source": "direct",
                "mandate_verification": mandate_verification
            }
        )

        # Add initial evidence
        if evidence:
            for ev in evidence:
                await self._add_evidence(dispute_case, ev, complainant_did)

        # Store dispute
        self.active_disputes[case_id] = dispute_case
        await self._save_dispute(dispute_case)

        # Update statistics
        self.resolution_stats["total_filed"] += 1

        # Notify parties
        await self._notify_dispute_filed(dispute_case)

        # Attempt automated resolution
        await self._attempt_auto_resolution(dispute_case)

        print(f"📋 Filed dispute case: {case_id} ({dispute_type.value})")
        return case_id

    async def submit_evidence(
        self,
        case_id: str,
        submitter_did: str,
        evidence_type: str,
        evidence_content: Dict[str, Any]
    ) -> bool:
        """
        Submit evidence for a dispute case.

        Args:
            case_id: Dispute case ID
            submitter_did: DID of evidence submitter
            evidence_type: Type of evidence
            evidence_content: Evidence content

        Returns:
            Success status
        """
        if case_id not in self.active_disputes:
            return False

        dispute_case = self.active_disputes[case_id]

        # Verify submitter is authorized
        if submitter_did not in [dispute_case.complainant_did, dispute_case.respondent_did]:
            if dispute_case.agent_did and submitter_did != dispute_case.agent_did:
                return False

        # Create evidence record
        evidence = {
            "evidence_type": evidence_type,
            "content": evidence_content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "submitter": submitter_did
        }

        await self._add_evidence(dispute_case, evidence, submitter_did)

        # Update case status if needed
        if dispute_case.status == DisputeStatus.AWAITING_EVIDENCE:
            dispute_case.status = DisputeStatus.UNDER_REVIEW

        dispute_case.last_updated = datetime.now(timezone.utc)
        await self._save_dispute(dispute_case)

        # Notify other parties
        await self._notify_evidence_submitted(dispute_case, submitter_did)

        # Re-attempt automated resolution with new evidence
        await self._attempt_auto_resolution(dispute_case)

        print(f"📎 Evidence submitted for case {case_id} by {submitter_did}")
        return True

    async def respond_to_dispute(
        self,
        case_id: str,
        respondent_did: str,
        response: str,
        evidence: Optional[List[Dict[str, Any]]] = None,
        proposed_resolution: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Allow respondent to respond to a dispute.

        Args:
            case_id: Dispute case ID
            respondent_did: DID of respondent
            response: Written response
            evidence: Supporting evidence (optional)
            proposed_resolution: Proposed resolution (optional)

        Returns:
            Success status
        """
        if case_id not in self.active_disputes:
            return False

        dispute_case = self.active_disputes[case_id]

        # Verify respondent
        if respondent_did != dispute_case.respondent_did:
            return False

        # Add response note
        dispute_case.case_notes.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "respondent_response",
            "content": response,
            "author": respondent_did
        })

        # Add evidence if provided
        if evidence:
            for ev in evidence:
                await self._add_evidence(dispute_case, ev, respondent_did)

        # Record proposed resolution
        if proposed_resolution:
            dispute_case.resolution_attempts.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "proposed_by": respondent_did,
                "proposal": proposed_resolution,
                "status": "pending_review"
            })

        dispute_case.status = DisputeStatus.UNDER_REVIEW
        dispute_case.last_updated = datetime.now(timezone.utc)
        await self._save_dispute(dispute_case)

        # Notify complainant
        await self._notify_dispute_response(dispute_case)

        # Attempt automated resolution with response
        await self._attempt_auto_resolution(dispute_case)

        print(f"💬 Response submitted for case {case_id}")
        return True

    async def escalate_dispute(
        self,
        case_id: str,
        escalation_reason: str,
        escalated_by: str
    ) -> bool:
        """
        Escalate a dispute to human arbitration.

        Args:
            case_id: Dispute case ID
            escalation_reason: Reason for escalation
            escalated_by: DID of party requesting escalation

        Returns:
            Success status
        """
        if case_id not in self.active_disputes:
            return False

        dispute_case = self.active_disputes[case_id]

        # Update status
        dispute_case.status = DisputeStatus.ESCALATED
        dispute_case.last_updated = datetime.now(timezone.utc)

        # Add escalation note
        dispute_case.case_notes.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "escalation",
            "content": escalation_reason,
            "author": escalated_by
        })

        await self._save_dispute(dispute_case)

        # Update statistics
        self.resolution_stats["escalated"] += 1

        # Notify arbitration service
        await self._notify_arbitration_required(dispute_case)

        print(f"⬆️ Escalated case {case_id} to arbitration")
        return True

    async def resolve_dispute(
        self,
        case_id: str,
        resolution: Dict[str, Any],
        resolved_by: str,
        resolution_amount: Optional[float] = None
    ) -> bool:
        """
        Resolve a dispute case.

        Args:
            case_id: Dispute case ID
            resolution: Resolution details
            resolved_by: DID of resolver (arbitrator or system)
            resolution_amount: Amount to be transferred (if applicable)

        Returns:
            Success status
        """
        if case_id not in self.active_disputes:
            return False

        dispute_case = self.active_disputes[case_id]

        # Update case
        dispute_case.status = DisputeStatus.RESOLVED
        dispute_case.resolution = resolution
        dispute_case.resolution_amount = resolution_amount
        dispute_case.resolved_at = datetime.now(timezone.utc)
        dispute_case.resolved_by = resolved_by
        dispute_case.last_updated = datetime.now(timezone.utc)

        # Add resolution note
        dispute_case.case_notes.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "resolution",
            "content": resolution.get("description", "Case resolved"),
            "author": resolved_by
        })

        await self._save_dispute(dispute_case)

        # Execute resolution if it involves transfers
        if resolution_amount and resolution.get("action") == "refund":
            await self._execute_refund(dispute_case)

        # Create mandate record for resolution
        await self._record_resolution_mandate(dispute_case)

        # Notify all parties
        await self._notify_dispute_resolved(dispute_case)

        # Move to resolved cases
        del self.active_disputes[case_id]

        # Update statistics
        resolution_time = (dispute_case.resolved_at - dispute_case.filed_at).total_seconds() / 3600
        self._update_resolution_stats(resolution_time)

        print(f"✅ Resolved case {case_id}: {resolution.get('summary', 'N/A')}")
        return True

    async def get_dispute_status(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a dispute case."""
        if case_id in self.active_disputes:
            dispute_case = self.active_disputes[case_id]
        else:
            # Check database for resolved cases
            dispute_case = await self._load_dispute(case_id)

        if not dispute_case:
            return None

        return {
            "case_id": case_id,
            "status": dispute_case.status.value,
            "dispute_type": dispute_case.dispute_type.value,
            "filed_at": dispute_case.filed_at.isoformat(),
            "last_updated": dispute_case.last_updated.isoformat(),
            "resolution_deadline": dispute_case.resolution_deadline.isoformat() if dispute_case.resolution_deadline else None,
            "evidence_count": len(dispute_case.evidence),
            "resolution": dispute_case.resolution,
            "resolved_at": dispute_case.resolved_at.isoformat() if dispute_case.resolved_at else None
        }

    async def get_user_disputes(
        self,
        user_did: str,
        status_filter: Optional[DisputeStatus] = None
    ) -> List[Dict[str, Any]]:
        """Get all disputes involving a specific user."""
        user_disputes = []

        # Check active disputes
        for dispute_case in self.active_disputes.values():
            if user_did in [dispute_case.complainant_did, dispute_case.respondent_did]:
                if not status_filter or dispute_case.status == status_filter:
                    user_disputes.append({
                        "case_id": dispute_case.case_id,
                        "dispute_type": dispute_case.dispute_type.value,
                        "status": dispute_case.status.value,
                        "role": "complainant" if user_did == dispute_case.complainant_did else "respondent",
                        "filed_at": dispute_case.filed_at.isoformat(),
                        "mandate_id": dispute_case.mandate_id,
                        "amount": dispute_case.transaction_amount
                    })

        # TODO: Also check resolved disputes in database

        return user_disputes

    async def get_dispute_statistics(self) -> Dict[str, Any]:
        """Get comprehensive dispute resolution statistics."""
        active_count = len(self.active_disputes)
        by_status = {}
        by_type = {}

        for dispute_case in self.active_disputes.values():
            status = dispute_case.status.value
            dispute_type = dispute_case.dispute_type.value

            by_status[status] = by_status.get(status, 0) + 1
            by_type[dispute_type] = by_type.get(dispute_type, 0) + 1

        return {
            "active_disputes": active_count,
            "by_status": by_status,
            "by_type": by_type,
            "resolution_stats": self.resolution_stats,
            "auto_resolution_rules": len(self.auto_resolution_rules),
            "escalation_rules": len(self.escalation_rules)
        }

    # Private methods

    async def _initialize_dispute_system(self):
        """Initialize the dispute resolution system."""
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS disputes (
                    case_id TEXT PRIMARY KEY,
                    dispute_data TEXT NOT NULL,
                    status TEXT NOT NULL,
                    filed_at TEXT NOT NULL,
                    resolved_at TEXT,
                    last_updated TEXT NOT NULL
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS dispute_evidence (
                    evidence_id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    evidence_data TEXT NOT NULL,
                    submitted_at TEXT NOT NULL,
                    FOREIGN KEY (case_id) REFERENCES disputes (case_id)
                )
            """)

            await db.commit()

        # Load auto-resolution rules
        self._load_auto_resolution_rules()

        print("🔧 Initialized dispute resolution system")

    def _load_auto_resolution_rules(self):
        """Load automated resolution rules."""
        self.auto_resolution_rules = [
            {
                "rule_id": "small_amount_refund",
                "condition": {
                    "dispute_type": ["goods_not_received", "goods_not_as_described"],
                    "amount_threshold": 50.0,
                    "evidence_required": False
                },
                "action": {
                    "type": "auto_refund",
                    "percentage": 100
                },
                "confidence": 0.8
            },
            {
                "rule_id": "fraud_detection_reversal",
                "condition": {
                    "dispute_type": ["fraud_detection"],
                    "fraud_score": 0.9,
                    "time_since_transaction": 24  # hours
                },
                "action": {
                    "type": "auto_reversal",
                    "percentage": 100
                },
                "confidence": 0.95
            },
            {
                "rule_id": "processing_error_correction",
                "condition": {
                    "dispute_type": ["payment_processing_error"],
                    "error_confirmed": True
                },
                "action": {
                    "type": "auto_correction",
                    "retry_payment": True
                },
                "confidence": 0.9
            }
        ]

    def _calculate_resolution_deadline(self, priority: DisputePriority) -> datetime:
        """Calculate resolution deadline based on priority."""
        hours_map = {
            DisputePriority.CRITICAL: 2,
            DisputePriority.URGENT: 12,
            DisputePriority.HIGH: 24,
            DisputePriority.NORMAL: 72,
            DisputePriority.LOW: 168  # 1 week
        }

        hours = hours_map.get(priority, 72)
        return datetime.now(timezone.utc) + timedelta(hours=hours)

    async def _add_evidence(
        self,
        dispute_case: DisputeCase,
        evidence_data: Dict[str, Any],
        submitter_did: str
    ):
        """Add evidence to a dispute case."""
        evidence = DisputeEvidence(
            evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
            evidence_type=evidence_data["evidence_type"],
            submitted_by=submitter_did,
            content=evidence_data["content"],
            timestamp=datetime.now(timezone.utc),
            verified=False
        )

        dispute_case.evidence.append(evidence)

        # Auto-verify certain types of evidence
        if evidence.evidence_type in ["mandate_verification", "ledger_record"]:
            evidence.verified = True

    async def _attempt_auto_resolution(self, dispute_case: DisputeCase):
        """Attempt automated resolution of a dispute."""
        if dispute_case.status not in [DisputeStatus.FILED, DisputeStatus.UNDER_REVIEW]:
            return

        # Evaluate auto-resolution rules
        for rule in self.auto_resolution_rules:
            if await self._evaluate_resolution_rule(dispute_case, rule):
                await self._apply_auto_resolution(dispute_case, rule)
                return

    async def _evaluate_resolution_rule(
        self,
        dispute_case: DisputeCase,
        rule: Dict[str, Any]
    ) -> bool:
        """Evaluate if a resolution rule applies to a dispute."""
        condition = rule["condition"]

        # Check dispute type
        if "dispute_type" in condition:
            if dispute_case.dispute_type.value not in condition["dispute_type"]:
                return False

        # Check amount threshold
        if "amount_threshold" in condition and dispute_case.transaction_amount:
            if dispute_case.transaction_amount > condition["amount_threshold"]:
                return False

        # Check evidence requirements
        if condition.get("evidence_required", True) and not dispute_case.evidence:
            return False

        # Check time constraints
        if "time_since_transaction" in condition:
            # This would check against actual transaction time
            pass

        return True

    async def _apply_auto_resolution(
        self,
        dispute_case: DisputeCase,
        rule: Dict[str, Any]
    ):
        """Apply automated resolution based on rule."""
        action = rule["action"]

        resolution = {
            "type": "automated",
            "rule_applied": rule["rule_id"],
            "confidence": rule["confidence"],
            "action": action["type"],
            "description": f"Automatically resolved using rule: {rule['rule_id']}"
        }

        # Calculate resolution amount
        resolution_amount = None
        if action["type"] in ["auto_refund", "auto_reversal"] and dispute_case.transaction_amount:
            percentage = action.get("percentage", 100)
            resolution_amount = (dispute_case.transaction_amount * percentage) / 100

        # Apply resolution
        await self.resolve_dispute(
            dispute_case.case_id,
            resolution,
            "automated_system",
            resolution_amount
        )

        # Update statistics
        self.resolution_stats["auto_resolved"] += 1

    async def _execute_refund(self, dispute_case: DisputeCase):
        """Execute refund as part of dispute resolution."""
        # This would integrate with the payment system to process refunds
        print(f"💰 Processing refund: {dispute_case.resolution_amount} {dispute_case.currency}")

    async def _record_resolution_mandate(self, dispute_case: DisputeCase):
        """Record dispute resolution as a mandate in the ledger."""
        if not dispute_case.resolution:
            return

        resolution_mandate_data = {
            "dispute_case_id": dispute_case.case_id,
            "original_mandate_id": dispute_case.mandate_id,
            "resolution_type": dispute_case.resolution.get("type"),
            "resolution_amount": dispute_case.resolution_amount,
            "resolved_by": dispute_case.resolved_by,
            "resolution_timestamp": dispute_case.resolved_at.isoformat()
        }

        await self.mandate_ledger.add_mandate_record(
            mandate_type=MandateType.DISPUTE_MANDATE,
            mandate_id=f"dispute_resolution_{dispute_case.case_id}",
            user_did=dispute_case.complainant_did,
            merchant_did=dispute_case.respondent_did,
            agent_did=dispute_case.resolved_by or "dispute_system",
            ap2_mandate_data=resolution_mandate_data,
            cryptographic_proof="dispute_resolution_proof",
            metadata={"dispute_resolution": True}
        )

    async def _notify_dispute_filed(self, dispute_case: DisputeCase):
        """Notify parties that a dispute has been filed."""
        notification = {
            "case_id": dispute_case.case_id,
            "dispute_type": dispute_case.dispute_type.value,
            "mandate_id": dispute_case.mandate_id,
            "filed_by": dispute_case.complainant_did,
            "resolution_deadline": dispute_case.resolution_deadline.isoformat()
        }

        # Notify respondent
        await self.a2a_protocol.send_message(
            receiver_id=dispute_case.respondent_did,
            message_type=MessageType.NOTIFICATION,
            payload={
                "type": "dispute_filed",
                "dispute_case": notification
            },
            security_level=SecurityLevel.CONFIDENTIAL
        )

    async def _notify_evidence_submitted(self, dispute_case: DisputeCase, submitter_did: str):
        """Notify parties when evidence is submitted."""
        parties = [dispute_case.complainant_did, dispute_case.respondent_did]
        if dispute_case.agent_did:
            parties.append(dispute_case.agent_did)

        for party in parties:
            if party != submitter_did:
                await self.a2a_protocol.send_message(
                    receiver_id=party,
                    message_type=MessageType.NOTIFICATION,
                    payload={
                        "type": "evidence_submitted",
                        "case_id": dispute_case.case_id,
                        "submitted_by": submitter_did
                    },
                    security_level=SecurityLevel.INTERNAL
                )

    async def _notify_dispute_response(self, dispute_case: DisputeCase):
        """Notify complainant of respondent's response."""
        await self.a2a_protocol.send_message(
            receiver_id=dispute_case.complainant_did,
            message_type=MessageType.NOTIFICATION,
            payload={
                "type": "dispute_response",
                "case_id": dispute_case.case_id,
                "respondent": dispute_case.respondent_did
            },
            security_level=SecurityLevel.CONFIDENTIAL
        )

    async def _notify_arbitration_required(self, dispute_case: DisputeCase):
        """Notify arbitration service of escalated dispute."""
        # This would integrate with external arbitration service
        print(f"🏛️ Notifying arbitration service for case {dispute_case.case_id}")

    async def _notify_dispute_resolved(self, dispute_case: DisputeCase):
        """Notify all parties of dispute resolution."""
        parties = [dispute_case.complainant_did, dispute_case.respondent_did]
        if dispute_case.agent_did:
            parties.append(dispute_case.agent_did)

        for party in parties:
            await self.a2a_protocol.send_message(
                receiver_id=party,
                message_type=MessageType.NOTIFICATION,
                payload={
                    "type": "dispute_resolved",
                    "case_id": dispute_case.case_id,
                    "resolution": dispute_case.resolution,
                    "resolution_amount": dispute_case.resolution_amount
                },
                security_level=SecurityLevel.CONFIDENTIAL
            )

    async def _save_dispute(self, dispute_case: DisputeCase):
        """Save dispute case to database."""
        dispute_data = json.dumps(asdict(dispute_case), default=str)

        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO disputes
                (case_id, dispute_data, status, filed_at, resolved_at, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                dispute_case.case_id,
                dispute_data,
                dispute_case.status.value,
                dispute_case.filed_at.isoformat(),
                dispute_case.resolved_at.isoformat() if dispute_case.resolved_at else None,
                dispute_case.last_updated.isoformat()
            ))
            await db.commit()

    async def _load_dispute(self, case_id: str) -> Optional[DisputeCase]:
        """Load dispute case from database."""
        async with aiosqlite.connect(self.database_path) as db:
            cursor = await db.execute(
                "SELECT dispute_data FROM disputes WHERE case_id = ?",
                (case_id,)
            )
            row = await cursor.fetchone()

            if row:
                dispute_data = json.loads(row[0])
                # Reconstruct DisputeCase object
                # This would need proper deserialization logic
                return None  # Placeholder

        return None

    def _update_resolution_stats(self, resolution_time_hours: float):
        """Update resolution statistics."""
        total_resolved = self.resolution_stats["auto_resolved"] + 1  # +1 for this resolution
        current_avg = self.resolution_stats["avg_resolution_time"]

        # Update running average
        new_avg = ((current_avg * (total_resolved - 1)) + resolution_time_hours) / total_resolved
        self.resolution_stats["avg_resolution_time"] = new_avg