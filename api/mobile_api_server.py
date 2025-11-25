"""
Mobile API Server for TelemetryIQ
Comprehensive REST API and WebSocket server for Android/iOS mobile app integration
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

# Import authentication and rate limiting
from api.auth_middleware import require_auth, require_role, require_permission
from api.rate_limiter import rate_limit
from api.input_validation import (
    OTACheckRequest, CreateSessionRequest, SuggestChangeRequest,
    SubmitRunRequest, LeaderboardRequest, CreateRecordRequest,
    AutoTuningRequest, AddVehicleRequest, RecordRunRequest,
)

LOGGER = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    from fastapi_jwt_auth import AuthJWT
    from fastapi_jwt_auth.exceptions import AuthJWTException
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    AuthJWT = None  # type: ignore

# Create FastAPI app
app = FastAPI(
    title="TelemetryIQ Mobile API",
    version="1.0.0",
    description="REST API and WebSocket server for mobile app integration"
)

# CORS middleware for mobile apps
# SECURITY: Restrict origins in production
_cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
if _cors_origins == ["*"] and os.getenv("DEBUG_MODE", "true").lower() not in {"1", "true", "yes"}:
    # In production, require explicit CORS origins
    import warnings
    warnings.warn(
        "CORS_ORIGINS not set! Allowing all origins is a security risk. "
        "Set CORS_ORIGINS environment variable to specific domains in production.",
        UserWarning
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,  # Restrict to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances (will be initialized on startup)
telemetry_data: Dict[str, float] = {}
active_websockets: List[WebSocket] = []
config_monitor = None
ai_advisor = None
backup_manager = None
hardware_manager = None
camera_manager = None


# ============================================================================
# Request/Response Models
# ============================================================================

class TelemetryRequest(BaseModel):
    """Telemetry data request."""
    sensors: Optional[List[str]] = None  # Specific sensors, or all if None


class ConfigChangeRequest(BaseModel):
    """Configuration change request."""
    change_type: str  # "ecu_tuning", "protection", "motorsport", etc.
    category: str
    parameter: str
    new_value: Any
    old_value: Optional[Any] = None


class AIQuestionRequest(BaseModel):
    """AI advisor question request."""
    question: str
    context: Optional[Dict[str, Any]] = None


class BackupRequest(BaseModel):
    """Backup creation request."""
    file_path: str
    backup_type: str
    description: Optional[str] = None


class RevertRequest(BaseModel):
    """Revert to backup request."""
    backup_id: str


# ============================================================================
# WebSocket Manager
# ============================================================================

class WebSocketManager:
    """Manages WebSocket connections for real-time data."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        LOGGER.info("WebSocket connected. Total connections: %d", len(self.active_connections))
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        LOGGER.info("WebSocket disconnected. Total connections: %d", len(self.active_connections))
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                LOGGER.error("Error sending WebSocket message: %s", e)
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)


ws_manager = WebSocketManager()

# Import and include theft tracking router
try:
    from api.theft_tracking_api import router as theft_tracking_router
    app.include_router(theft_tracking_router)
    THEFT_TRACKING_AVAILABLE = True
except ImportError:
    THEFT_TRACKING_AVAILABLE = False
    LOGGER.warning("Theft tracking API not available")

# Import and include remote access router
try:
    from api.remote_access_api import router as remote_access_router, initialize_remote_access
    app.include_router(remote_access_router)
    REMOTE_ACCESS_AVAILABLE = True
except ImportError:
    REMOTE_ACCESS_AVAILABLE = False
    LOGGER.warning("Remote access API not available")


# ============================================================================
# Startup/Shutdown
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global config_monitor, ai_advisor, backup_manager, hardware_manager, camera_manager
    
    try:
        # Initialize configuration monitor
        from services.config_version_control import ConfigVersionControl
        from services.intelligent_config_monitor import IntelligentConfigMonitor
        config_vc = ConfigVersionControl()
        config_monitor = IntelligentConfigMonitor(config_vc=config_vc)
    except Exception as e:
        LOGGER.warning("Failed to initialize config monitor: %s", e)
    
    try:
        # Initialize AI advisor
        from services.ai_advisor_q import AIAdvisorQ
        ai_advisor = AIAdvisorQ(use_llm=False, config_monitor=config_monitor)
    except Exception as e:
        LOGGER.warning("Failed to initialize AI advisor: %s", e)
    
    try:
        # Initialize backup manager
        from services.backup_manager import BackupManager
        backup_manager = BackupManager()
    except Exception as e:
        LOGGER.warning("Failed to initialize backup manager: %s", e)
    
    try:
        # Initialize hardware manager
        from services.hardware_interface_manager import HardwareInterfaceManager
        hardware_manager = HardwareInterfaceManager()
    except Exception as e:
        LOGGER.warning("Failed to initialize hardware manager: %s", e)
    
    try:
        # Initialize camera manager
        from services.usb_camera_manager import USBCameraManager
        camera_manager = USBCameraManager()
        camera_manager.detect_all_cameras()
    except Exception as e:
        LOGGER.warning("Failed to initialize camera manager: %s", e)
    
    # Start telemetry broadcast task
    asyncio.create_task(broadcast_telemetry())
    
    # Initialize remote access service
    if REMOTE_ACCESS_AVAILABLE:
        try:
            from services.remote_access_service import RemoteAccessConfig
            initialize_remote_access(RemoteAccessConfig(enabled=True))
            LOGGER.info("Remote access service initialized")
        except Exception as e:
            LOGGER.warning("Failed to initialize remote access: %s", e)
    
    LOGGER.info("Mobile API server started")


async def broadcast_telemetry():
    """Background task to broadcast telemetry data via WebSocket."""
    while True:
        if telemetry_data and ws_manager.active_connections:
            try:
                await ws_manager.broadcast({
                    "type": "telemetry",
                    "timestamp": time.time(),
                    "data": telemetry_data,
                })
            except Exception as e:
                LOGGER.error("Error broadcasting telemetry: %s", e)
        
        await asyncio.sleep(0.1)  # 10 Hz update rate


# ============================================================================
# Health & Status
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "TelemetryIQ Mobile API",
        "version": "1.0.0",
        "status": "online"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {
            "config_monitor": config_monitor is not None,
            "ai_advisor": ai_advisor is not None,
            "backup_manager": backup_manager is not None,
            "hardware_manager": hardware_manager is not None,
            "camera_manager": camera_manager is not None,
        }
    }


# ============================================================================
# Telemetry Endpoints
# ============================================================================

@app.get("/api/telemetry/current")
async def get_current_telemetry(sensors: Optional[str] = None):
    """
    Get current telemetry data.
    
    Args:
        sensors: Comma-separated list of sensor names (optional)
    """
    if sensors:
        sensor_list = [s.strip() for s in sensors.split(",")]
        filtered_data = {k: v for k, v in telemetry_data.items() if k in sensor_list}
        return {"timestamp": time.time(), "data": filtered_data}
    
    return {"timestamp": time.time(), "data": telemetry_data}


@app.get("/api/telemetry/sensors")
async def list_sensors():
    """List all available sensors."""
    return {
        "sensors": list(telemetry_data.keys()),
        "count": len(telemetry_data)
    }


@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    """WebSocket endpoint for real-time telemetry streaming."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": time.time()})
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# ============================================================================
# Configuration Endpoints
# ============================================================================

@app.post("/api/config/change")
async def apply_config_change(request: ConfigChangeRequest):
    """
    Apply a configuration change.
    
    Returns warnings and suggestions from AI advisor.
    """
    if not config_monitor:
        raise HTTPException(status_code=503, detail="Configuration monitor not available")
    
    try:
        from services.config_version_control import ChangeType
        
        change_type_map = {
            "ecu_tuning": ChangeType.ECU_TUNING,
            "protection": ChangeType.PROTECTION,
            "motorsport": ChangeType.MOTORSPORT,
            "transmission": ChangeType.TRANSMISSION,
            "sensor": ChangeType.SENSOR,
            "hardware": ChangeType.HARDWARE,
            "camera": ChangeType.CAMERA,
        }
        
        change_type = change_type_map.get(request.change_type, ChangeType.ECU_TUNING)
        
        # Monitor change and get warnings
        warnings = config_monitor.monitor_change(
            change_type=change_type,
            category=request.category,
            parameter=request.parameter,
            old_value=request.old_value,
            new_value=request.new_value,
            telemetry=telemetry_data,
        )
        
        # Convert warnings to JSON-serializable format
        warnings_data = []
        for warning in warnings:
            warnings_data.append({
                "severity": warning.severity,
                "message": warning.message,
                "suggestion": warning.suggestion,
                "alternative_value": warning.alternative_value,
                "reasoning": warning.reasoning,
            })
        
        return {
            "status": "success",
            "warnings": warnings_data,
            "change_applied": True,
        }
        
    except Exception as e:
        LOGGER.error("Error applying config change: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config/history")
async def get_config_history(category: Optional[str] = None, limit: int = 50):
    """Get configuration change history."""
    if not config_monitor or not config_monitor.config_vc:
        raise HTTPException(status_code=503, detail="Configuration version control not available")
    
    changes = config_monitor.config_vc.get_change_history(category=category, limit=limit)
    
    changes_data = []
    for change in changes:
        changes_data.append({
            "change_id": change.change_id,
            "timestamp": change.timestamp,
            "category": change.category,
            "parameter": change.parameter,
            "old_value": change.old_value,
            "new_value": change.new_value,
            "severity": change.severity.value,
            "outcome": change.outcome,
        })
    
    return {"changes": changes_data, "count": len(changes_data)}


@app.get("/api/config/best")
async def get_best_config(config_type: str = "ecu_tuning", metric: str = "power"):
    """Get best performing configuration for a metric."""
    if not config_monitor or not config_monitor.config_vc:
        raise HTTPException(status_code=503, detail="Configuration version control not available")
    
    try:
        from services.config_version_control import ChangeType
        
        change_type_map = {
            "ecu_tuning": ChangeType.ECU_TUNING,
            "motorsport": ChangeType.MOTORSPORT,
        }
        
        change_type = change_type_map.get(config_type, ChangeType.ECU_TUNING)
        best_config = config_monitor.config_vc.get_best_performing_config(change_type, metric)
        
        if best_config:
            return {
                "snapshot_id": best_config.snapshot_id,
                "timestamp": best_config.timestamp,
                "configuration": best_config.configuration,
                "performance_metrics": best_config.performance_metrics,
                "description": best_config.description,
            }
        else:
            return {"message": "No performance data available"}
    except Exception as e:
        LOGGER.error("Error getting best config: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AI Advisor Endpoints
# ============================================================================

@app.post("/api/ai/ask")
async def ask_ai_advisor(request: AIQuestionRequest):
    """Ask AI advisor Q a question."""
    if not ai_advisor:
        raise HTTPException(status_code=503, detail="AI advisor not available")
    
    try:
        response = ai_advisor.ask(request.question, context=request.context)
        return {
            "response": response,
            "timestamp": time.time(),
        }
    except Exception as e:
        LOGGER.error("Error asking AI advisor: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai/suggestions")
async def get_ai_suggestions(partial: str = ""):
    """Get AI advisor question suggestions."""
    if not ai_advisor:
        raise HTTPException(status_code=503, detail="AI advisor not available")
    
    suggestions = ai_advisor.get_suggestions(partial)
    return {"suggestions": suggestions}


# ============================================================================
# Backup & Version Control Endpoints
# ============================================================================

@app.post("/api/backup/create")
async def create_backup(request: BackupRequest):
    """Create a backup of a file."""
    if not backup_manager:
        raise HTTPException(status_code=503, detail="Backup manager not available")
    
    try:
        from services.backup_manager import BackupType
        
        backup_type_map = {
            "ecu_tuning": BackupType.ECU_TUNING,
            "ecu_calibration": BackupType.ECU_CALIBRATION,
            "ecu_binary": BackupType.ECU_BINARY,
            "configuration": BackupType.CONFIGURATION,
            "global": BackupType.GLOBAL,
        }
        
        backup_type = backup_type_map.get(request.backup_type, BackupType.GLOBAL)
        
        backup = backup_manager.create_backup(
            request.file_path,
            backup_type,
            description=request.description or "Mobile app backup",
            force=True,
        )
        
        if backup:
            return {
                "status": "success",
                "backup_id": backup.backup_id,
                "timestamp": backup.timestamp,
                "file_path": backup.file_path,
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create backup")
    except Exception as e:
        LOGGER.error("Error creating backup: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/backup/list")
async def list_backups(file_path: Optional[str] = None):
    """List backups for a file."""
    if not backup_manager:
        raise HTTPException(status_code=503, detail="Backup manager not available")
    
    if not file_path:
        raise HTTPException(status_code=400, detail="file_path parameter required")
    
    backups = backup_manager.get_backups(file_path)
    
    backups_data = []
    for backup in backups:
        backups_data.append({
            "backup_id": backup.backup_id,
            "timestamp": backup.timestamp,
            "description": backup.description,
            "file_size": backup.file_size,
            "file_hash": backup.file_hash[:16],  # Shortened
        })
    
    return {"backups": backups_data, "count": len(backups_data)}


@app.post("/api/backup/revert")
async def revert_backup(request: RevertRequest):
    """Revert a file to a backup."""
    if not backup_manager:
        raise HTTPException(status_code=503, detail="Backup manager not available")
    
    # Find backup by ID
    # Note: This is simplified - in production, you'd need a better lookup mechanism
    # For now, we'll need the file_path in the request
    raise HTTPException(status_code=501, detail="Revert endpoint requires file_path - use /api/backup/revert/{file_path}/{backup_id}")


@app.post("/api/backup/revert/{file_path:path}/{backup_id}")
async def revert_backup_by_id(file_path: str, backup_id: str):
    """Revert a file to a specific backup."""
    if not backup_manager:
        raise HTTPException(status_code=503, detail="Backup manager not available")
    
    backups = backup_manager.get_backups(file_path)
    backup = next((b for b in backups if b.backup_id == backup_id), None)
    
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    success = backup_manager.revert_to_backup(backup, create_backup=True)
    
    if success:
        return {"status": "success", "message": "File reverted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to revert file")


# ============================================================================
# Hardware Endpoints
# ============================================================================

@app.get("/api/hardware/interfaces")
async def list_hardware_interfaces():
    """List all detected hardware interfaces."""
    if not hardware_manager:
        raise HTTPException(status_code=503, detail="Hardware manager not available")
    
    interfaces = hardware_manager.list_interfaces()
    
    interfaces_data = []
    for interface in interfaces:
        interfaces_data.append({
            "interface_id": interface.interface_id,
            "interface_type": interface.interface_type.value,
            "board_type": interface.board_type.value if interface.board_type else None,
            "name": interface.name,
            "description": interface.description,
            "connected": interface.connected,
            "gpio_pins": len(interface.gpio_pins),
        })
    
    return {"interfaces": interfaces_data, "count": len(interfaces_data)}


@app.get("/api/hardware/gpio/{interface_id}/{pin}")
async def read_gpio(interface_id: str, pin: int):
    """Read GPIO pin value."""
    if not hardware_manager:
        raise HTTPException(status_code=503, detail="Hardware manager not available")
    
    value = hardware_manager.read_gpio(interface_id, pin)
    
    if value is None:
        raise HTTPException(status_code=404, detail="GPIO pin not found or not configured")
    
    return {"interface_id": interface_id, "pin": pin, "value": value}


@app.post("/api/hardware/gpio/{interface_id}/{pin}")
async def write_gpio(interface_id: str, pin: int, value: bool):
    """Write GPIO pin value."""
    if not hardware_manager:
        raise HTTPException(status_code=503, detail="Hardware manager not available")
    
    success = hardware_manager.write_gpio(interface_id, pin, value)
    
    if success:
        return {"status": "success", "interface_id": interface_id, "pin": pin, "value": value}
    else:
        raise HTTPException(status_code=500, detail="Failed to write GPIO pin")


# ============================================================================
# Camera Endpoints
# ============================================================================

@app.get("/api/cameras")
async def list_cameras():
    """List all detected USB cameras."""
    if not camera_manager:
        raise HTTPException(status_code=503, detail="Camera manager not available")
    
    cameras = camera_manager.list_cameras()
    
    cameras_data = []
    for camera in cameras:
        cameras_data.append({
            "device_id": camera.device_id,
            "vendor": camera.vendor.value if hasattr(camera.vendor, 'value') else str(camera.vendor),
            "model": camera.model,
            "driver": camera.driver.value if hasattr(camera.driver, 'value') else str(camera.driver),
            "max_fps": camera.max_fps,
            "supported_resolutions": camera.supported_resolutions,
        })
    
    return {"cameras": cameras_data, "count": len(cameras_data)}


@app.get("/api/cameras/{device_id}/preview")
async def get_camera_preview(device_id: str):
    """Get camera preview frame (JPEG)."""
    if not camera_manager:
        raise HTTPException(status_code=503, detail="Camera manager not available")
    
    try:
        import cv2
        import base64
        from io import BytesIO
        
        cap = camera_manager.open_camera(device_id, width=640, height=480, fps=30)
        if not cap:
            raise HTTPException(status_code=404, detail="Camera not found or cannot be opened")
        
        ret, frame = cap.read()
        if not ret:
            raise HTTPException(status_code=500, detail="Failed to capture frame")
        
        # Encode frame as JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame_bytes = buffer.tobytes()
        
        return StreamingResponse(
            BytesIO(frame_bytes),
            media_type="image/jpeg",
            headers={"Cache-Control": "no-cache"}
        )
    except ImportError:
        raise HTTPException(status_code=503, detail="OpenCV not available")
    except Exception as e:
        LOGGER.error("Error getting camera preview: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# System Status Endpoints
# ============================================================================

@app.get("/api/system/status")
async def get_system_status():
    """Get overall system status."""
    status = {
        "timestamp": time.time(),
        "telemetry": {
            "sensors_count": len(telemetry_data),
            "last_update": max(telemetry_data.values()) if telemetry_data else None,
        },
        "websockets": {
            "active_connections": len(ws_manager.active_connections),
        },
        "services": {
            "config_monitor": config_monitor is not None,
            "ai_advisor": ai_advisor is not None,
            "backup_manager": backup_manager is not None,
            "hardware_manager": hardware_manager is not None,
            "camera_manager": camera_manager is not None,
        },
    }
    
    return status


# ============================================================================
# Telemetry Update Endpoint (for desktop app to push data)
# ============================================================================

@app.post("/api/telemetry/update")
async def update_telemetry(data: Dict[str, float]):
    """
    Update telemetry data (called by desktop app).
    
    This endpoint allows the desktop application to push telemetry data
    to the API server for mobile app access and remote viewers.
    """
    global telemetry_data
    telemetry_data.update(data)
    
    # Broadcast to WebSocket clients (mobile app)
    if ws_manager.active_connections:
        await ws_manager.broadcast({
            "type": "telemetry",
            "timestamp": time.time(),
            "data": data,
        })
    
    # Update remote access service if available
    if REMOTE_ACCESS_AVAILABLE:
        try:
            from api.remote_access_api import remote_service
            if remote_service:
                await remote_service.update_telemetry(data)
        except Exception as e:
            LOGGER.debug("Error updating remote access telemetry: %s", e)
    
    return {"status": "updated", "sensors_count": len(telemetry_data)}


# ============================================================================
# Enhanced Mobile API Endpoints (New Competitive Advantages)
# ============================================================================

@app.get("/api/ota/check")
@rate_limit("/api/ota/check")
@require_auth
async def check_ota_updates(request: Request):
    """Check for OTA updates."""
    try:
        from services.ota_update_service import OTAUpdateService
        import config
        
        ota_service = OTAUpdateService(
            update_server_url=os.getenv("OTA_SERVER_URL", "https://updates.telemetryiq.com"),
            app_version=getattr(config, "__version__", "1.0.0"),
        )
        
        update_info = ota_service.check_for_updates(force=True)
        
        if update_info:
            return {
                "update_available": True,
                "version": update_info.version,
                "changelog": update_info.changelog,
                "critical": update_info.critical,
            }
        else:
            return {"update_available": False}
    except Exception as e:
        LOGGER.error("OTA check failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/remote-tuning/tuners")
@rate_limit("/api/remote-tuning")
@require_auth
async def get_available_tuners(request: Request):
    """Get available professional tuners."""
    try:
        from services.remote_tuning_service import RemoteTuningService
        
        tuning_service = RemoteTuningService(
            server_url=os.getenv("REMOTE_TUNING_SERVER_URL", "https://tuning.telemetryiq.com"),
        )
        
        tuners = tuning_service.get_available_tuners()
        
        return {
            "tuners": [
                {
                    "tuner_id": t.tuner_id,
                    "name": t.name,
                    "rating": t.rating,
                    "rating_count": t.rating_count,
                    "specializations": t.specializations,
                    "verified": t.verified,
                }
                for t in tuners
            ]
        }
    except Exception as e:
        LOGGER.error("Failed to get tuners: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/social/leaderboard/{category}")
@rate_limit("/api/social")
@require_auth
async def get_leaderboard(request: Request, category: str, limit: int = 100):
    """Get leaderboard for category."""
    try:
        from services.social_racing_platform import SocialRacingPlatform
        
        platform = SocialRacingPlatform(
            server_url=os.getenv("SOCIAL_PLATFORM_URL", "https://social.telemetryiq.com"),
        )
        
        entries = platform.get_leaderboard(category, limit)
        
        return {
            "category": category,
            "entries": [
                {
                    "rank": e.rank,
                    "username": e.username,
                    "vehicle": e.vehicle,
                    "value": e.value,
                    "unit": e.unit,
                }
                for e in entries
            ]
        }
    except Exception as e:
        LOGGER.error("Failed to get leaderboard: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/fleet/performance")
@rate_limit("/api/fleet")
@require_auth
async def get_fleet_performance(request: Request):
    """Get fleet performance metrics."""
    try:
        from services.fleet_management import FleetManagement
        
        fleet = FleetManagement()
        performance = fleet.get_fleet_performance()
        
        return {
            "total_vehicles": performance.total_vehicles,
            "active_vehicles": performance.active_vehicles,
            "total_runs": performance.total_runs,
            "total_distance": performance.total_distance,
            "average_best_time": performance.average_best_time,
            "average_best_speed": performance.average_best_speed,
            "top_performer": performance.top_performer,
        }
    except Exception as e:
        LOGGER.error("Failed to get fleet performance: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/blockchain/records")
@rate_limit("/api/blockchain")
@require_auth
async def get_blockchain_records(request: Request, record_type: Optional[str] = None):
    """Get blockchain-verified records."""
    try:
        from services.blockchain_records import BlockchainRecords, RecordType
        
        records_service = BlockchainRecords()
        
        record_type_enum = None
        if record_type:
            try:
                record_type_enum = RecordType(record_type)
            except ValueError:
                pass
        
        records = records_service.get_all_records(record_type=record_type_enum)
        
        return {
            "records": [
                {
                    "record_id": r.record_id,
                    "record_type": r.record_type.value,
                    "value": r.value,
                    "unit": r.unit,
                    "vehicle_name": r.vehicle_name,
                    "timestamp": r.timestamp,
                    "verified": r.verified,
                    "nft_token_id": r.nft_token_id,
                }
                for r in records
            ]
        }
    except Exception as e:
        LOGGER.error("Failed to get records: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)











