"""FastAPI server for ECU flashing, calibration editing, and AI tuning."""

from __future__ import annotations

import asyncio
import io
import logging
import time

from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from pydantic import BaseModel

from ai_engine.tuner import AITuningEngine
from calibration.editor import CalibrationEditor
from can_interface.ecu_flash import ECUFlashManager
from telemetry.can_logger import CANDataLogger

from .auth import (
    UserLogin,
    UserRegister,
    authenticate_user,
    jwt_exception_handler,
    require_role,
)
from .users_db import create_user, has_users, init_db

LOGGER = logging.getLogger(__name__)

app = FastAPI(title="AI Tuner Edge Agent API", version="3.0")
app.add_exception_handler(AuthJWTException, jwt_exception_handler)

# Global instances
ecu_manager = ECUFlashManager()
ai_engine = AITuningEngine()
can_logger = CANDataLogger()


class TuneRequest(BaseModel):
    """Request model for AI tuning."""

    rpm: float
    load: float
    afr: float


@app.on_event("startup")
async def _startup() -> None:
    init_db()


@app.post("/auth/register")
def register_user(req: UserRegister, authorize: AuthJWT = Depends()):
    """
    Register a new user. The first user can self-register; subsequent registrations
    require an authenticated admin token.
    """
    if has_users():
        try:
            authorize.jwt_required()
            claims = authorize.get_raw_jwt()
        except Exception as exc:  # pragma: no cover - FastAPI handles detail
            raise HTTPException(status_code=401, detail="Authentication required") from exc
        if claims.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin privileges required")

    create_user(req.username, req.password, req.role)
    return {"status": "user created", "username": req.username, "role": req.role}


@app.post("/auth/login")
def login(req: UserLogin, authorize: AuthJWT = Depends()):
    user = authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = authorize.create_access_token(
        subject=user["username"], user_claims={"role": user["role"]}
    )
    refresh_token = authorize.create_refresh_token(subject=user["username"])
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "role": user["role"],
    }


@app.post("/auth/refresh")
def refresh_token(authorize: AuthJWT = Depends()):
    authorize.jwt_refresh_token_required()
    current_user = authorize.get_jwt_subject()
    new_access_token = authorize.create_access_token(subject=current_user)
    return {"access_token": new_access_token}


@app.post("/ecu/read")
async def ecu_read(start_addr: int, size: int) -> StreamingResponse:
    """
    Read ECU memory at specified address and size.

    Args:
        start_addr: Starting address (hex format, e.g., 0x000000)
        size: Number of bytes to read

    Returns:
        Binary stream of ECU data
    """
    try:
        data = ecu_manager.read_ecu(start_addr, size)
        return StreamingResponse(io.BytesIO(data), media_type="application/octet-stream")
    except Exception as e:
        LOGGER.error("ECU read failed: %s", e)
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/ecu/write")
async def ecu_write(
    file: UploadFile = File(...),
    start_addr: int = 0x000000,
    background_tasks: BackgroundTasks | None = None,
    claims: dict = Depends(require_role("admin")),
) -> JSONResponse:
    """
    Write binary data to ECU at specified address.

    Args:
        file: Binary file to write
        start_addr: Starting address (hex format)
        background_tasks: FastAPI background tasks

    Returns:
        Status response
    """
    try:
        bin_data = await file.read()
        if background_tasks:
            background_tasks.add_task(ecu_manager.write_ecu, start_addr, bin_data)
        else:
            ecu_manager.write_ecu(start_addr, bin_data)
        return JSONResponse({"status": "ECU write complete", "bytes": len(bin_data)})
    except Exception as e:
        LOGGER.error("ECU write failed: %s", e)
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/calibration/upload")
async def calibration_upload(file: UploadFile = File(...)) -> JSONResponse:
    """
    Upload calibration binary file.

    Args:
        file: Calibration binary file

    Returns:
        Upload status
    """
    try:
        data = await file.read()
        editor = CalibrationEditor(data)
        editor.save("uploaded_calibration.bin")
        return JSONResponse({"status": "Calibration uploaded", "size": len(data)})
    except Exception as e:
        LOGGER.error("Calibration upload failed: %s", e)
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/calibration/download")
async def calibration_download() -> StreamingResponse:
    """
    Download the current calibration binary.

    Returns:
        Binary stream of calibration data
    """
    try:
        with open("uploaded_calibration.bin", "rb") as f:
            data = f.read()
        return StreamingResponse(io.BytesIO(data), media_type="application/octet-stream")
    except FileNotFoundError:
        return JSONResponse({"error": "No calibration file found"}, status_code=404)
    except Exception as e:
        LOGGER.error("Calibration download failed: %s", e)
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/ai/tune")
async def ai_tune(
    req: TuneRequest,
    claims: dict = Depends(require_role("tuner")),
) -> JSONResponse:
    """
    Get AI-suggested tuning adjustments based on telemetry.

    Args:
        req: Tuning request with RPM, load, and AFR

    Returns:
        Suggested adjustments
    """
    try:
        telemetry = [[req.rpm, req.load, req.afr]]
        adjustments = ai_engine.suggest_adjustments(telemetry)
        return JSONResponse({"adjustments": adjustments.tolist()})
    except Exception as e:
        LOGGER.error("AI tuning failed: %s", e)
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/telemetry/live")
async def telemetry_live() -> StreamingResponse:
    """
    Stream live CAN bus telemetry as Server-Sent Events (SSE).

    Returns:
        Event stream of CAN messages
    """
    async def event_stream():
        if not can_logger.is_active():
            can_logger.start_background_stream()
            # Wait a bit for connection
            await asyncio.sleep(0.5)
        
        # Use background stream and poll database for new messages
        last_timestamp = time.time()
        try:
            while True:
                # Query recent messages from database
                if can_logger.cursor:
                    can_logger.cursor.execute(
                        "SELECT pid, value, data FROM logs WHERE timestamp > ? ORDER BY timestamp DESC LIMIT 10",
                        (last_timestamp,)
                    )
                    rows = can_logger.cursor.fetchall()
                    for pid, value, data in rows:
                        data_hex = data.hex() if data else ""
                        yield f"data: {pid},{value},{data_hex}\n\n"
                        last_timestamp = time.time()
                
                await asyncio.sleep(0.1)
        except Exception as e:
            LOGGER.error("Telemetry stream error: %s", e)
            yield f"data: error,{str(e)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "ecu_connected": ecu_manager.is_connected(),
        "ai_engine_loaded": ai_engine.is_loaded(),
        "can_logger_active": can_logger.is_active(),
    })


__all__ = ["app", "TuneRequest"]

