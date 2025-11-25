"""
Remote Access API
REST API and WebSocket endpoints for remote tuner access.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
    Depends,
    Query,
    Header,
)
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from services.remote_access_service import (
    RemoteAccessService,
    RemoteAccessConfig,
    RemoteSession,
    AccessLevel,
)

LOGGER = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/remote", tags=["remote-access"])

# Global service instance (will be initialized on startup)
remote_service: Optional[RemoteAccessService] = None


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateSessionRequest(BaseModel):
    """Request to create a remote access session."""
    client_name: str
    access_level: Optional[str] = None  # "view_only", "view_annotate", "view_control", "full_access"
    access_token: Optional[str] = None


class ChatMessageRequest(BaseModel):
    """Request to send a chat message."""
    message: str
    message_type: str = "message"  # "message", "warning", "error", "info"


class AnnotationRequest(BaseModel):
    """Request to add an annotation."""
    annotation_type: str  # "marker", "note", "highlight"
    data: Dict[str, Any]
    timestamp: Optional[float] = None


class SubscribeRequest(BaseModel):
    """Request to subscribe to specific channels."""
    channels: List[str]  # ["telemetry", "gps", "video", "chat", "annotations"]


# ============================================================================
# WebSocket Manager
# ============================================================================

class RemoteWebSocketManager:
    """Manages WebSocket connections for remote access."""
    
    def __init__(self, remote_service: RemoteAccessService):
        self.remote_service = remote_service
        self.connections: Dict[str, WebSocket] = {}  # session_id -> WebSocket
        self.broadcast_task: Optional[asyncio.Task] = None
        
        # Register broadcast callback
        self.remote_service.register_broadcast_callback(self._broadcast_message)
    
    def _broadcast_message(self, message: Dict[str, Any]) -> None:
        """Callback for broadcasting messages to WebSocket clients."""
        # This will be called from the service
        # We'll handle actual broadcasting in the async context
        pass
    
    async def connect(self, websocket: WebSocket, session: RemoteSession) -> None:
        """Accept WebSocket connection and register session."""
        await websocket.accept()
        self.connections[session.session_id] = websocket
        
        # Send initial data
        await websocket.send_json({
            "type": "connected",
            "session_id": session.session_id,
            "client_name": session.client_name,
            "access_level": session.access_level.value,
            "telemetry_snapshot": self.remote_service.get_telemetry_snapshot(),
        })
        
        LOGGER.info("WebSocket connected for session: %s", session.session_id)
    
    async def disconnect(self, session_id: str) -> None:
        """Disconnect WebSocket and remove from connections."""
        websocket = self.connections.pop(session_id, None)
        if websocket:
            try:
                await websocket.close()
            except Exception:
                pass
        LOGGER.info("WebSocket disconnected for session: %s", session_id)
    
    async def send_to_session(self, session_id: str, message: Dict[str, Any]) -> bool:
        """Send message to a specific session."""
        websocket = self.connections.get(session_id)
        if not websocket:
            return False
        
        try:
            await websocket.send_json(message)
            return True
        except Exception as e:
            LOGGER.error("Error sending to session %s: %s", session_id, e)
            await self.disconnect(session_id)
            return False
    
    async def broadcast(self, message: Dict[str, Any], channel: str = "telemetry") -> None:
        """Broadcast message to all connected sessions subscribed to channel."""
        if not remote_service:
            return
        
        disconnected = []
        for session_id, websocket in self.connections.items():
            session = remote_service.get_session(session_id)
            if not session or channel not in session.subscribed_channels:
                continue
            
            try:
                await websocket.send_json(message)
            except Exception as e:
                LOGGER.error("Error broadcasting to session %s: %s", session_id, e)
                disconnected.append(session_id)
        
        # Clean up disconnected sessions
        for session_id in disconnected:
            await self.disconnect(session_id)
            if remote_service:
                await remote_service.disconnect_session(session_id)


# Global WebSocket manager
ws_manager: Optional[RemoteWebSocketManager] = None


# ============================================================================
# Startup/Initialization
# ============================================================================

def initialize_remote_access(config: Optional[RemoteAccessConfig] = None) -> None:
    """Initialize the remote access service."""
    global remote_service, ws_manager
    
    if remote_service is None:
        remote_service = RemoteAccessService(config or RemoteAccessConfig())
        ws_manager = RemoteWebSocketManager(remote_service)
        LOGGER.info("Remote access service initialized")


# ============================================================================
# REST API Endpoints
# ============================================================================

@router.post("/session/create")
async def create_session(
    request: CreateSessionRequest,
    x_forwarded_for: Optional[str] = Header(None),
    user_agent: Optional[str] = Header(None),
) -> JSONResponse:
    """Create a new remote access session."""
    if not remote_service:
        raise HTTPException(status_code=503, detail="Remote access service not initialized")
    
    # Determine access level
    access_level = None
    if request.access_level:
        try:
            access_level = AccessLevel(request.access_level)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid access level: {request.access_level}")
    
    # Get client IP
    ip_address = x_forwarded_for.split(",")[0].strip() if x_forwarded_for else ""
    
    try:
        session = await remote_service.create_session(
            client_name=request.client_name,
            access_level=access_level,
            ip_address=ip_address,
            user_agent=user_agent or "",
            access_token=request.access_token,
        )
        
        return JSONResponse({
            "status": "success",
            "session_id": session.session_id,
            "access_token": session.access_token,
            "access_level": session.access_level.value,
            "access_link": remote_service.generate_access_link(session.session_id),
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/session/authenticate")
async def authenticate_session(
    token: str = Query(..., description="Access token"),
) -> JSONResponse:
    """Authenticate a session using access token."""
    if not remote_service:
        raise HTTPException(status_code=503, detail="Remote access service not initialized")
    
    session = await remote_service.authenticate_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")
    
    return JSONResponse({
        "status": "authenticated",
        "session_id": session.session_id,
        "client_name": session.client_name,
        "access_level": session.access_level.value,
        "created_at": session.created_at,
    })


@router.get("/session/list")
async def list_sessions() -> JSONResponse:
    """List all active remote access sessions."""
    if not remote_service:
        raise HTTPException(status_code=503, detail="Remote access service not initialized")
    
    sessions = remote_service.list_sessions()
    return JSONResponse({
        "sessions": sessions,
        "count": len(sessions),
    })


@router.post("/session/{session_id}/disconnect")
async def disconnect_session(session_id: str) -> JSONResponse:
    """Disconnect a remote access session."""
    if not remote_service:
        raise HTTPException(status_code=503, detail="Remote access service not initialized")
    
    await remote_service.disconnect_session(session_id)
    if ws_manager:
        await ws_manager.disconnect(session_id)
    
    return JSONResponse({"status": "disconnected"})


@router.get("/telemetry/snapshot")
async def get_telemetry_snapshot(
    token: str = Query(..., description="Access token"),
) -> JSONResponse:
    """Get current telemetry data snapshot."""
    if not remote_service:
        raise HTTPException(status_code=503, detail="Remote access service not initialized")
    
    session = await remote_service.authenticate_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")
    
    snapshot = remote_service.get_telemetry_snapshot()
    return JSONResponse(snapshot)


@router.post("/chat/send")
async def send_chat_message(
    request: ChatMessageRequest,
    token: str = Query(..., description="Access token"),
) -> JSONResponse:
    """Send a chat message."""
    if not remote_service:
        raise HTTPException(status_code=503, detail="Remote access service not initialized")
    
    session = await remote_service.authenticate_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")
    
    chat_msg = await remote_service.add_chat_message(
        session.session_id,
        request.message,
        request.message_type,
    )
    
    # Broadcast via WebSocket
    if ws_manager:
        await ws_manager.broadcast({
            "type": "chat",
            "data": chat_msg,
        }, channel="chat")
    
    return JSONResponse({"status": "sent", "message": chat_msg})


@router.get("/chat/history")
async def get_chat_history(
    token: str = Query(..., description="Access token"),
    limit: int = Query(50, description="Number of messages to retrieve"),
) -> JSONResponse:
    """Get chat message history."""
    if not remote_service:
        raise HTTPException(status_code=503, detail="Remote access service not initialized")
    
    session = await remote_service.authenticate_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")
    
    messages = remote_service.chat_messages[-limit:]
    return JSONResponse({"messages": messages, "count": len(messages)})


@router.post("/annotation/add")
async def add_annotation(
    request: AnnotationRequest,
    token: str = Query(..., description="Access token"),
) -> JSONResponse:
    """Add an annotation."""
    if not remote_service:
        raise HTTPException(status_code=503, detail="Remote access service not initialized")
    
    session = await remote_service.authenticate_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")
    
    try:
        annotation = await remote_service.add_annotation(
            session.session_id,
            {
                "type": request.annotation_type,
                "data": request.data,
                "timestamp": request.timestamp or time.time(),
            },
        )
        
        # Broadcast via WebSocket
        if ws_manager:
            await ws_manager.broadcast({
                "type": "annotation",
                "data": annotation,
            }, channel="annotations")
        
        return JSONResponse({"status": "added", "annotation": annotation})
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# ============================================================================
# WebSocket Endpoints
# ============================================================================

@router.websocket("/ws/{token}")
async def websocket_remote_access(websocket: WebSocket, token: str):
    """WebSocket endpoint for real-time remote access."""
    if not remote_service or not ws_manager:
        await websocket.close(code=1003, reason="Service not initialized")
        return
    
    # Authenticate session
    session = await remote_service.authenticate_session(token)
    if not session:
        await websocket.close(code=1008, reason="Invalid or expired access token")
        return
    
    # Connect WebSocket
    await ws_manager.connect(websocket, session)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": time.time()})
                
                elif message_type == "subscribe":
                    # Update subscribed channels
                    channels = message.get("channels", [])
                    session.subscribed_channels = set(channels)
                    await websocket.send_json({
                        "type": "subscribed",
                        "channels": list(session.subscribed_channels),
                    })
                
                elif message_type == "chat":
                    # Handle chat message
                    chat_request = ChatMessageRequest(**message.get("data", {}))
                    await send_chat_message(chat_request, token=token)
                
                elif message_type == "annotation":
                    # Handle annotation
                    annotation_request = AnnotationRequest(**message.get("data", {}))
                    await add_annotation(annotation_request, token=token)
                
                # Update session activity
                session.update_activity()
                
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
            except Exception as e:
                LOGGER.error("Error handling WebSocket message: %s", e)
                await websocket.send_json({"type": "error", "message": str(e)})
    
    except WebSocketDisconnect:
        await ws_manager.disconnect(session.session_id)
        await remote_service.disconnect_session(session.session_id)
    except Exception as e:
        LOGGER.error("WebSocket error: %s", e)
        await ws_manager.disconnect(session.session_id)
        await remote_service.disconnect_session(session.session_id)


# ============================================================================
# Web Viewer
# ============================================================================

@router.get("/view", response_class=HTMLResponse)
async def remote_viewer_page(
    token: Optional[str] = Query(None, description="Access token"),
) -> HTMLResponse:
    """Serve the remote viewer web page."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TelemetryIQ Remote Viewer</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
                color: #ffffff;
                overflow-x: hidden;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
            }
            .header {
                background: rgba(0, 0, 0, 0.3);
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .status {
                display: flex;
                gap: 20px;
                align-items: center;
            }
            .status-indicator {
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background: #4CAF50;
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }
            .card {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 20px;
                backdrop-filter: blur(10px);
            }
            .card h3 {
                margin-bottom: 15px;
                color: #00d4ff;
                font-size: 18px;
            }
            .metric {
                display: flex;
                justify-content: space-between;
                padding: 10px 0;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            .metric:last-child {
                border-bottom: none;
            }
            .metric-label {
                color: #aaa;
            }
            .metric-value {
                font-weight: bold;
                font-size: 18px;
                color: #00d4ff;
            }
            .chat-container {
                display: flex;
                flex-direction: column;
                height: 400px;
            }
            .chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 10px;
                background: rgba(0, 0, 0, 0.2);
                border-radius: 5px;
                margin-bottom: 10px;
            }
            .chat-message {
                padding: 8px;
                margin-bottom: 8px;
                border-radius: 5px;
                background: rgba(255, 255, 255, 0.05);
            }
            .chat-input-container {
                display: flex;
                gap: 10px;
            }
            .chat-input {
                flex: 1;
                padding: 10px;
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 5px;
                color: #fff;
            }
            .btn {
                padding: 10px 20px;
                background: #00d4ff;
                border: none;
                border-radius: 5px;
                color: #000;
                font-weight: bold;
                cursor: pointer;
                transition: background 0.3s;
            }
            .btn:hover {
                background: #00b8d4;
            }
            .error {
                color: #ff4444;
                padding: 20px;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>TelemetryIQ Remote Viewer</h1>
                <div class="status">
                    <div class="status-indicator" id="statusIndicator"></div>
                    <span id="statusText">Connecting...</span>
                </div>
            </div>
            
            <div id="errorMessage" class="error" style="display: none;"></div>
            
            <div id="mainContent" style="display: none;">
                <div class="grid">
                    <div class="card">
                        <h3>Engine Metrics</h3>
                        <div id="engineMetrics"></div>
                    </div>
                    <div class="card">
                        <h3>Performance</h3>
                        <div id="performanceMetrics"></div>
                    </div>
                    <div class="card">
                        <h3>Temperature</h3>
                        <div id="temperatureMetrics"></div>
                    </div>
                    <div class="card">
                        <h3>GPS & Location</h3>
                        <div id="gpsMetrics"></div>
                    </div>
                </div>
                
                <div class="card">
                    <h3>Chat</h3>
                    <div class="chat-container">
                        <div class="chat-messages" id="chatMessages"></div>
                        <div class="chat-input-container">
                            <input type="text" class="chat-input" id="chatInput" placeholder="Type a message...">
                            <button class="btn" onclick="sendChatMessage()">Send</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            const token = new URLSearchParams(window.location.search).get('token');
            if (!token) {
                document.getElementById('errorMessage').textContent = 'Missing access token';
                document.getElementById('errorMessage').style.display = 'block';
            } else {
                connectWebSocket();
            }
            
            let ws = null;
            let telemetryData = {};
            
            function connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/remote/ws/${token}`;
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = () => {
                    document.getElementById('statusText').textContent = 'Connected';
                    document.getElementById('statusIndicator').style.background = '#4CAF50';
                    document.getElementById('mainContent').style.display = 'block';
                    
                    // Subscribe to channels
                    ws.send(JSON.stringify({
                        type: 'subscribe',
                        channels: ['telemetry', 'gps', 'chat']
                    }));
                };
                
                ws.onmessage = (event) => {
                    const message = JSON.parse(event.data);
                    handleMessage(message);
                };
                
                ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    document.getElementById('statusText').textContent = 'Connection Error';
                    document.getElementById('statusIndicator').style.background = '#ff4444';
                };
                
                ws.onclose = () => {
                    document.getElementById('statusText').textContent = 'Disconnected';
                    document.getElementById('statusIndicator').style.background = '#ff4444';
                    setTimeout(connectWebSocket, 3000);
                };
            }
            
            function handleMessage(message) {
                if (message.type === 'telemetry') {
                    telemetryData = { ...telemetryData, ...message.data };
                    updateMetrics();
                } else if (message.type === 'gps') {
                    updateGPS(message.data);
                } else if (message.type === 'chat') {
                    addChatMessage(message.data);
                }
            }
            
            function updateMetrics() {
                const engine = document.getElementById('engineMetrics');
                const performance = document.getElementById('performanceMetrics');
                const temperature = document.getElementById('temperatureMetrics');
                
                engine.innerHTML = `
                    <div class="metric">
                        <span class="metric-label">RPM</span>
                        <span class="metric-value">${formatValue(telemetryData.RPM || telemetryData.Engine_RPM)}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Throttle</span>
                        <span class="metric-value">${formatValue(telemetryData.Throttle_Position, '%')}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Boost</span>
                        <span class="metric-value">${formatValue(telemetryData.Boost_Pressure, 'psi')}</span>
                    </div>
                `;
                
                performance.innerHTML = `
                    <div class="metric">
                        <span class="metric-label">Speed</span>
                        <span class="metric-value">${formatValue(telemetryData.Speed, 'mph')}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">G-Force</span>
                        <span class="metric-value">${formatValue(telemetryData.GForce_Lateral, 'g')}</span>
                    </div>
                `;
                
                temperature.innerHTML = `
                    <div class="metric">
                        <span class="metric-label">Coolant</span>
                        <span class="metric-value">${formatValue(telemetryData.Coolant_Temp, '°F')}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Oil Temp</span>
                        <span class="metric-value">${formatValue(telemetryData.Oil_Temp, '°F')}</span>
                    </div>
                `;
            }
            
            function updateGPS(gpsData) {
                const gps = document.getElementById('gpsMetrics');
                if (gpsData) {
                    gps.innerHTML = `
                        <div class="metric">
                            <span class="metric-label">Latitude</span>
                            <span class="metric-value">${gpsData.lat?.toFixed(6) || 'N/A'}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Longitude</span>
                            <span class="metric-value">${gpsData.lon?.toFixed(6) || 'N/A'}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Speed</span>
                            <span class="metric-value">${formatValue(gpsData.speed, 'mph')}</span>
                        </div>
                    `;
                }
            }
            
            function formatValue(value, unit = '') {
                if (value === undefined || value === null) return 'N/A';
                if (typeof value === 'number') {
                    return value.toFixed(1) + (unit ? ' ' + unit : '');
                }
                return value;
            }
            
            function addChatMessage(msg) {
                const chat = document.getElementById('chatMessages');
                const div = document.createElement('div');
                div.className = 'chat-message';
                div.innerHTML = `<strong>${msg.client_name}:</strong> ${msg.message}`;
                chat.appendChild(div);
                chat.scrollTop = chat.scrollHeight;
            }
            
            function sendChatMessage() {
                const input = document.getElementById('chatInput');
                const message = input.value.trim();
                if (message && ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: 'chat',
                        data: { message, message_type: 'message' }
                    }));
                    input.value = '';
                }
            }
            
            document.getElementById('chatInput').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    sendChatMessage();
                }
            });
            
            // Ping to keep connection alive
            setInterval(() => {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ type: 'ping' }));
                }
            }, 30000);
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


__all__ = ["router", "initialize_remote_access"]

