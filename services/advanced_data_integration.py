"""
Advanced Data Integration Platform

Handles large datasets, integrates with various data sources,
ensures data cleanliness, accuracy, and regular updates.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import sqlite3
from datetime import datetime, timedelta

LOGGER = logging.getLogger(__name__)

# Try to import data processing libraries
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None  # type: ignore

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None  # type: ignore


class DataSourceType(Enum):
    """Data source types."""
    TELEMETRY = "telemetry"
    TUNING_GUIDE = "tuning_guide"
    RACING_DATA = "racing_data"
    USER_SUBMISSION = "user_submission"
    COMMUNITY = "community"
    EXTERNAL_API = "external_api"
    DATABASE = "database"
    FILE = "file"
    STREAM = "stream"


class DataQuality(Enum):
    """Data quality levels."""
    EXCELLENT = "excellent"  # 95-100% confidence
    GOOD = "good"  # 80-95% confidence
    FAIR = "fair"  # 60-80% confidence
    POOR = "poor"  # <60% confidence
    INVALID = "invalid"  # Failed validation


@dataclass
class DataSource:
    """Data source configuration."""
    source_id: str
    source_type: DataSourceType
    name: str
    endpoint: Optional[str] = None  # URL, file path, etc.
    credentials: Optional[Dict[str, str]] = None
    update_frequency: int = 3600  # seconds
    last_update: Optional[float] = None
    enabled: bool = True
    validation_rules: List[Callable] = field(default_factory=list)
    transform_function: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataRecord:
    """Data record with metadata."""
    record_id: str
    source_id: str
    data: Dict[str, Any]
    timestamp: float
    quality_score: float  # 0-1
    quality_level: DataQuality
    validation_errors: List[str] = field(default_factory=list)
    checksum: str = ""
    version: int = 1


@dataclass
class DataStatistics:
    """Data statistics."""
    total_records: int = 0
    records_by_source: Dict[str, int] = field(default_factory=dict)
    records_by_quality: Dict[DataQuality, int] = field(default_factory=dict)
    average_quality_score: float = 0.0
    last_update_time: Optional[float] = None
    data_freshness: Dict[str, float] = field(default_factory=dict)  # source_id -> hours since update


class AdvancedDataIntegration:
    """
    Advanced data integration platform.
    
    Features:
    - Multi-source data ingestion
    - Data cleaning and validation
    - Quality scoring
    - Automatic updates
    - Large dataset handling
    - Data deduplication
    - Schema validation
    - Data transformation
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize data integration platform.
        
        Args:
            storage_path: Path to store data
        """
        self.storage_path = storage_path or Path("data/integrated_data")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Database for metadata
        self.db_path = self.storage_path / "data_metadata.db"
        self._init_database()
        
        # Data sources
        self.sources: Dict[str, DataSource] = {}
        
        # Data records cache
        self.records_cache: Dict[str, DataRecord] = {}
        
        # Statistics
        self.statistics = DataStatistics()
        
        # Validation rules
        self.global_validation_rules: List[Callable] = []
        
        # Update scheduler
        self.update_timers: Dict[str, Any] = {}
        
        LOGGER.info("Advanced data integration platform initialized")
    
    def _init_database(self) -> None:
        """Initialize SQLite database for metadata."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Data records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_records (
                record_id TEXT PRIMARY KEY,
                source_id TEXT,
                data_hash TEXT,
                timestamp REAL,
                quality_score REAL,
                quality_level TEXT,
                validation_errors TEXT,
                version INTEGER,
                data_json TEXT
            )
        """)
        
        # Data sources table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_sources (
                source_id TEXT PRIMARY KEY,
                source_type TEXT,
                name TEXT,
                endpoint TEXT,
                update_frequency INTEGER,
                last_update REAL,
                enabled INTEGER,
                metadata_json TEXT
            )
        """)
        
        # Update history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS update_history (
                update_id TEXT PRIMARY KEY,
                source_id TEXT,
                timestamp REAL,
                records_added INTEGER,
                records_updated INTEGER,
                records_failed INTEGER,
                status TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def register_source(self, source: DataSource) -> None:
        """
        Register a data source.
        
        Args:
            source: Data source configuration
        """
        self.sources[source.source_id] = source
        
        # Save to database
        self._save_source_to_db(source)
        
        # Schedule updates
        if source.enabled:
            self._schedule_updates(source)
        
        LOGGER.info("Registered data source: %s (%s)", source.name, source.source_type.value)
    
    def ingest_data(
        self,
        source_id: str,
        data: List[Dict[str, Any]],
        validate: bool = True,
        transform: bool = True
    ) -> Tuple[int, int, int]:
        """
        Ingest data from source.
        
        Args:
            source_id: Source identifier
            data: List of data records
            validate: Whether to validate data
            transform: Whether to transform data
        
        Returns:
            Tuple of (added, updated, failed) counts
        """
        if source_id not in self.sources:
            raise ValueError(f"Source not found: {source_id}")
        
        source = self.sources[source_id]
        added = 0
        updated = 0
        failed = 0
        
        for raw_record in data:
            try:
                # Transform if needed
                if transform and source.transform_function:
                    transformed = source.transform_function(raw_record)
                else:
                    transformed = raw_record
                
                # Validate
                if validate:
                    quality_score, quality_level, errors = self._validate_record(
                        transformed, source
                    )
                else:
                    quality_score, quality_level, errors = 1.0, DataQuality.EXCELLENT, []
                
                # Skip invalid records
                if quality_level == DataQuality.INVALID:
                    failed += 1
                    continue
                
                # Generate record ID
                record_id = self._generate_record_id(source_id, transformed)
                
                # Check if exists
                existing = self._get_record(record_id)
                
                if existing:
                    # Update existing
                    if quality_score > existing.quality_score:
                        # Better quality, update
                        record = DataRecord(
                            record_id=record_id,
                            source_id=source_id,
                            data=transformed,
                            timestamp=time.time(),
                            quality_score=quality_score,
                            quality_level=quality_level,
                            validation_errors=errors,
                            checksum=self._calculate_checksum(transformed),
                            version=existing.version + 1,
                        )
                        self._save_record(record)
                        updated += 1
                else:
                    # New record
                    record = DataRecord(
                        record_id=record_id,
                        source_id=source_id,
                        data=transformed,
                        timestamp=time.time(),
                        quality_score=quality_score,
                        quality_level=quality_level,
                        validation_errors=errors,
                        checksum=self._calculate_checksum(transformed),
                    )
                    self._save_record(record)
                    added += 1
                
            except Exception as e:
                LOGGER.error("Error ingesting record from %s: %s", source_id, e)
                failed += 1
        
        # Update source last_update
        source.last_update = time.time()
        self._save_source_to_db(source)
        
        # Update statistics
        self._update_statistics()
        
        LOGGER.info("Ingested data from %s: %d added, %d updated, %d failed", source_id, added, updated, failed)
        
        return added, updated, failed
    
    def _validate_record(
        self,
        record: Dict[str, Any],
        source: DataSource
    ) -> Tuple[float, DataQuality, List[str]]:
        """
        Validate data record.
        
        Args:
            record: Data record
            source: Data source
        
        Returns:
            Tuple of (quality_score, quality_level, errors)
        """
        errors = []
        score = 1.0
        
        # Source-specific validation
        for rule in source.validation_rules:
            try:
                if not rule(record):
                    errors.append(f"Failed source validation: {rule.__name__}")
                    score -= 0.2
            except Exception as e:
                errors.append(f"Validation error: {e}")
                score -= 0.1
        
        # Global validation
        for rule in self.global_validation_rules:
            try:
                if not rule(record):
                    errors.append(f"Failed global validation: {rule.__name__}")
                    score -= 0.1
            except Exception as e:
                errors.append(f"Validation error: {e}")
                score -= 0.05
        
        # Basic checks
        if not record:
            errors.append("Empty record")
            score = 0.0
        
        # Determine quality level
        if score >= 0.95:
            quality = DataQuality.EXCELLENT
        elif score >= 0.80:
            quality = DataQuality.GOOD
        elif score >= 0.60:
            quality = DataQuality.FAIR
        elif score >= 0.40:
            quality = DataQuality.POOR
        else:
            quality = DataQuality.INVALID
        
        return max(0.0, score), quality, errors
    
    def _generate_record_id(self, source_id: str, data: Dict[str, Any]) -> str:
        """Generate unique record ID."""
        # Use hash of key fields
        key_data = json.dumps(data, sort_keys=True)
        data_hash = hashlib.md5(key_data.encode()).hexdigest()[:16]
        return f"{source_id}_{data_hash}"
    
    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate data checksum."""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def _save_record(self, record: DataRecord) -> None:
        """Save record to database and cache."""
        # Save to cache
        self.records_cache[record.record_id] = record
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO data_records
            (record_id, source_id, data_hash, timestamp, quality_score, quality_level, validation_errors, version, data_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.record_id,
            record.source_id,
            record.checksum,
            record.timestamp,
            record.quality_score,
            record.quality_level.value,
            json.dumps(record.validation_errors),
            record.version,
            json.dumps(record.data),
        ))
        
        conn.commit()
        conn.close()
    
    def _get_record(self, record_id: str) -> Optional[DataRecord]:
        """Get record from cache or database."""
        # Check cache first
        if record_id in self.records_cache:
            return self.records_cache[record_id]
        
        # Load from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT source_id, data_json, timestamp, quality_score, quality_level, validation_errors, version, data_hash
            FROM data_records WHERE record_id = ?
        """, (record_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            source_id, data_json, timestamp, quality_score, quality_level, errors_json, version, checksum = row
            return DataRecord(
                record_id=record_id,
                source_id=source_id,
                data=json.loads(data_json),
                timestamp=timestamp,
                quality_score=quality_score,
                quality_level=DataQuality(quality_level),
                validation_errors=json.loads(errors_json),
                checksum=checksum,
                version=version,
            )
        
        return None
    
    def query_data(
        self,
        source_ids: Optional[List[str]] = None,
        min_quality: DataQuality = DataQuality.FAIR,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[DataRecord]:
        """
        Query data records.
        
        Args:
            source_ids: Filter by source IDs
            min_quality: Minimum quality level
            filters: Additional filters
            limit: Maximum results
        
        Returns:
            List of data records
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build query
        query = "SELECT record_id FROM data_records WHERE 1=1"
        params = []
        
        if source_ids:
            placeholders = ",".join("?" * len(source_ids))
            query += f" AND source_id IN ({placeholders})"
            params.extend(source_ids)
        
        # Quality filter
        quality_threshold = {
            DataQuality.EXCELLENT: 0.95,
            DataQuality.GOOD: 0.80,
            DataQuality.FAIR: 0.60,
            DataQuality.POOR: 0.40,
        }.get(min_quality, 0.0)
        query += " AND quality_score >= ?"
        params.append(quality_threshold)
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, params)
        record_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # Load records
        records = []
        for record_id in record_ids:
            record = self._get_record(record_id)
            if record:
                # Apply filters
                if filters:
                    match = True
                    for key, value in filters.items():
                        if key not in record.data or record.data[key] != value:
                            match = False
                            break
                    if not match:
                        continue
                
                records.append(record)
        
        return records
    
    def _save_source_to_db(self, source: DataSource) -> None:
        """Save source to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO data_sources
            (source_id, source_type, name, endpoint, update_frequency, last_update, enabled, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            source.source_id,
            source.source_type.value,
            source.name,
            source.endpoint,
            source.update_frequency,
            source.last_update,
            1 if source.enabled else 0,
            json.dumps(source.metadata),
        ))
        
        conn.commit()
        conn.close()
    
    def _schedule_updates(self, source: DataSource) -> None:
        """Schedule automatic updates for source."""
        # In real implementation, would use scheduler
        # For now, just mark for update checking
        LOGGER.info("Scheduled updates for source: %s (every %d seconds)", source.name, source.update_frequency)
    
    def _update_statistics(self) -> None:
        """Update data statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total records
        cursor.execute("SELECT COUNT(*) FROM data_records")
        self.statistics.total_records = cursor.fetchone()[0]
        
        # By source
        cursor.execute("SELECT source_id, COUNT(*) FROM data_records GROUP BY source_id")
        self.statistics.records_by_source = {row[0]: row[1] for row in cursor.fetchall()}
        
        # By quality
        cursor.execute("SELECT quality_level, COUNT(*) FROM data_records GROUP BY quality_level")
        self.statistics.records_by_quality = {
            DataQuality(row[0]): row[1] for row in cursor.fetchall()
        }
        
        # Average quality
        cursor.execute("SELECT AVG(quality_score) FROM data_records")
        avg = cursor.fetchone()[0]
        self.statistics.average_quality_score = avg if avg else 0.0
        
        # Data freshness
        for source_id in self.sources:
            source = self.sources[source_id]
            if source.last_update:
                hours_old = (time.time() - source.last_update) / 3600
                self.statistics.data_freshness[source_id] = hours_old
        
        conn.close()
    
    def get_statistics(self) -> DataStatistics:
        """Get current statistics."""
        self._update_statistics()
        return self.statistics
    
    def clean_data(
        self,
        source_id: Optional[str] = None,
        remove_duplicates: bool = True,
        remove_invalid: bool = True
    ) -> Dict[str, int]:
        """
        Clean data.
        
        Args:
            source_id: Clean specific source (None = all)
            remove_duplicates: Remove duplicate records
            remove_invalid: Remove invalid records
        
        Returns:
            Dictionary with cleanup statistics
        """
        stats = {
            "duplicates_removed": 0,
            "invalid_removed": 0,
            "records_cleaned": 0,
        }
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Remove invalid
        if remove_invalid:
            query = "DELETE FROM data_records WHERE quality_level = ?"
            params = [DataQuality.INVALID.value]
            if source_id:
                query += " AND source_id = ?"
                params.append(source_id)
            cursor.execute(query, params)
            stats["invalid_removed"] = cursor.rowcount
        
        # Remove duplicates (keep highest quality)
        if remove_duplicates:
            # This would need more sophisticated logic
            # For now, just a placeholder
            pass
        
        conn.commit()
        conn.close()
        
        # Update statistics
        self._update_statistics()
        
        LOGGER.info("Data cleaning completed: %s", stats)
        return stats


__all__ = [
    "AdvancedDataIntegration",
    "DataSource",
    "DataSourceType",
    "DataRecord",
    "DataQuality",
    "DataStatistics",
]









