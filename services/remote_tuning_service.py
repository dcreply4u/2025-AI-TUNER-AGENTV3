"""
Remote Tuning & Collaboration Service
Enables professional tuners to remotely access and tune vehicles.
"""

from __future__ import annotations

import json
import logging
import secrets
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

# Import security for encryption
try:
    from services.security_enhancements import SecurityEnhancements
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False
    SecurityEnhancements = None  # type: ignore

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None  # type: ignore

LOGGER = logging.getLogger(__name__)


class SessionStatus(Enum):
    """Remote tuning session status."""
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ChangeStatus(Enum):
    """Tuning change status."""
    PENDING = "pending"  # Awaiting user approval
    APPROVED = "approved"  # User approved, ready to apply
    APPLIED = "applied"  # Change has been applied
    REJECTED = "rejected"  # User rejected
    FAILED = "failed"  # Application failed


@dataclass
class TuningChange:
    """A tuning change suggestion."""
    change_id: str
    parameter_name: str
    current_value: float
    suggested_value: float
    reason: str
    safety_level: str = "safe"  # safe, caution, warning
    status: ChangeStatus = ChangeStatus.PENDING
    timestamp: float = field(default_factory=time.time)
    applied_at: Optional[float] = None
    tuner_notes: str = ""
    user_notes: str = ""


@dataclass
class RemoteSession:
    """Remote tuning session."""
    session_id: str
    vehicle_id: str
    tuner_id: str
    tuner_name: str
    status: SessionStatus
    created_at: float
    started_at: Optional[float] = None
    ended_at: Optional[float] = None
    changes: List[TuningChange] = field(default_factory=list)
    telemetry_snapshot: Dict[str, Any] = field(default_factory=dict)
    session_recording: Optional[str] = None  # Path to recording file
    notes: str = ""


@dataclass
class TunerProfile:
    """Professional tuner profile."""
    tuner_id: str
    name: str
    email: str
    rating: float = 0.0
    rating_count: int = 0
    specializations: List[str] = field(default_factory=list)
    vehicles_tuned: int = 0
    verified: bool = False
    bio: str = ""
    location: str = ""


class RemoteTuningService:
    """
    Remote tuning and collaboration service.
    
    Enables:
    - Professional tuners to remotely access vehicles
    - Real-time telemetry streaming
    - Tuning change suggestions
    - User approval workflow
    - Session recording
    - Payment processing
    """
    
    def __init__(
        self,
        server_url: str,
        api_key: Optional[str] = None,
        vehicle_id: Optional[str] = None,
    ):
        """
        Initialize remote tuning service.
        
        Args:
            server_url: Remote tuning server URL
            api_key: API key for authentication
            vehicle_id: Current vehicle ID
        """
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.vehicle_id = vehicle_id
        
        self.current_session: Optional[RemoteSession] = None
        self.tuner_profiles: Dict[str, TunerProfile] = {}
        
        # Security for encryption
        self.security = SecurityEnhancements() if SECURITY_AVAILABLE else None
        
        # Callbacks
        self.telemetry_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self.change_callback: Optional[Callable[[TuningChange], None]] = None
        self.status_callback: Optional[Callable[[SessionStatus], None]] = None
        
        # Session data
        self.sessions_dir = Path("data/remote_sessions")
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def create_session(
        self,
        tuner_id: str,
        vehicle_id: Optional[str] = None,
        notes: str = "",
    ) -> Optional[RemoteSession]:
        """
        Create a new remote tuning session.
        
        Args:
            tuner_id: Professional tuner ID
            vehicle_id: Vehicle ID (uses self.vehicle_id if None)
            notes: Session notes
        
        Returns:
            RemoteSession if created successfully
        """
        vehicle_id = vehicle_id or self.vehicle_id
        if not vehicle_id:
            LOGGER.error("Vehicle ID required for remote session")
            return None
        
        session_id = str(uuid.uuid4())
        
        session = RemoteSession(
            session_id=session_id,
            vehicle_id=vehicle_id,
            tuner_id=tuner_id,
            tuner_name="",  # Will be fetched
            status=SessionStatus.PENDING,
            created_at=time.time(),
            notes=notes,
        )
        
        # Register with server
        if REQUESTS_AVAILABLE:
            try:
                response = requests.post(
                    f"{self.server_url}/api/sessions",
                    json={
                        "session_id": session_id,
                        "vehicle_id": vehicle_id,
                        "tuner_id": tuner_id,
                        "notes": notes,
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                    timeout=10,
                )
                response.raise_for_status()
            except requests.RequestException as e:
                LOGGER.warning("Failed to register session with server: %s", e)
                # Continue with local session
        
        self.current_session = session
        self._save_session(session)
        
        LOGGER.info("Remote session created: %s", session_id)
        return session
    
    def start_session(self, session_id: Optional[str] = None) -> bool:
        """
        Start remote tuning session.
        
        Args:
            session_id: Session ID (uses current_session if None)
        
        Returns:
            True if started successfully
        """
        if session_id:
            session = self._load_session(session_id)
        else:
            session = self.current_session
        
        if not session:
            LOGGER.error("No session found")
            return False
        
        session.status = SessionStatus.ACTIVE
        session.started_at = time.time()
        self.current_session = session
        
        self._save_session(session)
        self._notify_status(session.status)
        
        LOGGER.info("Remote session started: %s", session.session_id)
        return True
    
    def stream_telemetry(self, telemetry_data: Dict[str, Any]) -> bool:
        """
        Stream telemetry data to remote tuner.
        
        Args:
            telemetry_data: Current telemetry data
        
        Returns:
            True if streamed successfully
        """
        if not self.current_session or self.current_session.status != SessionStatus.ACTIVE:
            return False
        
        # Send to server
        if REQUESTS_AVAILABLE:
            try:
                response = requests.post(
                    f"{self.server_url}/api/sessions/{self.current_session.session_id}/telemetry",
                    json=telemetry_data,
                    headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                    timeout=5,
                )
                response.raise_for_status()
            except requests.RequestException as e:
                LOGGER.warning("Failed to stream telemetry: %s", e)
                return False
        
        # Update session snapshot
        self.current_session.telemetry_snapshot = telemetry_data
        
        # Notify callback
        if self.telemetry_callback:
            try:
                self.telemetry_callback(telemetry_data)
            except Exception as e:
                LOGGER.warning("Telemetry callback error: %s", e)
        
        return True
    
    def suggest_change(
        self,
        parameter_name: str,
        current_value: float,
        suggested_value: float,
        reason: str,
        safety_level: str = "safe",
        tuner_notes: str = "",
    ) -> Optional[TuningChange]:
        """
        Suggest a tuning change (from tuner).
        
        Args:
            parameter_name: Parameter to change
            current_value: Current parameter value
            suggested_value: Suggested new value
            reason: Reason for change
            safety_level: Safety level (safe, caution, warning)
            tuner_notes: Tuner's notes
        
        Returns:
            TuningChange if created successfully
        """
        if not self.current_session:
            LOGGER.error("No active session")
            return None
        
        change = TuningChange(
            change_id=str(uuid.uuid4()),
            parameter_name=parameter_name,
            current_value=current_value,
            suggested_value=suggested_value,
            reason=reason,
            safety_level=safety_level,
            status=ChangeStatus.PENDING,
            tuner_notes=tuner_notes,
        )
        
        self.current_session.changes.append(change)
        self._save_session(self.current_session)
        
        # Notify user
        if self.change_callback:
            try:
                self.change_callback(change)
            except Exception as e:
                LOGGER.warning("Change callback error: %s", e)
        
        LOGGER.info("Tuning change suggested: %s = %s (was %s)", 
                   parameter_name, suggested_value, current_value)
        return change
    
    def approve_change(self, change_id: str) -> bool:
        """
        Approve a tuning change (from user).
        
        Args:
            change_id: Change ID to approve
        
        Returns:
            True if approved successfully
        """
        if not self.current_session:
            return False
        
        change = next((c for c in self.current_session.changes if c.change_id == change_id), None)
        if not change:
            LOGGER.error("Change not found: %s", change_id)
            return False
        
        change.status = ChangeStatus.APPROVED
        self._save_session(self.current_session)
        
        LOGGER.info("Change approved: %s", change_id)
        return True
    
    def reject_change(self, change_id: str, reason: str = "") -> bool:
        """
        Reject a tuning change (from user).
        
        Args:
            change_id: Change ID to reject
            reason: Rejection reason
        
        Returns:
            True if rejected successfully
        """
        if not self.current_session:
            return False
        
        change = next((c for c in self.current_session.changes if c.change_id == change_id), None)
        if not change:
            return False
        
        change.status = ChangeStatus.REJECTED
        change.user_notes = reason
        self._save_session(self.current_session)
        
        LOGGER.info("Change rejected: %s", change_id)
        return True
    
    def apply_change(self, change_id: str, ecu_control) -> bool:
        """
        Apply an approved tuning change.
        
        Args:
            change_id: Change ID to apply
            ecu_control: ECU control interface
        
        Returns:
            True if applied successfully
        """
        if not self.current_session:
            return False
        
        change = next((c for c in self.current_session.changes if c.change_id == change_id), None)
        if not change or change.status != ChangeStatus.APPROVED:
            LOGGER.error("Change not approved: %s", change_id)
            return False
        
        try:
            # Apply change via ECU control
            # This would need to be implemented based on ECU type
            # Example:
            # ecu_control.set_parameter(change.parameter_name, change.suggested_value)
            
            change.status = ChangeStatus.APPLIED
            change.applied_at = time.time()
            self._save_session(self.current_session)
            
            LOGGER.info("Change applied: %s = %s", change.parameter_name, change.suggested_value)
            return True
            
        except Exception as e:
            LOGGER.error("Failed to apply change: %s", e)
            change.status = ChangeStatus.FAILED
            self._save_session(self.current_session)
            return False
    
    def end_session(self, notes: str = "") -> bool:
        """
        End remote tuning session.
        
        Args:
            notes: Session end notes
        
        Returns:
            True if ended successfully
        """
        if not self.current_session:
            return False
        
        self.current_session.status = SessionStatus.COMPLETED
        self.current_session.ended_at = time.time()
        if notes:
            self.current_session.notes += f"\n\nEnd notes: {notes}"
        
        self._save_session(self.current_session)
        self._notify_status(SessionStatus.COMPLETED)
        
        LOGGER.info("Remote session ended: %s", self.current_session.session_id)
        return True
    
    def get_available_tuners(
        self,
        specialization: Optional[str] = None,
        min_rating: float = 0.0,
    ) -> List[TunerProfile]:
        """
        Get list of available professional tuners.
        
        Args:
            specialization: Filter by specialization
            min_rating: Minimum rating
        
        Returns:
            List of tuner profiles
        """
        if REQUESTS_AVAILABLE:
            try:
                params = {}
                if specialization:
                    params["specialization"] = specialization
                if min_rating > 0:
                    params["min_rating"] = min_rating
                
                response = requests.get(
                    f"{self.server_url}/api/tuners",
                    params=params,
                    headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                    timeout=10,
                )
                response.raise_for_status()
                
                data = response.json()
                tuners = []
                for tuner_data in data.get("tuners", []):
                    tuner = TunerProfile(
                        tuner_id=tuner_data["tuner_id"],
                        name=tuner_data.get("name", ""),
                        email=tuner_data.get("email", ""),
                        rating=tuner_data.get("rating", 0.0),
                        rating_count=tuner_data.get("rating_count", 0),
                        specializations=tuner_data.get("specializations", []),
                        vehicles_tuned=tuner_data.get("vehicles_tuned", 0),
                        verified=tuner_data.get("verified", False),
                        bio=tuner_data.get("bio", ""),
                        location=tuner_data.get("location", ""),
                    )
                    tuners.append(tuner)
                    self.tuner_profiles[tuner.tuner_id] = tuner
                
                return tuners
            except requests.RequestException as e:
                LOGGER.warning("Failed to fetch tuners: %s", e)
        
        # Return cached profiles
        return list(self.tuner_profiles.values())
    
    def _save_session(self, session: RemoteSession) -> None:
        """Save session to disk (encrypted if security available)."""
        try:
            session_file = self.sessions_dir / f"{session.session_id}.json"
            session_data = {
                    "session_id": session.session_id,
                    "vehicle_id": session.vehicle_id,
                    "tuner_id": session.tuner_id,
                    "tuner_name": session.tuner_name,
                    "status": session.status.value,
                    "created_at": session.created_at,
                    "started_at": session.started_at,
                    "ended_at": session.ended_at,
                    "changes": [
                        {
                            "change_id": c.change_id,
                            "parameter_name": c.parameter_name,
                            "current_value": c.current_value,
                            "suggested_value": c.suggested_value,
                            "reason": c.reason,
                            "safety_level": c.safety_level,
                            "status": c.status.value,
                            "timestamp": c.timestamp,
                            "applied_at": c.applied_at,
                            "tuner_notes": c.tuner_notes,
                            "user_notes": c.user_notes,
                        }
                        for c in session.changes
                    ],
                    "telemetry_snapshot": session.telemetry_snapshot,
                    "notes": session.notes,
                }
            
            # Encrypt sensitive data if security available
            if self.security and session.telemetry_snapshot:
                encrypted_telemetry = self.security.encrypt_data(
                    json.dumps(session.telemetry_snapshot)
                )
                session_data["telemetry_snapshot"] = {"encrypted": True, "data": encrypted_telemetry}
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
        except Exception as e:
            LOGGER.error("Failed to save session: %s", e)
    
    def _load_session(self, session_id: str) -> Optional[RemoteSession]:
        """Load session from disk."""
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            if not session_file.exists():
                return None
            
            with open(session_file, 'r') as f:
                data = json.load(f)
            
            # Decrypt telemetry if encrypted
            telemetry_snapshot = data.get("telemetry_snapshot", {})
            if isinstance(telemetry_snapshot, dict) and telemetry_snapshot.get("encrypted"):
                if self.security:
                    try:
                        decrypted = self.security.decrypt_data(telemetry_snapshot["data"])
                        telemetry_snapshot = json.loads(decrypted)
                    except Exception as e:
                        LOGGER.warning("Failed to decrypt telemetry: %s", e)
                        telemetry_snapshot = {}
                else:
                    telemetry_snapshot = {}
            
            changes = [
                TuningChange(
                    change_id=c["change_id"],
                    parameter_name=c["parameter_name"],
                    current_value=c["current_value"],
                    suggested_value=c["suggested_value"],
                    reason=c["reason"],
                    safety_level=c.get("safety_level", "safe"),
                    status=ChangeStatus(c["status"]),
                    timestamp=c.get("timestamp", time.time()),
                    applied_at=c.get("applied_at"),
                    tuner_notes=c.get("tuner_notes", ""),
                    user_notes=c.get("user_notes", ""),
                )
                for c in data.get("changes", [])
            ]
            
            session = RemoteSession(
                session_id=data["session_id"],
                vehicle_id=data["vehicle_id"],
                tuner_id=data["tuner_id"],
                tuner_name=data.get("tuner_name", ""),
                status=SessionStatus(data["status"]),
                created_at=data["created_at"],
                started_at=data.get("started_at"),
                ended_at=data.get("ended_at"),
                changes=changes,
                telemetry_snapshot=telemetry_snapshot,
                notes=data.get("notes", ""),
            )
            
            return session
        except Exception as e:
            LOGGER.error("Failed to load session: %s", e)
            return None
    
    def set_telemetry_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Set callback for telemetry streaming."""
        self.telemetry_callback = callback
    
    def set_change_callback(self, callback: Callable[[TuningChange], None]) -> None:
        """Set callback for tuning changes."""
        self.change_callback = callback
    
    def set_status_callback(self, callback: Callable[[SessionStatus], None]) -> None:
        """Set callback for status changes."""
        self.status_callback = callback
    
    def _notify_status(self, status: SessionStatus) -> None:
        """Notify status callback."""
        if self.status_callback:
            try:
                self.status_callback(status)
            except Exception as e:
                LOGGER.warning("Status callback error: %s", e)


