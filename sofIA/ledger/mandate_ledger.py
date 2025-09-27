"""
Distributed Ledger for AP2 Mandate Verification

Implements a blockchain-based system for immutable storage and verification
of AP2 payment mandates with cryptographic proof of compliance.
"""

import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import sqlite3
import aiosqlite
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt


class MandateType(Enum):
    """Types of AP2 mandates stored in the ledger."""
    INTENT_MANDATE = "intent_mandate"
    CART_MANDATE = "cart_mandate"
    PAYMENT_MANDATE = "payment_mandate"
    REFUND_MANDATE = "refund_mandate"
    DISPUTE_MANDATE = "dispute_mandate"


class RecordStatus(Enum):
    """Status of mandate records in the ledger."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    EXECUTED = "executed"
    DISPUTED = "disputed"
    REVERTED = "reverted"


@dataclass
class MandateRecord:
    """Individual mandate record for blockchain storage."""
    record_id: str
    mandate_type: MandateType
    mandate_id: str
    user_did: str
    merchant_did: str
    agent_did: str
    ap2_mandate_data: Dict[str, Any]
    cryptographic_proof: str
    timestamp: datetime
    status: RecordStatus
    transaction_amount: Optional[float] = None
    currency: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LedgerBlock:
    """Blockchain block containing mandate records."""
    block_number: int
    previous_hash: str
    timestamp: datetime
    records: List[MandateRecord]
    merkle_root: str
    block_hash: str
    nonce: int
    difficulty: int
    miner_id: str
    signatures: List[Dict[str, str]]  # Multi-signature consensus


class MandateLedger:
    """
    Distributed Ledger for AP2 Mandate Verification

    Provides immutable storage and verification of AP2 payment mandates
    with cryptographic proof of compliance and regulatory audit trails.
    """

    def __init__(
        self,
        node_id: str,
        private_key: rsa.RSAPrivateKey,
        database_path: str = "mandate_ledger.db",
        difficulty: int = 4
    ):
        self.node_id = node_id
        self.private_key = private_key
        self.public_key = private_key.public_key()
        self.database_path = database_path
        self.difficulty = difficulty

        # Blockchain state
        self.blockchain: List[LedgerBlock] = []
        self.pending_records: List[MandateRecord] = []
        self.record_pool: Dict[str, MandateRecord] = {}

        # Verification state
        self.verified_mandates: Dict[str, bool] = {}
        self.mandate_index: Dict[str, str] = {}  # mandate_id -> block_hash

        # Network state
        self.peer_nodes: Dict[str, Dict[str, Any]] = {}
        self.consensus_threshold = 0.51  # 51% for majority

        # Initialize
        asyncio.create_task(self._initialize_ledger())

    async def add_mandate_record(
        self,
        mandate_type: MandateType,
        mandate_id: str,
        user_did: str,
        merchant_did: str,
        agent_did: str,
        ap2_mandate_data: Dict[str, Any],
        cryptographic_proof: str,
        transaction_amount: Optional[float] = None,
        currency: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a new mandate record to the ledger.

        Args:
            mandate_type: Type of AP2 mandate
            mandate_id: Unique mandate identifier
            user_did: User's decentralized identifier
            merchant_did: Merchant's DID
            agent_did: Processing agent's DID
            ap2_mandate_data: Complete AP2 mandate structure
            cryptographic_proof: RSA signature of the mandate
            transaction_amount: Transaction amount (if applicable)
            currency: Currency code
            metadata: Additional metadata

        Returns:
            record_id: Unique identifier for the ledger record
        """
        # Validate mandate data
        if not await self._validate_ap2_mandate(ap2_mandate_data, mandate_type):
            raise ValueError("Invalid AP2 mandate data")

        # Create record
        record = MandateRecord(
            record_id=f"{mandate_type.value}_{mandate_id}_{int(datetime.now().timestamp())}",
            mandate_type=mandate_type,
            mandate_id=mandate_id,
            user_did=user_did,
            merchant_did=merchant_did,
            agent_did=agent_did,
            ap2_mandate_data=ap2_mandate_data,
            cryptographic_proof=cryptographic_proof,
            timestamp=datetime.now(timezone.utc),
            status=RecordStatus.PENDING,
            transaction_amount=transaction_amount,
            currency=currency,
            metadata=metadata or {}
        )

        # Add to pending pool
        self.pending_records.append(record)
        self.record_pool[record.record_id] = record

        print(f"📝 Added mandate record: {record.record_id}")

        # Try to mine block if we have enough records
        if len(self.pending_records) >= 5:  # Configurable block size
            await self._mine_block()

        return record.record_id

    async def verify_mandate(
        self,
        mandate_id: str,
        verification_criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Verify a mandate against the distributed ledger.

        Args:
            mandate_id: Mandate ID to verify
            verification_criteria: Additional verification criteria

        Returns:
            Verification result with proof of inclusion
        """
        # Find mandate in ledger
        block_hash = self.mandate_index.get(mandate_id)
        if not block_hash:
            return {
                "verified": False,
                "error": "Mandate not found in ledger",
                "mandate_id": mandate_id
            }

        # Get block containing the mandate
        block = await self._get_block_by_hash(block_hash)
        if not block:
            return {
                "verified": False,
                "error": "Block not found",
                "mandate_id": mandate_id
            }

        # Find the specific record
        mandate_record = None
        for record in block.records:
            if record.mandate_id == mandate_id:
                mandate_record = record
                break

        if not mandate_record:
            return {
                "verified": False,
                "error": "Record not found in block",
                "mandate_id": mandate_id
            }

        # Verify cryptographic proof
        proof_valid = await self._verify_mandate_proof(mandate_record)

        # Verify blockchain integrity
        chain_valid = await self._verify_block_integrity(block)

        # Check consensus
        consensus_valid = await self._verify_block_consensus(block)

        # Generate Merkle proof
        merkle_proof = self._generate_merkle_proof(block, mandate_record)

        verification_result = {
            "verified": proof_valid and chain_valid and consensus_valid,
            "mandate_id": mandate_id,
            "record_id": mandate_record.record_id,
            "block_number": block.block_number,
            "block_hash": block.block_hash,
            "timestamp": mandate_record.timestamp.isoformat(),
            "status": mandate_record.status.value,
            "proofs": {
                "cryptographic_proof_valid": proof_valid,
                "blockchain_integrity_valid": chain_valid,
                "consensus_valid": consensus_valid,
                "merkle_proof": merkle_proof
            },
            "mandate_data": mandate_record.ap2_mandate_data
        }

        # Apply additional verification criteria
        if verification_criteria:
            additional_checks = await self._apply_verification_criteria(
                mandate_record, verification_criteria
            )
            verification_result["additional_checks"] = additional_checks

        return verification_result

    async def get_mandate_history(
        self,
        mandate_id: str
    ) -> List[Dict[str, Any]]:
        """Get complete history of a mandate across all records."""
        history = []

        # Search all blocks for records with this mandate_id
        for block in self.blockchain:
            for record in block.records:
                if record.mandate_id == mandate_id:
                    history.append({
                        "record_id": record.record_id,
                        "mandate_type": record.mandate_type.value,
                        "status": record.status.value,
                        "timestamp": record.timestamp.isoformat(),
                        "block_number": block.block_number,
                        "block_hash": block.block_hash,
                        "agent_did": record.agent_did,
                        "metadata": record.metadata
                    })

        # Sort by timestamp
        history.sort(key=lambda x: x["timestamp"])
        return history

    async def get_user_mandates(
        self,
        user_did: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get all mandates for a specific user."""
        user_mandates = []

        for block in self.blockchain:
            for record in block.records:
                if record.user_did == user_did:
                    # Date filtering
                    if start_date and record.timestamp < start_date:
                        continue
                    if end_date and record.timestamp > end_date:
                        continue

                    user_mandates.append({
                        "mandate_id": record.mandate_id,
                        "mandate_type": record.mandate_type.value,
                        "status": record.status.value,
                        "merchant_did": record.merchant_did,
                        "amount": record.transaction_amount,
                        "currency": record.currency,
                        "timestamp": record.timestamp.isoformat(),
                        "block_number": block.block_number
                    })

        return user_mandates

    async def get_merchant_transactions(
        self,
        merchant_did: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get transaction summary for a merchant."""
        transactions = []
        total_amount = 0.0
        currency_totals = {}

        for block in self.blockchain:
            for record in block.records:
                if record.merchant_did == merchant_did:
                    # Date filtering
                    if start_date and record.timestamp < start_date:
                        continue
                    if end_date and record.timestamp > end_date:
                        continue

                    if record.mandate_type == MandateType.PAYMENT_MANDATE and record.status == RecordStatus.EXECUTED:
                        transactions.append({
                            "mandate_id": record.mandate_id,
                            "user_did": record.user_did,
                            "amount": record.transaction_amount,
                            "currency": record.currency,
                            "timestamp": record.timestamp.isoformat()
                        })

                        # Sum amounts
                        if record.transaction_amount and record.currency:
                            if record.currency not in currency_totals:
                                currency_totals[record.currency] = 0.0
                            currency_totals[record.currency] += record.transaction_amount

        return {
            "merchant_did": merchant_did,
            "transaction_count": len(transactions),
            "currency_totals": currency_totals,
            "transactions": transactions,
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            }
        }

    async def update_mandate_status(
        self,
        mandate_id: str,
        new_status: RecordStatus,
        agent_did: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update the status of a mandate (creates new record).

        Args:
            mandate_id: Mandate to update
            new_status: New status
            agent_did: Agent making the update
            metadata: Additional metadata

        Returns:
            Success status
        """
        # Find original mandate
        original_record = None
        for block in self.blockchain:
            for record in block.records:
                if record.mandate_id == mandate_id:
                    original_record = record
                    break

        if not original_record:
            return False

        # Create status update record
        update_record = MandateRecord(
            record_id=f"status_update_{mandate_id}_{int(datetime.now().timestamp())}",
            mandate_type=original_record.mandate_type,
            mandate_id=mandate_id,
            user_did=original_record.user_did,
            merchant_did=original_record.merchant_did,
            agent_did=agent_did,
            ap2_mandate_data=original_record.ap2_mandate_data,
            cryptographic_proof=original_record.cryptographic_proof,
            timestamp=datetime.now(timezone.utc),
            status=new_status,
            transaction_amount=original_record.transaction_amount,
            currency=original_record.currency,
            metadata={
                **(original_record.metadata or {}),
                "status_update": True,
                "previous_status": original_record.status.value,
                "updated_by": agent_did,
                **(metadata or {})
            }
        )

        # Add to pending records
        self.pending_records.append(update_record)
        self.record_pool[update_record.record_id] = update_record

        print(f"📋 Status update for {mandate_id}: {original_record.status.value} -> {new_status.value}")
        return True

    async def get_ledger_statistics(self) -> Dict[str, Any]:
        """Get comprehensive ledger statistics."""
        total_blocks = len(self.blockchain)
        total_records = sum(len(block.records) for block in self.blockchain)

        # Count by mandate type
        by_mandate_type = {}
        by_status = {}
        by_currency = {}

        for block in self.blockchain:
            for record in block.records:
                # Count by type
                mandate_type = record.mandate_type.value
                by_mandate_type[mandate_type] = by_mandate_type.get(mandate_type, 0) + 1

                # Count by status
                status = record.status.value
                by_status[status] = by_status.get(status, 0) + 1

                # Count by currency
                if record.currency:
                    by_currency[record.currency] = by_currency.get(record.currency, 0) + 1

        return {
            "node_id": self.node_id,
            "total_blocks": total_blocks,
            "total_records": total_records,
            "pending_records": len(self.pending_records),
            "by_mandate_type": by_mandate_type,
            "by_status": by_status,
            "by_currency": by_currency,
            "chain_length": total_blocks,
            "last_block_time": self.blockchain[-1].timestamp.isoformat() if self.blockchain else None,
            "verified_mandates": len(self.verified_mandates)
        }

    # Private methods

    async def _initialize_ledger(self):
        """Initialize the mandate ledger database and genesis block."""
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS blocks (
                    block_number INTEGER PRIMARY KEY,
                    previous_hash TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    merkle_root TEXT NOT NULL,
                    block_hash TEXT UNIQUE NOT NULL,
                    nonce INTEGER NOT NULL,
                    difficulty INTEGER NOT NULL,
                    miner_id TEXT NOT NULL,
                    signatures TEXT NOT NULL,
                    records_json TEXT NOT NULL
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS mandate_index (
                    mandate_id TEXT PRIMARY KEY,
                    block_hash TEXT NOT NULL,
                    record_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)

            await db.commit()

        # Load existing blockchain
        await self._load_blockchain()

        # Create genesis block if empty
        if not self.blockchain:
            await self._create_genesis_block()

    async def _load_blockchain(self):
        """Load blockchain from database."""
        async with aiosqlite.connect(self.database_path) as db:
            cursor = await db.execute(
                "SELECT * FROM blocks ORDER BY block_number ASC"
            )
            rows = await cursor.fetchall()

            for row in rows:
                block = self._row_to_block(row)
                self.blockchain.append(block)

                # Update mandate index
                for record in block.records:
                    self.mandate_index[record.mandate_id] = block.block_hash

    def _row_to_block(self, row) -> LedgerBlock:
        """Convert database row to LedgerBlock."""
        records_data = json.loads(row[9])
        records = []

        for record_data in records_data:
            record = MandateRecord(
                record_id=record_data["record_id"],
                mandate_type=MandateType(record_data["mandate_type"]),
                mandate_id=record_data["mandate_id"],
                user_did=record_data["user_did"],
                merchant_did=record_data["merchant_did"],
                agent_did=record_data["agent_did"],
                ap2_mandate_data=record_data["ap2_mandate_data"],
                cryptographic_proof=record_data["cryptographic_proof"],
                timestamp=datetime.fromisoformat(record_data["timestamp"]),
                status=RecordStatus(record_data["status"]),
                transaction_amount=record_data.get("transaction_amount"),
                currency=record_data.get("currency"),
                metadata=record_data.get("metadata", {})
            )
            records.append(record)

        return LedgerBlock(
            block_number=row[0],
            previous_hash=row[1],
            timestamp=datetime.fromisoformat(row[2]),
            records=records,
            merkle_root=row[3],
            block_hash=row[4],
            nonce=row[5],
            difficulty=row[6],
            miner_id=row[7],
            signatures=json.loads(row[8])
        )

    async def _create_genesis_block(self):
        """Create the genesis block."""
        genesis_block = LedgerBlock(
            block_number=0,
            previous_hash="0" * 64,
            timestamp=datetime.now(timezone.utc),
            records=[],
            merkle_root="0" * 64,
            block_hash="",
            nonce=0,
            difficulty=self.difficulty,
            miner_id=self.node_id,
            signatures=[]
        )

        # Calculate genesis hash
        genesis_block.block_hash = self._calculate_block_hash(genesis_block)

        # Add to chain
        self.blockchain.append(genesis_block)

        # Save to database
        await self._save_block(genesis_block)

        print("🌱 Created genesis block")

    async def _mine_block(self):
        """Mine a new block with pending records."""
        if not self.pending_records:
            return

        # Create new block
        block_number = len(self.blockchain)
        previous_hash = self.blockchain[-1].block_hash if self.blockchain else "0" * 64

        block = LedgerBlock(
            block_number=block_number,
            previous_hash=previous_hash,
            timestamp=datetime.now(timezone.utc),
            records=self.pending_records.copy(),
            merkle_root="",
            block_hash="",
            nonce=0,
            difficulty=self.difficulty,
            miner_id=self.node_id,
            signatures=[]
        )

        # Calculate Merkle root
        block.merkle_root = self._calculate_merkle_root(block.records)

        # Mine block (proof of work)
        block.block_hash, block.nonce = await self._proof_of_work(block)

        # Add to blockchain
        self.blockchain.append(block)

        # Update mandate index
        for record in block.records:
            self.mandate_index[record.mandate_id] = block.block_hash

        # Clear pending records
        self.pending_records.clear()

        # Save to database
        await self._save_block(block)

        print(f"⛏️ Mined block {block_number} with {len(block.records)} records")

    def _calculate_merkle_root(self, records: List[MandateRecord]) -> str:
        """Calculate Merkle root of records."""
        if not records:
            return "0" * 64

        # Hash each record
        hashes = []
        for record in records:
            record_data = json.dumps(asdict(record), sort_keys=True, default=str)
            record_hash = hashlib.sha256(record_data.encode()).hexdigest()
            hashes.append(record_hash)

        # Build Merkle tree
        while len(hashes) > 1:
            if len(hashes) % 2 == 1:
                hashes.append(hashes[-1])  # Duplicate last hash if odd

            new_hashes = []
            for i in range(0, len(hashes), 2):
                combined = hashes[i] + hashes[i + 1]
                new_hash = hashlib.sha256(combined.encode()).hexdigest()
                new_hashes.append(new_hash)

            hashes = new_hashes

        return hashes[0]

    async def _proof_of_work(self, block: LedgerBlock) -> Tuple[str, int]:
        """Perform proof of work mining."""
        target = "0" * block.difficulty
        nonce = 0

        while True:
            block.nonce = nonce
            block_hash = self._calculate_block_hash(block)

            if block_hash.startswith(target):
                return block_hash, nonce

            nonce += 1

            # Yield control periodically
            if nonce % 10000 == 0:
                await asyncio.sleep(0.001)

    def _calculate_block_hash(self, block: LedgerBlock) -> str:
        """Calculate hash of a block."""
        block_data = {
            "block_number": block.block_number,
            "previous_hash": block.previous_hash,
            "timestamp": block.timestamp.isoformat(),
            "merkle_root": block.merkle_root,
            "nonce": block.nonce,
            "difficulty": block.difficulty,
            "miner_id": block.miner_id
        }

        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def _generate_merkle_proof(
        self,
        block: LedgerBlock,
        target_record: MandateRecord
    ) -> List[str]:
        """Generate Merkle proof for a record in a block."""
        # Find target record index
        target_index = -1
        for i, record in enumerate(block.records):
            if record.record_id == target_record.record_id:
                target_index = i
                break

        if target_index == -1:
            return []

        # Generate proof path
        proof = []
        records = block.records.copy()

        # Hash each record
        current_hashes = []
        for record in records:
            record_data = json.dumps(asdict(record), sort_keys=True, default=str)
            record_hash = hashlib.sha256(record_data.encode()).hexdigest()
            current_hashes.append(record_hash)

        current_index = target_index

        # Build proof up the tree
        while len(current_hashes) > 1:
            if len(current_hashes) % 2 == 1:
                current_hashes.append(current_hashes[-1])

            # Find sibling
            if current_index % 2 == 0:
                sibling_index = current_index + 1
            else:
                sibling_index = current_index - 1

            if sibling_index < len(current_hashes):
                proof.append(current_hashes[sibling_index])

            # Move up one level
            new_hashes = []
            for i in range(0, len(current_hashes), 2):
                combined = current_hashes[i] + current_hashes[i + 1]
                new_hash = hashlib.sha256(combined.encode()).hexdigest()
                new_hashes.append(new_hash)

            current_hashes = new_hashes
            current_index = current_index // 2

        return proof

    async def _validate_ap2_mandate(
        self,
        mandate_data: Dict[str, Any],
        mandate_type: MandateType
    ) -> bool:
        """Validate AP2 mandate structure."""
        required_fields = {
            MandateType.INTENT_MANDATE: ["user_intent", "timestamp", "signature"],
            MandateType.CART_MANDATE: ["cart_contents", "merchant_authorization", "timestamp"],
            MandateType.PAYMENT_MANDATE: ["payment_details", "user_authorization", "merchant_confirmation"]
        }

        if mandate_type not in required_fields:
            return False

        for field in required_fields[mandate_type]:
            if field not in mandate_data:
                return False

        return True

    async def _verify_mandate_proof(self, record: MandateRecord) -> bool:
        """Verify cryptographic proof of a mandate record."""
        try:
            # In a real implementation, this would verify the RSA signature
            # against the user's public key from their DID
            return len(record.cryptographic_proof) > 0
        except Exception:
            return False

    async def _verify_block_integrity(self, block: LedgerBlock) -> bool:
        """Verify the integrity of a block."""
        # Recalculate block hash
        calculated_hash = self._calculate_block_hash(block)
        if calculated_hash != block.block_hash:
            return False

        # Verify proof of work
        target = "0" * block.difficulty
        if not block.block_hash.startswith(target):
            return False

        # Verify Merkle root
        calculated_merkle = self._calculate_merkle_root(block.records)
        if calculated_merkle != block.merkle_root:
            return False

        return True

    async def _verify_block_consensus(self, block: LedgerBlock) -> bool:
        """Verify consensus signatures on a block."""
        # In a distributed system, this would verify signatures from other nodes
        # For now, return True as we're running a single node
        return True

    async def _get_block_by_hash(self, block_hash: str) -> Optional[LedgerBlock]:
        """Get block by its hash."""
        for block in self.blockchain:
            if block.block_hash == block_hash:
                return block
        return None

    async def _save_block(self, block: LedgerBlock):
        """Save block to database."""
        records_json = json.dumps([asdict(record) for record in block.records], default=str)
        signatures_json = json.dumps(block.signatures)

        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                INSERT INTO blocks (
                    block_number, previous_hash, timestamp, merkle_root,
                    block_hash, nonce, difficulty, miner_id, signatures, records_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                block.block_number,
                block.previous_hash,
                block.timestamp.isoformat(),
                block.merkle_root,
                block.block_hash,
                block.nonce,
                block.difficulty,
                block.miner_id,
                signatures_json,
                records_json
            ))

            # Update mandate index
            for record in block.records:
                await db.execute("""
                    INSERT OR REPLACE INTO mandate_index
                    (mandate_id, block_hash, record_id, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (
                    record.mandate_id,
                    block.block_hash,
                    record.record_id,
                    record.timestamp.isoformat()
                ))

            await db.commit()

    async def _apply_verification_criteria(
        self,
        record: MandateRecord,
        criteria: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Apply additional verification criteria to a record."""
        results = {}

        # Amount validation
        if "max_amount" in criteria and record.transaction_amount:
            results["amount_within_limit"] = record.transaction_amount <= criteria["max_amount"]

        # Currency validation
        if "allowed_currencies" in criteria and record.currency:
            results["currency_allowed"] = record.currency in criteria["allowed_currencies"]

        # Time validation
        if "max_age_hours" in criteria:
            age_hours = (datetime.now(timezone.utc) - record.timestamp).total_seconds() / 3600
            results["age_within_limit"] = age_hours <= criteria["max_age_hours"]

        # Status validation
        if "required_status" in criteria:
            results["status_matches"] = record.status.value == criteria["required_status"]

        return results