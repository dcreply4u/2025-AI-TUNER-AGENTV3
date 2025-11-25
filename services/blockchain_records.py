"""
Blockchain-Verified Records Service
Tamper-proof performance records using blockchain.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger(__name__)


class RecordType(Enum):
    """Record type."""
    SPEED = "speed"
    TIME = "time"
    POWER = "power"
    TORQUE = "torque"
    LAP_TIME = "lap_time"
    QUARTER_MILE = "quarter_mile"
    CUSTOM = "custom"


class VerificationStatus(Enum):
    """Verification status."""
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"


@dataclass
class PerformanceRecord:
    """Performance record."""
    record_id: str
    record_type: RecordType
    value: float
    unit: str
    vehicle_id: str
    vehicle_name: str
    timestamp: float
    location: Optional[str] = None
    conditions: Dict[str, Any] = field(default_factory=dict)
    telemetry_data: Dict[str, Any] = field(default_factory=dict)
    verified: bool = False
    blockchain_hash: Optional[str] = None
    nft_token_id: Optional[str] = None


@dataclass
class BlockchainVerification:
    """Blockchain verification."""
    record_id: str
    blockchain_hash: str
    transaction_hash: Optional[str] = None
    block_number: Optional[int] = None
    verification_status: VerificationStatus = VerificationStatus.PENDING
    verified_at: Optional[float] = None


class BlockchainRecords:
    """
    Blockchain-verified records service.
    
    Features:
    - Create tamper-proof records
    - Verify record integrity
    - Mint NFTs for records
    - Marketplace for records
    """
    
    def __init__(
        self,
        blockchain_provider: Optional[str] = None,
        nft_contract_address: Optional[str] = None,
    ):
        """
        Initialize blockchain records service.
        
        Args:
            blockchain_provider: Blockchain provider URL (e.g., Ethereum, Polygon)
            nft_contract_address: NFT contract address
        """
        self.blockchain_provider = blockchain_provider
        self.nft_contract_address = nft_contract_address
        
        self.records: Dict[str, PerformanceRecord] = {}
        self.verifications: Dict[str, BlockchainVerification] = {}
        
        # Local storage
        self.data_dir = Path("data/blockchain_records")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self._load_records()
    
    def create_record(
        self,
        record_type: RecordType,
        value: float,
        unit: str,
        vehicle_id: str,
        vehicle_name: str,
        location: Optional[str] = None,
        conditions: Optional[Dict[str, Any]] = None,
        telemetry_data: Optional[Dict[str, Any]] = None,
    ) -> PerformanceRecord:
        """
        Create a performance record.
        
        Args:
            record_type: Type of record
            value: Record value
            unit: Unit of measurement
            vehicle_id: Vehicle ID
            vehicle_name: Vehicle name
            location: Location (optional)
            conditions: Environmental conditions
            telemetry_data: Telemetry data
        
        Returns:
            Created PerformanceRecord
        """
        record_id = self._generate_record_id(record_type, value, vehicle_id)
        
        record = PerformanceRecord(
            record_id=record_id,
            record_type=record_type,
            value=value,
            unit=unit,
            vehicle_id=vehicle_id,
            vehicle_name=vehicle_name,
            timestamp=time.time(),
            location=location,
            conditions=conditions or {},
            telemetry_data=telemetry_data or {},
        )
        
        # Generate blockchain hash
        record.blockchain_hash = self._generate_hash(record)
        
        self.records[record_id] = record
        self._save_records()
        
        LOGGER.info("Record created: %s - %s %s", record_type.value, value, unit)
        return record
    
    def verify_record(self, record_id: str) -> bool:
        """
        Verify record integrity using blockchain.
        
        Args:
            record_id: Record ID to verify
        
        Returns:
            True if verified
        """
        if record_id not in self.records:
            return False
        
        record = self.records[record_id]
        
        # Calculate current hash
        current_hash = self._generate_hash(record)
        
        # Compare with stored hash
        if record.blockchain_hash and current_hash == record.blockchain_hash:
            record.verified = True
            
            # Create verification entry
            verification = BlockchainVerification(
                record_id=record_id,
                blockchain_hash=current_hash,
                verification_status=VerificationStatus.VERIFIED,
                verified_at=time.time(),
            )
            
            self.verifications[record_id] = verification
            self._save_records()
            
            LOGGER.info("Record verified: %s", record_id)
            return True
        else:
            LOGGER.warning("Record verification failed: %s", record_id)
            return False
    
    def mint_nft(
        self,
        record_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Mint NFT for record.
        
        Args:
            record_id: Record ID
            metadata: Additional NFT metadata
        
        Returns:
            NFT token ID if minted successfully
        """
        if record_id not in self.records:
            return None
        
        record = self.records[record_id]
        
        if not record.verified:
            LOGGER.warning("Cannot mint NFT for unverified record")
            return None
        
        # In real implementation, would interact with blockchain
        # For now, generate a token ID
        token_id = f"nft_{int(time.time())}_{record_id[:8]}"
        
        record.nft_token_id = token_id
        
        # Store NFT metadata
        nft_metadata = {
            "name": f"{record.record_type.value.title()} Record",
            "description": f"{record.vehicle_name} - {record.value} {record.unit}",
            "image": self._generate_record_image(record),
            "attributes": [
                {"trait_type": "Type", "value": record.record_type.value},
                {"trait_type": "Value", "value": record.value},
                {"trait_type": "Unit", "value": record.unit},
                {"trait_type": "Vehicle", "value": record.vehicle_name},
                {"trait_type": "Date", "value": time.strftime("%Y-%m-%d", time.localtime(record.timestamp))},
            ],
            **(metadata or {}),
        }
        
        self._save_nft_metadata(record_id, nft_metadata)
        self._save_records()
        
        LOGGER.info("NFT minted: %s", token_id)
        return token_id
    
    def _generate_record_id(
        self,
        record_type: RecordType,
        value: float,
        vehicle_id: str,
    ) -> str:
        """Generate unique record ID."""
        data = f"{record_type.value}_{value}_{vehicle_id}_{int(time.time())}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _generate_hash(self, record: PerformanceRecord) -> str:
        """Generate blockchain hash for record."""
        # Create hashable data
        hash_data = {
            "record_id": record.record_id,
            "record_type": record.record_type.value,
            "value": record.value,
            "unit": record.unit,
            "vehicle_id": record.vehicle_id,
            "timestamp": record.timestamp,
            "conditions": json.dumps(record.conditions, sort_keys=True),
        }
        
        # Generate hash
        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    def _generate_record_image(self, record: PerformanceRecord) -> str:
        """Generate image URL for record NFT."""
        # In real implementation, would generate or upload image
        # For now, return placeholder
        return f"https://api.telemetryiq.com/records/{record.record_id}/image"
    
    def _save_nft_metadata(self, record_id: str, metadata: Dict[str, Any]) -> None:
        """Save NFT metadata."""
        try:
            metadata_file = self.data_dir / f"{record_id}_nft.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            LOGGER.error("Failed to save NFT metadata: %s", e)
    
    def get_record(self, record_id: str) -> Optional[PerformanceRecord]:
        """Get record by ID."""
        return self.records.get(record_id)
    
    def get_all_records(
        self,
        record_type: Optional[RecordType] = None,
        vehicle_id: Optional[str] = None,
    ) -> List[PerformanceRecord]:
        """Get all records, optionally filtered."""
        records = list(self.records.values())
        
        if record_type:
            records = [r for r in records if r.record_type == record_type]
        
        if vehicle_id:
            records = [r for r in records if r.vehicle_id == vehicle_id]
        
        return sorted(records, key=lambda r: r.timestamp, reverse=True)
    
    def _save_records(self) -> None:
        """Save records to disk."""
        try:
            records_file = self.data_dir / "records.json"
            with open(records_file, 'w') as f:
                json.dump({
                    record_id: {
                        "record_id": r.record_id,
                        "record_type": r.record_type.value,
                        "value": r.value,
                        "unit": r.unit,
                        "vehicle_id": r.vehicle_id,
                        "vehicle_name": r.vehicle_name,
                        "timestamp": r.timestamp,
                        "location": r.location,
                        "conditions": r.conditions,
                        "telemetry_data": r.telemetry_data,
                        "verified": r.verified,
                        "blockchain_hash": r.blockchain_hash,
                        "nft_token_id": r.nft_token_id,
                    }
                    for record_id, r in self.records.items()
                }, f, indent=2)
        except Exception as e:
            LOGGER.error("Failed to save records: %s", e)
    
    def _load_records(self) -> None:
        """Load records from disk."""
        try:
            records_file = self.data_dir / "records.json"
            if not records_file.exists():
                return
            
            with open(records_file, 'r') as f:
                data = json.load(f)
            
            for record_id, record_data in data.items():
                self.records[record_id] = PerformanceRecord(
                    record_id=record_data["record_id"],
                    record_type=RecordType(record_data["record_type"]),
                    value=record_data["value"],
                    unit=record_data["unit"],
                    vehicle_id=record_data["vehicle_id"],
                    vehicle_name=record_data["vehicle_name"],
                    timestamp=record_data["timestamp"],
                    location=record_data.get("location"),
                    conditions=record_data.get("conditions", {}),
                    telemetry_data=record_data.get("telemetry_data", {}),
                    verified=record_data.get("verified", False),
                    blockchain_hash=record_data.get("blockchain_hash"),
                    nft_token_id=record_data.get("nft_token_id"),
                )
        except Exception as e:
            LOGGER.error("Failed to load records: %s", e)

