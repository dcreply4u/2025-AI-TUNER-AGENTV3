"""
Configuration Version Control
Tracks all configuration changes with history, analysis, and rollback capability
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any

LOGGER = logging.getLogger(__name__)


class ChangeType(Enum):
    """Type of configuration change."""
    ECU_TUNING = "ecu_tuning"
    PROTECTION = "protection"
    MOTORSPORT = "motorsport"
    TRANSMISSION = "transmission"
    SENSOR = "sensor"
    HARDWARE = "hardware"
    CAMERA = "camera"
    BACKUP = "backup"
    GLOBAL = "global"


class ChangeSeverity(Enum):
    """Severity of configuration change."""
    LOW = "low"  # Minor adjustment
    MEDIUM = "medium"  # Moderate change
    HIGH = "high"  # Significant change
    CRITICAL = "critical"  # Potentially dangerous


@dataclass
class ConfigChange:
    """Configuration change record."""
    change_id: str
    timestamp: float
    change_type: ChangeType
    category: str  # e.g., "Fuel VE", "Ignition Timing", "Boost Control"
    parameter: str  # Parameter name
    old_value: Any
    new_value: Any
    severity: ChangeSeverity
    user: str = "user"
    description: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    telemetry_snapshot: Dict[str, float] = field(default_factory=dict)
    outcome: Optional[str] = None  # "success", "warning", "failure"
    notes: str = ""


@dataclass
class ConfigSnapshot:
    """Complete configuration snapshot."""
    snapshot_id: str
    timestamp: float
    config_type: ChangeType
    configuration: Dict[str, Any]
    telemetry_baseline: Dict[str, float] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    description: str = ""


class ConfigVersionControl:
    """
    Configuration version control system.
    
    Features:
    - Track all configuration changes
    - Version history
    - Change analysis
    - Rollback capability
    - Historical data correlation
    - Performance tracking
    """
    
    def __init__(self, db_path: str = "config_history.db"):
        """
        Initialize configuration version control.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
        # In-memory cache for recent changes
        self.recent_changes: List[ConfigChange] = []
        self.max_cache_size = 100
    
    def _init_database(self) -> None:
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Configuration changes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config_changes (
                change_id TEXT PRIMARY KEY,
                timestamp REAL,
                change_type TEXT,
                category TEXT,
                parameter TEXT,
                old_value TEXT,
                new_value TEXT,
                severity TEXT,
                user TEXT,
                description TEXT,
                context TEXT,
                telemetry_snapshot TEXT,
                outcome TEXT,
                notes TEXT
            )
        """)
        
        # Configuration snapshots table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                timestamp REAL,
                config_type TEXT,
                configuration TEXT,
                telemetry_baseline TEXT,
                performance_metrics TEXT,
                description TEXT
            )
        """)
        
        # Performance history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id TEXT,
                timestamp REAL,
                metric_name TEXT,
                metric_value REAL,
                FOREIGN KEY (snapshot_id) REFERENCES config_snapshots(snapshot_id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON config_changes(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON config_changes(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_parameter ON config_changes(parameter)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshot_timestamp ON config_snapshots(timestamp)")
        
        conn.commit()
        conn.close()
    
    def record_change(
        self,
        change_type: ChangeType,
        category: str,
        parameter: str,
        old_value: Any,
        new_value: Any,
        severity: ChangeSeverity = ChangeSeverity.MEDIUM,
        description: str = "",
        context: Optional[Dict[str, Any]] = None,
        telemetry: Optional[Dict[str, float]] = None,
    ) -> ConfigChange:
        """
        Record a configuration change.
        
        Args:
            change_type: Type of change
            category: Category (e.g., "Fuel VE", "Ignition Timing")
            parameter: Parameter name
            old_value: Previous value
            new_value: New value
            severity: Change severity
            description: Optional description
            context: Optional context
            telemetry: Optional telemetry snapshot
            
        Returns:
            ConfigChange record
        """
        change_id = f"{int(time.time() * 1000)}_{hashlib.md5(f'{category}:{parameter}'.encode()).hexdigest()[:8]}"
        
        change = ConfigChange(
            change_id=change_id,
            timestamp=time.time(),
            change_type=change_type,
            category=category,
            parameter=parameter,
            old_value=old_value,
            new_value=new_value,
            severity=severity,
            description=description,
            context=context or {},
            telemetry_snapshot=telemetry or {},
        )
        
        # Save to database
        self._save_change(change)
        
        # Add to cache
        self.recent_changes.append(change)
        if len(self.recent_changes) > self.max_cache_size:
            self.recent_changes.pop(0)
        
        LOGGER.info("Recorded config change: %s.%s = %s -> %s", category, parameter, old_value, new_value)
        return change
    
    def __init__(self, db_path: str = "config_history.db"):
        """
        Initialize configuration version control.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
        # In-memory cache for recent changes
        self.recent_changes: List[ConfigChange] = []
        self.max_cache_size = 100
        
        # Connection pool for database operations
        try:
            from services.optimization_manager import ConnectionPool
            self.conn_pool = ConnectionPool(
                factory=lambda: sqlite3.connect(self.db_path, check_same_thread=False),
                max_size=3
            )
        except Exception:
            self.conn_pool = None
    
    def _save_change(self, change: ConfigChange) -> None:
        """Save change to database."""
        # Use connection pool if available
        if self.conn_pool:
            conn = self.conn_pool.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO config_changes
                    (change_id, timestamp, change_type, category, parameter, old_value, new_value,
                     severity, user, description, context, telemetry_snapshot, outcome, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    change.change_id,
                    change.timestamp,
                    change.change_type.value,
                    change.category,
                    change.parameter,
                    json.dumps(change.old_value),
                    json.dumps(change.new_value),
                    change.severity.value,
                    change.user,
                    change.description,
                    json.dumps(change.context),
                    json.dumps(change.telemetry_snapshot),
                    change.outcome,
                    change.notes,
                ))
                conn.commit()
            finally:
                self.conn_pool.return_connection(conn)
        else:
            # Fallback to direct connection
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO config_changes
                (change_id, timestamp, change_type, category, parameter, old_value, new_value,
                 severity, user, description, context, telemetry_snapshot, outcome, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                change.change_id,
                change.timestamp,
                change.change_type.value,
                change.category,
                change.parameter,
                json.dumps(change.old_value),
                json.dumps(change.new_value),
                change.severity.value,
                change.user,
                change.description,
                json.dumps(change.context),
                json.dumps(change.telemetry_snapshot),
                change.outcome,
                change.notes,
            ))
            
            conn.commit()
            conn.close()
    
    def create_snapshot(
        self,
        config_type: ChangeType,
        configuration: Dict[str, Any],
        telemetry: Optional[Dict[str, float]] = None,
        performance: Optional[Dict[str, float]] = None,
        description: str = "",
    ) -> ConfigSnapshot:
        """
        Create a configuration snapshot.
        
        Args:
            config_type: Type of configuration
            configuration: Complete configuration
            telemetry: Telemetry baseline
            performance: Performance metrics
            description: Snapshot description
            
        Returns:
            ConfigSnapshot
        """
        snapshot_id = f"snapshot_{int(time.time() * 1000)}_{hashlib.md5(json.dumps(configuration, sort_keys=True).encode()).hexdigest()[:8]}"
        
        snapshot = ConfigSnapshot(
            snapshot_id=snapshot_id,
            timestamp=time.time(),
            config_type=config_type,
            configuration=configuration,
            telemetry_baseline=telemetry or {},
            performance_metrics=performance or {},
            description=description,
        )
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO config_snapshots
            (snapshot_id, timestamp, config_type, configuration, telemetry_baseline,
             performance_metrics, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot.snapshot_id,
            snapshot.timestamp,
            snapshot.config_type.value,
            json.dumps(snapshot.configuration),
            json.dumps(snapshot.telemetry_baseline),
            json.dumps(snapshot.performance_metrics),
            snapshot.description,
        ))
        
        conn.commit()
        conn.close()
        
        LOGGER.info("Created config snapshot: %s", snapshot_id)
        return snapshot
    
    def get_change_history(
        self,
        category: Optional[str] = None,
        parameter: Optional[str] = None,
        limit: int = 100,
    ) -> List[ConfigChange]:
        """
        Get configuration change history.
        
        Args:
            category: Filter by category
            parameter: Filter by parameter
            limit: Maximum number of records
            
        Returns:
            List of configuration changes
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM config_changes WHERE 1=1"
        params = []
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if parameter:
            query += " AND parameter = ?"
            params.append(parameter)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        changes = []
        for row in rows:
            change = ConfigChange(
                change_id=row[0],
                timestamp=row[1],
                change_type=ChangeType(row[2]),
                category=row[3],
                parameter=row[4],
                old_value=json.loads(row[5]),
                new_value=json.loads(row[6]),
                severity=ChangeSeverity(row[7]),
                user=row[8],
                description=row[9],
                context=json.loads(row[10]) if row[10] else {},
                telemetry_snapshot=json.loads(row[11]) if row[11] else {},
                outcome=row[12],
                notes=row[13] or "",
            )
            changes.append(change)
        
        return changes
    
    def get_similar_configurations(
        self,
        current_config: Dict[str, Any],
        config_type: ChangeType,
        limit: int = 10,
    ) -> List[ConfigSnapshot]:
        """
        Find similar historical configurations.
        
        Args:
            current_config: Current configuration
            config_type: Configuration type
            limit: Maximum number of results
            
        Returns:
            List of similar snapshots
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM config_snapshots
            WHERE config_type = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (config_type.value, limit * 5))  # Get more, then filter
        
        rows = cursor.fetchall()
        conn.close()
        
        snapshots = []
        for row in rows:
            snapshot = ConfigSnapshot(
                snapshot_id=row[0],
                timestamp=row[1],
                config_type=ChangeType(row[2]),
                configuration=json.loads(row[3]),
                telemetry_baseline=json.loads(row[4]) if row[4] else {},
                performance_metrics=json.loads(row[5]) if row[5] else {},
                description=row[6] or "",
            )
            snapshots.append(snapshot)
        
        # Calculate similarity and return top matches
        scored = []
        for snapshot in snapshots:
            similarity = self._calculate_similarity(current_config, snapshot.configuration)
            scored.append((similarity, snapshot))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [snapshot for _, snapshot in scored[:limit]]
    
    def _calculate_similarity(self, config1: Dict[str, Any], config2: Dict[str, Any]) -> float:
        """Calculate similarity between two configurations."""
        if not config1 or not config2:
            return 0.0
        
        # Get common keys
        keys1 = set(config1.keys())
        keys2 = set(config2.keys())
        common_keys = keys1.intersection(keys2)
        
        if not common_keys:
            return 0.0
        
        # Calculate similarity based on value differences
        total_diff = 0.0
        for key in common_keys:
            val1 = config1[key]
            val2 = config2[key]
            
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                # Numeric difference (normalized)
                if val1 != 0:
                    diff = abs(val1 - val2) / abs(val1)
                else:
                    diff = abs(val2) if val2 != 0 else 0
                total_diff += diff
            elif val1 == val2:
                total_diff += 0  # Match
            else:
                total_diff += 1  # Mismatch
        
        # Similarity = 1 - average difference
        avg_diff = total_diff / len(common_keys)
        similarity = max(0.0, 1.0 - avg_diff)
        
        return similarity
    
    def get_best_performing_config(
        self,
        config_type: ChangeType,
        metric: str = "power",
    ) -> Optional[ConfigSnapshot]:
        """
        Get best performing configuration for a metric.
        
        Args:
            config_type: Configuration type
            metric: Performance metric name
            
        Returns:
            Best performing snapshot or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM config_snapshots
            WHERE config_type = ?
            ORDER BY timestamp DESC
            LIMIT 100
        """, (config_type.value,))
        
        rows = cursor.fetchall()
        conn.close()
        
        best_snapshot = None
        best_value = None
        
        for row in rows:
            performance = json.loads(row[5]) if row[5] else {}
            if metric in performance:
                value = performance[metric]
                if best_value is None or value > best_value:
                    best_value = value
                    best_snapshot = ConfigSnapshot(
                        snapshot_id=row[0],
                        timestamp=row[1],
                        config_type=ChangeType(row[2]),
                        configuration=json.loads(row[3]),
                        telemetry_baseline=json.loads(row[4]) if row[4] else {},
                        performance_metrics=performance,
                        description=row[6] or "",
                    )
        
        return best_snapshot
    
    def analyze_change_impact(
        self,
        change: ConfigChange,
    ) -> Dict[str, Any]:
        """
        Analyze the potential impact of a configuration change.
        
        Args:
            change: Configuration change
            
        Returns:
            Analysis results
        """
        analysis = {
            "risk_level": "low",
            "warnings": [],
            "suggestions": [],
            "similar_changes": [],
            "expected_impact": {},
        }
        
        # Get similar historical changes
        similar_changes = self.get_change_history(
            category=change.category,
            parameter=change.parameter,
            limit=20,
        )
        
        # Analyze patterns
        successful_changes = [c for c in similar_changes if c.outcome == "success"]
        failed_changes = [c for c in similar_changes if c.outcome == "failure"]
        
        # Calculate risk based on historical outcomes
        if failed_changes:
            failure_rate = len(failed_changes) / len(similar_changes) if similar_changes else 0
            if failure_rate > 0.3:
                analysis["risk_level"] = "high"
                analysis["warnings"].append(
                    f"Similar changes have a {failure_rate:.0%} failure rate"
                )
        
        # Check for dangerous combinations
        warnings = self._check_dangerous_combinations(change)
        analysis["warnings"].extend(warnings)
        
        # Get suggestions from best performing configs
        suggestions = self._get_suggestions_from_history(change)
        analysis["suggestions"].extend(suggestions)
        
        return analysis
    
    def _check_dangerous_combinations(self, change: ConfigChange) -> List[str]:
        """Check for dangerous configuration combinations."""
        warnings = []
        
        # Get recent changes in same category
        recent = [c for c in self.recent_changes if c.category == change.category and c.change_id != change.change_id]
        
        # Check for dangerous timing changes
        if change.category == "Ignition Timing":
            if isinstance(change.new_value, (int, float)) and isinstance(change.old_value, (int, float)):
                advance_change = change.new_value - change.old_value
                
                # Large advance increase
                if advance_change > 10:
                    warnings.append(
                        f"Large ignition advance increase ({advance_change:.1f}°) may cause knock. "
                        "Consider smaller increments and monitor knock sensor."
                    )
                
                # Check for high boost + high timing
                boost_changes = [c for c in recent if "boost" in c.category.lower()]
                if boost_changes:
                    warnings.append(
                        "High ignition advance with boost changes requires careful monitoring. "
                        "Watch for knock and EGT."
                    )
        
        # Check for lean fuel changes
        if change.category == "Fuel VE" or "fuel" in change.parameter.lower():
            if isinstance(change.new_value, (int, float)) and isinstance(change.old_value, (int, float)):
                fuel_change = change.new_value - change.old_value
                
                # Large fuel reduction
                if fuel_change < -10:
                    warnings.append(
                        f"Large fuel reduction ({fuel_change:.1f}%) may cause lean condition. "
                        "Monitor AFR closely and ensure wideband is functioning."
                    )
        
        # Check nitrous settings
        if "nitrous" in change.category.lower():
            # Check for proper fuel enrichment
            fuel_changes = [c for c in recent if "fuel" in c.category.lower()]
            if not fuel_changes:
                warnings.append(
                    "Nitrous activation requires additional fuel. "
                    "Ensure fuel offset map is configured properly."
                )
        
        return warnings
    
    def _get_suggestions_from_history(self, change: ConfigChange) -> List[str]:
        """Get suggestions based on historical data."""
        suggestions = []
        
        # Get best performing config for this category
        config_type_map = {
            "Fuel VE": ChangeType.ECU_TUNING,
            "Ignition Timing": ChangeType.ECU_TUNING,
            "Boost Control": ChangeType.ECU_TUNING,
            "Nitrous": ChangeType.MOTORSPORT,
        }
        
        config_type = config_type_map.get(change.category, ChangeType.ECU_TUNING)
        best_config = self.get_best_performing_config(config_type)
        
        if best_config and change.parameter in best_config.configuration:
            best_value = best_config.configuration[change.parameter]
            current_value = change.new_value
            
            if isinstance(best_value, (int, float)) and isinstance(current_value, (int, float)):
                diff = best_value - current_value
                if abs(diff) > 5:  # Significant difference
                    suggestions.append(
                        f"Historical best performance was achieved with {change.parameter} = {best_value:.1f} "
                        f"(your current: {current_value:.1f}). Consider trying {best_value:.1f} for better results."
                    )
        
        return suggestions
    
    def update_change_outcome(
        self,
        change_id: str,
        outcome: str,
        notes: str = "",
    ) -> bool:
        """
        Update the outcome of a configuration change.
        
        Args:
            change_id: Change ID
            outcome: "success", "warning", or "failure"
            notes: Optional notes
            
        Returns:
            True if updated
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE config_changes
            SET outcome = ?, notes = ?
            WHERE change_id = ?
        """, (outcome, notes, change_id))
        
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        
        return updated

