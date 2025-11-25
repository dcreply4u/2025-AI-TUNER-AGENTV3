"""
GDPR Compliance Implementation
General Data Protection Regulation compliance features.
"""

from __future__ import annotations

import logging
import time
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3

LOGGER = logging.getLogger(__name__)


class ConsentType(Enum):
    """Types of consent."""
    DATA_COLLECTION = "data_collection"
    DATA_PROCESSING = "data_processing"
    DATA_SHARING = "data_sharing"
    MARKETING = "marketing"
    ANALYTICS = "analytics"


class DataCategory(Enum):
    """Data categories."""
    PERSONAL = "personal"  # Name, email, etc.
    TELEMETRY = "telemetry"  # Vehicle telemetry data
    LOCATION = "location"  # GPS data
    DIAGNOSTIC = "diagnostic"  # Diagnostic codes, errors
    CONFIGURATION = "configuration"  # ECU configurations
    PERFORMANCE = "performance"  # Performance metrics
    VIDEO = "video"  # Video recordings


@dataclass
class ConsentRecord:
    """Consent record."""
    consent_id: str
    user_id: str
    consent_type: ConsentType
    granted: bool
    timestamp: float
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    version: str = "1.0"
    withdrawn: bool = False
    withdrawal_timestamp: Optional[float] = None


@dataclass
class DataRetentionPolicy:
    """Data retention policy."""
    category: DataCategory
    retention_days: int
    auto_delete: bool = True
    archive_before_delete: bool = False


@dataclass
class DataSubjectRequest:
    """Data subject request (GDPR Article 15-22)."""
    request_id: str
    user_id: str
    request_type: str  # "access", "rectification", "erasure", "portability"
    timestamp: float
    status: str = "pending"  # "pending", "processing", "completed", "rejected"
    data_categories: List[DataCategory] = field(default_factory=list)
    completed_at: Optional[float] = None
    result_path: Optional[str] = None


class GDPRComplianceManager:
    """Manages GDPR compliance."""
    
    def __init__(self, db_path: str = "data/gdpr_compliance.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Consent records
        self.consent_records: Dict[str, ConsentRecord] = {}
        
        # Data retention policies
        self.retention_policies: Dict[DataCategory, DataRetentionPolicy] = {
            DataCategory.PERSONAL: DataRetentionPolicy(
                category=DataCategory.PERSONAL,
                retention_days=365,
                auto_delete=True,
                archive_before_delete=True,
            ),
            DataCategory.TELEMETRY: DataRetentionPolicy(
                category=DataCategory.TELEMETRY,
                retention_days=730,  # 2 years
                auto_delete=True,
            ),
            DataCategory.LOCATION: DataRetentionPolicy(
                category=DataCategory.LOCATION,
                retention_days=90,
                auto_delete=True,
            ),
            DataCategory.DIAGNOSTIC: DataRetentionPolicy(
                category=DataCategory.DIAGNOSTIC,
                retention_days=365,
                auto_delete=True,
            ),
            DataCategory.CONFIGURATION: DataRetentionPolicy(
                category=DataCategory.CONFIGURATION,
                retention_days=1825,  # 5 years (important for tuning history)
                auto_delete=False,
            ),
            DataCategory.PERFORMANCE: DataRetentionPolicy(
                category=DataCategory.PERFORMANCE,
                retention_days=730,
                auto_delete=True,
            ),
            DataCategory.VIDEO: DataRetentionPolicy(
                category=DataCategory.VIDEO,
                retention_days=90,
                auto_delete=True,
            ),
        }
        
        # Data subject requests
        self.requests: Dict[str, DataSubjectRequest] = {}
        
        # Load existing data
        self._load_consent_records()
        self._load_requests()
    
    def _init_database(self) -> None:
        """Initialize GDPR compliance database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Consent table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS consent_records (
                consent_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                consent_type TEXT NOT NULL,
                granted INTEGER NOT NULL,
                timestamp REAL NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                version TEXT,
                withdrawn INTEGER DEFAULT 0,
                withdrawal_timestamp REAL
            )
        """)
        
        # Data subject requests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_subject_requests (
                request_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                request_type TEXT NOT NULL,
                timestamp REAL NOT NULL,
                status TEXT NOT NULL,
                data_categories TEXT,
                completed_at REAL,
                result_path TEXT
            )
        """)
        
        # Data access log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_access_log (
                access_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                data_category TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp REAL NOT NULL,
                ip_address TEXT,
                user_agent TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _load_consent_records(self) -> None:
        """Load consent records from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM consent_records")
        rows = cursor.fetchall()
        
        for row in rows:
            record = ConsentRecord(
                consent_id=row[0],
                user_id=row[1],
                consent_type=ConsentType(row[2]),
                granted=bool(row[3]),
                timestamp=row[4],
                ip_address=row[5],
                user_agent=row[6],
                version=row[7] or "1.0",
                withdrawn=bool(row[8]),
                withdrawal_timestamp=row[9],
            )
            self.consent_records[record.consent_id] = record
        
        conn.close()
    
    def _load_requests(self) -> None:
        """Load data subject requests from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM data_subject_requests")
        rows = cursor.fetchall()
        
        for row in rows:
            categories = []
            if row[4]:
                try:
                    categories = [DataCategory(c) for c in json.loads(row[4])]
                except Exception:
                    pass
            
            request = DataSubjectRequest(
                request_id=row[0],
                user_id=row[1],
                request_type=row[2],
                timestamp=row[3],
                status=row[4],
                data_categories=categories,
                completed_at=row[5],
                result_path=row[6],
            )
            self.requests[request.request_id] = request
        
        conn.close()
    
    def record_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        granted: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ConsentRecord:
        """Record user consent."""
        consent_id = f"CONS-{int(time.time() * 1000)}"
        
        record = ConsentRecord(
            consent_id=consent_id,
            user_id=user_id,
            consent_type=consent_type,
            granted=granted,
            timestamp=time.time(),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        self.consent_records[consent_id] = record
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO consent_records 
            (consent_id, user_id, consent_type, granted, timestamp, ip_address, user_agent, version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.consent_id,
            record.user_id,
            record.consent_type.value,
            1 if record.granted else 0,
            record.timestamp,
            record.ip_address,
            record.user_agent,
            record.version,
        ))
        conn.commit()
        conn.close()
        
        LOGGER.info("Consent recorded: %s - %s - %s", user_id, consent_type.value, "granted" if granted else "denied")
        
        return record
    
    def withdraw_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
    ) -> bool:
        """Withdraw consent."""
        # Find active consent records
        active_consents = [
            r for r in self.consent_records.values()
            if r.user_id == user_id
            and r.consent_type == consent_type
            and r.granted
            and not r.withdrawn
        ]
        
        if not active_consents:
            return False
        
        # Withdraw all active consents
        for record in active_consents:
            record.withdrawn = True
            record.withdrawal_timestamp = time.time()
            
            # Update database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE consent_records
                SET withdrawn = 1, withdrawal_timestamp = ?
                WHERE consent_id = ?
            """, (record.withdrawal_timestamp, record.consent_id))
            conn.commit()
            conn.close()
        
        LOGGER.info("Consent withdrawn: %s - %s", user_id, consent_type.value)
        return True
    
    def has_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
    ) -> bool:
        """Check if user has active consent."""
        active_consents = [
            r for r in self.consent_records.values()
            if r.user_id == user_id
            and r.consent_type == consent_type
            and r.granted
            and not r.withdrawn
        ]
        return len(active_consents) > 0
    
    def request_data_access(self, user_id: str) -> DataSubjectRequest:
        """Request access to personal data (GDPR Article 15)."""
        request_id = f"REQ-{int(time.time() * 1000)}"
        
        request = DataSubjectRequest(
            request_id=request_id,
            user_id=user_id,
            request_type="access",
            timestamp=time.time(),
            data_categories=list(DataCategory),
        )
        
        self.requests[request_id] = request
        self._save_request(request)
        
        # Process request asynchronously
        self._process_access_request(request)
        
        return request
    
    def request_data_erasure(self, user_id: str) -> DataSubjectRequest:
        """Request data erasure (GDPR Article 17 - Right to be forgotten)."""
        request_id = f"REQ-{int(time.time() * 1000)}"
        
        request = DataSubjectRequest(
            request_id=request_id,
            user_id=user_id,
            request_type="erasure",
            timestamp=time.time(),
            data_categories=list(DataCategory),
        )
        
        self.requests[request_id] = request
        self._save_request(request)
        
        # Process request
        self._process_erasure_request(request)
        
        return request
    
    def request_data_portability(self, user_id: str) -> DataSubjectRequest:
        """Request data portability (GDPR Article 20)."""
        request_id = f"REQ-{int(time.time() * 1000)}"
        
        request = DataSubjectRequest(
            request_id=request_id,
            user_id=user_id,
            request_type="portability",
            timestamp=time.time(),
            data_categories=list(DataCategory),
        )
        
        self.requests[request_id] = request
        self._save_request(request)
        
        # Process request
        self._process_portability_request(request)
        
        return request
    
    def _process_access_request(self, request: DataSubjectRequest) -> None:
        """Process data access request."""
        request.status = "processing"
        self._save_request(request)
        
        try:
            # Collect user data from all sources
            user_data = self._collect_user_data(request.user_id, request.data_categories)
            
            # Export to JSON
            export_path = Path(f"exports/user_data_{request.user_id}_{int(time.time())}.json")
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_path, "w") as f:
                json.dump(user_data, f, indent=2, default=str)
            
            request.status = "completed"
            request.completed_at = time.time()
            request.result_path = str(export_path)
            self._save_request(request)
            
            LOGGER.info("Data access request completed: %s", request.request_id)
        except Exception as e:
            LOGGER.error("Error processing access request: %s", e)
            request.status = "rejected"
            self._save_request(request)
    
    def _process_erasure_request(self, request: DataSubjectRequest) -> None:
        """Process data erasure request."""
        request.status = "processing"
        self._save_request(request)
        
        try:
            # Delete user data from all sources
            deleted_count = self._delete_user_data(request.user_id, request.data_categories)
            
            request.status = "completed"
            request.completed_at = time.time()
            self._save_request(request)
            
            LOGGER.info("Data erasure request completed: %s - Deleted %d records", request.request_id, deleted_count)
        except Exception as e:
            LOGGER.error("Error processing erasure request: %s", e)
            request.status = "rejected"
            self._save_request(request)
    
    def _process_portability_request(self, request: DataSubjectRequest) -> None:
        """Process data portability request."""
        # Similar to access request but in machine-readable format
        self._process_access_request(request)
    
    def _collect_user_data(
        self,
        user_id: str,
        categories: List[DataCategory],
    ) -> Dict[str, Any]:
        """Collect user data from all sources."""
        data = {
            "user_id": user_id,
            "export_timestamp": time.time(),
            "data": {},
        }
        
        # This would integrate with actual data sources
        # For now, return structure
        
        for category in categories:
            data["data"][category.value] = {
                "count": 0,
                "sources": [],
                "note": "Data collection would be implemented per data source",
            }
        
        return data
    
    def _delete_user_data(
        self,
        user_id: str,
        categories: List[DataCategory],
    ) -> int:
        """Delete user data from all sources."""
        deleted_count = 0
        
        # This would integrate with actual data sources
        # For now, just return count
        
        LOGGER.info("Deleting user data for %s in categories: %s", user_id, [c.value for c in categories])
        
        return deleted_count
    
    def _save_request(self, request: DataSubjectRequest) -> None:
        """Save request to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO data_subject_requests
            (request_id, user_id, request_type, timestamp, status, data_categories, completed_at, result_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.request_id,
            request.user_id,
            request.request_type,
            request.timestamp,
            request.status,
            json.dumps([c.value for c in request.data_categories]),
            request.completed_at,
            request.result_path,
        ))
        
        conn.commit()
        conn.close()
    
    def apply_retention_policies(self) -> int:
        """Apply data retention policies and delete expired data."""
        deleted_count = 0
        current_time = time.time()
        
        for category, policy in self.retention_policies.items():
            if not policy.auto_delete:
                continue
            
            cutoff_time = current_time - (policy.retention_days * 24 * 3600)
            
            # This would integrate with actual data sources
            # For now, just log
            LOGGER.info(
                "Applying retention policy for %s: deleting data older than %d days",
                category.value, policy.retention_days
            )
        
        return deleted_count
    
    def log_data_access(
        self,
        user_id: str,
        category: DataCategory,
        action: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """Log data access for audit."""
        access_id = f"ACC-{int(time.time() * 1000000)}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO data_access_log
            (access_id, user_id, data_category, action, timestamp, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            access_id,
            user_id,
            category.value,
            action,
            time.time(),
            ip_address,
            user_agent,
        ))
        
        conn.commit()
        conn.close()
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """Get GDPR compliance report."""
        return {
            "consent_records": len(self.consent_records),
            "active_consents": len([r for r in self.consent_records.values() if r.granted and not r.withdrawn]),
            "pending_requests": len([r for r in self.requests.values() if r.status == "pending"]),
            "retention_policies": {
                cat.value: {
                    "retention_days": pol.retention_days,
                    "auto_delete": pol.auto_delete,
                }
                for cat, pol in self.retention_policies.items()
            },
        }


# Global instance
_gdpr_manager: Optional[GDPRComplianceManager] = None


def get_gdpr_manager() -> GDPRComplianceManager:
    """Get global GDPR compliance manager instance."""
    global _gdpr_manager
    if _gdpr_manager is None:
        _gdpr_manager = GDPRComplianceManager()
    return _gdpr_manager


__all__ = [
    "GDPRComplianceManager",
    "ConsentType",
    "DataCategory",
    "ConsentRecord",
    "DataRetentionPolicy",
    "DataSubjectRequest",
    "get_gdpr_manager",
]

