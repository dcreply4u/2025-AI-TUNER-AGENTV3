"""
Input Validation Models
Pydantic models for API request/response validation.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator, root_validator


class RecordType(str, Enum):
    """Record type for blockchain."""
    SPEED = "speed"
    TIME = "time"
    POWER = "power"
    TORQUE = "torque"
    LAP_TIME = "lap_time"
    QUARTER_MILE = "quarter_mile"
    CUSTOM = "custom"


class TuningMode(str, Enum):
    """Tuning mode."""
    SAFE = "safe"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    ADAPTIVE = "adaptive"


class OptimizationGoal(str, Enum):
    """Optimization goal."""
    MAX_POWER = "max_power"
    MAX_TORQUE = "max_torque"
    FUEL_EFFICIENCY = "fuel_efficiency"
    BALANCED = "balanced"
    TRACK_PERFORMANCE = "track_performance"
    STREET_PERFORMANCE = "street_performance"


# ============================================================================
# OTA Update Models
# ============================================================================

class OTACheckRequest(BaseModel):
    """OTA update check request."""
    force: bool = Field(default=False, description="Force check even if recently checked")


class OTADownloadRequest(BaseModel):
    """OTA update download request."""
    version: str = Field(..., description="Version to download")
    
    @validator("version")
    def validate_version(cls, v):
        if not v or len(v) > 50:
            raise ValueError("Invalid version format")
        return v


# ============================================================================
# Remote Tuning Models
# ============================================================================

class CreateSessionRequest(BaseModel):
    """Create remote tuning session request."""
    tuner_id: str = Field(..., min_length=1, max_length=100)
    vehicle_id: str = Field(..., min_length=1, max_length=100)
    notes: str = Field(default="", max_length=1000)
    
    @validator("tuner_id", "vehicle_id")
    def validate_id(cls, v):
        if not v.isalnum() and "_" not in v and "-" not in v:
            raise ValueError("ID must be alphanumeric with underscores or hyphens")
        return v


class SuggestChangeRequest(BaseModel):
    """Suggest tuning change request."""
    parameter_name: str = Field(..., min_length=1, max_length=100)
    current_value: float = Field(..., ge=-10000, le=10000)
    suggested_value: float = Field(..., ge=-10000, le=10000)
    reason: str = Field(..., min_length=1, max_length=500)
    safety_level: str = Field(default="safe", pattern="^(safe|caution|warning)$")
    tuner_notes: str = Field(default="", max_length=1000)


class ApproveChangeRequest(BaseModel):
    """Approve tuning change request."""
    change_id: str = Field(..., min_length=1, max_length=100)


# ============================================================================
# AI Auto-Tuning Models
# ============================================================================

class AutoTuningRequest(BaseModel):
    """AI auto-tuning request."""
    tuning_mode: TuningMode = Field(default=TuningMode.MODERATE)
    optimization_goal: OptimizationGoal = Field(default=OptimizationGoal.BALANCED)
    current_telemetry: Dict[str, Any] = Field(..., description="Current telemetry data")
    current_parameters: Dict[str, float] = Field(..., description="Current ECU parameters")
    vehicle_profile: Optional[Dict[str, Any]] = Field(default=None)
    conditions: Optional[Dict[str, Any]] = Field(default=None)
    
    @validator("current_parameters")
    def validate_parameters(cls, v):
        if not v:
            raise ValueError("Current parameters required")
        # Validate parameter values are reasonable
        for key, value in v.items():
            if not isinstance(value, (int, float)):
                raise ValueError(f"Parameter {key} must be numeric")
            if abs(value) > 100000:
                raise ValueError(f"Parameter {key} value out of range")
        return v


# ============================================================================
# Social Platform Models
# ============================================================================

class SubmitRunRequest(BaseModel):
    """Submit run request."""
    track_name: str = Field(..., min_length=1, max_length=100)
    time_seconds: float = Field(..., gt=0, le=3600, description="Run time in seconds")
    telemetry_data: Optional[Dict[str, Any]] = Field(default=None)
    
    @validator("track_name")
    def validate_track_name(cls, v):
        # Sanitize track name
        if not v.strip():
            raise ValueError("Track name cannot be empty")
        return v.strip()[:100]


class LeaderboardRequest(BaseModel):
    """Leaderboard request."""
    category: str = Field(..., min_length=1, max_length=50)
    limit: int = Field(default=100, ge=1, le=1000)


# ============================================================================
# Predictive Parts Models
# ============================================================================

class MonitorPartRequest(BaseModel):
    """Monitor part request."""
    part_id: str = Field(..., min_length=1, max_length=100)
    telemetry_data: Dict[str, Any] = Field(..., description="Telemetry data")
    current_mileage: float = Field(..., ge=0, le=1000000)


class CreateOrderRequest(BaseModel):
    """Create parts order request."""
    part_id: str = Field(..., min_length=1, max_length=100)
    prediction_id: Optional[str] = Field(default=None, max_length=100)


# ============================================================================
# Fleet Management Models
# ============================================================================

class AddVehicleRequest(BaseModel):
    """Add vehicle to fleet request."""
    vehicle_id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)
    make: str = Field(..., min_length=1, max_length=50)
    model: str = Field(..., min_length=1, max_length=50)
    year: int = Field(..., ge=1900, le=2100)
    configuration: Optional[Dict[str, Any]] = Field(default=None)


class RecordRunRequest(BaseModel):
    """Record run request."""
    vehicle_id: str = Field(..., min_length=1, max_length=100)
    time_seconds: Optional[float] = Field(default=None, gt=0, le=3600)
    speed: Optional[float] = Field(default=None, ge=0, le=500)
    distance: Optional[float] = Field(default=None, ge=0, le=1000)


# ============================================================================
# Blockchain Records Models
# ============================================================================

class CreateRecordRequest(BaseModel):
    """Create blockchain record request."""
    record_type: RecordType
    value: float = Field(..., ge=-1000000, le=1000000)
    unit: str = Field(..., min_length=1, max_length=20)
    vehicle_id: str = Field(..., min_length=1, max_length=100)
    vehicle_name: str = Field(..., min_length=1, max_length=100)
    location: Optional[str] = Field(default=None, max_length=200)
    conditions: Optional[Dict[str, Any]] = Field(default=None)
    telemetry_data: Optional[Dict[str, Any]] = Field(default=None)


class VerifyRecordRequest(BaseModel):
    """Verify record request."""
    record_id: str = Field(..., min_length=1, max_length=100)


# ============================================================================
# AI Racing Coach Models
# ============================================================================

class StartLapRequest(BaseModel):
    """Start lap request."""
    pass  # No parameters needed


class ProcessTelemetryRequest(BaseModel):
    """Process telemetry for coaching request."""
    telemetry_data: Dict[str, Any] = Field(..., description="Telemetry data")
    gps_data: Optional[Dict[str, Any]] = Field(default=None, description="GPS data")


# ============================================================================
# Response Models
# ============================================================================

class ErrorResponse(BaseModel):
    """Error response."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Error detail")
    code: Optional[str] = Field(default=None, description="Error code")


class SuccessResponse(BaseModel):
    """Success response."""
    success: bool = Field(default=True)
    message: Optional[str] = Field(default=None)
    data: Optional[Dict[str, Any]] = Field(default=None)


