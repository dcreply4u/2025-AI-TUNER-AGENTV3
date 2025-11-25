"""
Remote Access Service
Enables remote tuners and technicians to view real-time telemetry data
with secure authentication and session management.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Callable, Any
from datetime import datetime, timedelta

LOGGER = logging.getLogger(__name__)


class AccessLevel(Enum):
    """Access permission levels for remote viewers."""
    VIEW_ONLY = "view_only"  # Can only view telemetry
    VIEW_ANNOTATE = "view_annotate"  # Can view and add annotations
    VIEW_CONTROL = "view_control"  # Can view and make limited changes
    FULL_ACCESS = "full_access"  # Full access (owner/admin)


@dataclass
class RemoteSession:
    """Represents an active remote access session."""
    session_id: str
    client_name: str
    access_token: str
    access_level: AccessLevel
    ip_address: str
    user_agent: str
    created_at: float
    last_activity: float
    connected: bool = True
    annotations: List[Dict[str, Any]] = field(default_factory=list)
    subscribed_channels: Set[str] = field(default_factory=lambda: {"telemetry", "gps", "video"})
    
    def is_expired(self, max_idle_minutes: int = 60) -> bool:
        """Check if session has expired due to inactivity."""
        idle_seconds = time.time() - self.last_activity
        return idle_seconds > (max_idle_minutes * 60)
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = time.time()


@dataclass
class RemoteAccessConfig:
    """Configuration for remote access service."""
    enabled: bool = True
    require_authentication: bool = True
    default_access_level: AccessLevel = AccessLevel.VIEW_ONLY
    max_sessions: int = 10
    session_timeout_minutes: int = 60
    allow_anonymous: bool = False
    rate_limit_per_minute: int = 1000
    enable_chat: bool = True
    enable_annotations: bool = True
    enable_video_streaming: bool = True


class RemoteAccessService:
    """Service for managing remote access sessions and broadcasting telemetry."""
    
    def __init__(self, config: Optional[RemoteAccessConfig] = None):
        self.config = config or RemoteAccessConfig()
        self.sessions: Dict[str, RemoteSession] = {}
        self.access_tokens: Dict[str, str] = {}  # token -> session_id
        self.broadcast_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self.telemetry_data: Dict[str, float] = {}
        self.gps_data: Optional[Dict[str, Any]] = None
        self.video_streams: Dict[str, Any] = {}
        self.chat_messages: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        
        if self.config.enabled:
            self._start_cleanup_task()
    
    def _start_cleanup_task(self) -> None:
        """Start background task to clean up expired sessions."""
        async def cleanup_loop():
            while True:
                await asyncio.sleep(60)  # Check every minute
                await self._cleanup_expired_sessions()
        
        try:
            loop = asyncio.get_event_loop()
            self._cleanup_task = loop.create_task(cleanup_loop())
        except RuntimeError:
            # No event loop running, will start when needed
            pass
    
    async def _cleanup_expired_sessions(self) -> None:
        """Remove expired sessions."""
        async with self._lock:
            expired = [
                session_id for session_id, session in self.sessions.items()
                if session.is_expired(self.config.session_timeout_minutes)
            ]
            for session_id in expired:
                await self.disconnect_session(session_id)
                LOGGER.info("Removed expired session: %s", session_id)
    
    async def create_session(
        self,
        client_name: str,
        access_level: Optional[AccessLevel] = None,
        ip_address: str = "",
        user_agent: str = "",
        access_token: Optional[str] = None,
    ) -> RemoteSession:
        """
        Create a new remote access session.
        
        Args:
            client_name: Name/identifier of the remote client
            access_level: Permission level (defaults to config default)
            ip_address: Client IP address
            user_agent: Client user agent string
            access_token: Optional pre-generated access token
        
        Returns:
            RemoteSession object
        """
        async with self._lock:
            # Check session limit
            if len(self.sessions) >= self.config.max_sessions:
                raise ValueError(f"Maximum sessions ({self.config.max_sessions}) reached")
            
            # Generate session ID and token
            session_id = secrets.token_urlsafe(16)
            if access_token is None:
                access_token = secrets.token_urlsafe(32)
            
            # Determine access level
            if access_level is None:
                access_level = self.config.default_access_level
            
            # Create session
            session = RemoteSession(
                session_id=session_id,
                client_name=client_name,
                access_token=access_token,
                access_level=access_level,
                ip_address=ip_address,
                user_agent=user_agent,
                created_at=time.time(),
                last_activity=time.time(),
            )
            
            self.sessions[session_id] = session
            self.access_tokens[access_token] = session_id
            
            LOGGER.info(
                "Created remote session: %s (%s) from %s",
                session_id, client_name, ip_address
            )
            
            return session
    
    async def authenticate_session(self, access_token: str) -> Optional[RemoteSession]:
        """
        Authenticate a session using access token.
        
        Args:
            access_token: Access token string
        
        Returns:
            RemoteSession if valid, None otherwise
        """
        async with self._lock:
            session_id = self.access_tokens.get(access_token)
            if not session_id:
                return None
            
            session = self.sessions.get(session_id)
            if not session or not session.connected:
                return None
            
            if session.is_expired(self.config.session_timeout_minutes):
                await self.disconnect_session(session_id)
                return None
            
            session.update_activity()
            return session
    
    async def disconnect_session(self, session_id: str) -> None:
        """Disconnect and remove a session."""
        async with self._lock:
            session = self.sessions.get(session_id)
            if session:
                session.connected = False
                self.access_tokens.pop(session.access_token, None)
                self.sessions.pop(session_id, None)
                LOGGER.info("Disconnected remote session: %s", session_id)
    
    async def update_telemetry(self, data: Dict[str, float]) -> None:
        """
        Update telemetry data and broadcast to all connected sessions.
        
        Args:
            data: Dictionary of telemetry values
        """
        self.telemetry_data.update(data)
        
        # Broadcast to all connected sessions
        if self.sessions:
            message = {
                "type": "telemetry",
                "timestamp": time.time(),
                "data": data,
            }
            await self._broadcast_to_sessions(message, channel="telemetry")
    
    async def update_gps(self, gps_data: Dict[str, Any]) -> None:
        """Update GPS data and broadcast."""
        self.gps_data = gps_data
        
        message = {
            "type": "gps",
            "timestamp": time.time(),
            "data": gps_data,
        }
        await self._broadcast_to_sessions(message, channel="gps")
    
    async def update_video_stream(self, stream_id: str, frame_data: Any) -> None:
        """Update video stream frame."""
        self.video_streams[stream_id] = {
            "stream_id": stream_id,
            "timestamp": time.time(),
            "frame_data": frame_data,
        }
        
        message = {
            "type": "video_frame",
            "stream_id": stream_id,
            "timestamp": time.time(),
            "frame_data": frame_data,
        }
        await self._broadcast_to_sessions(message, channel="video")
    
    async def add_chat_message(
        self,
        session_id: str,
        message: str,
        message_type: str = "message",
    ) -> Dict[str, Any]:
        """
        Add a chat message and broadcast to all sessions.
        
        Args:
            session_id: Session ID of sender
            message: Message text
            message_type: Type of message (message, warning, error, info)
        
        Returns:
            Chat message object
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        chat_msg = {
            "id": secrets.token_urlsafe(8),
            "session_id": session_id,
            "client_name": session.client_name,
            "message": message,
            "type": message_type,
            "timestamp": time.time(),
        }
        
        self.chat_messages.append(chat_msg)
        
        # Keep only last 100 messages
        if len(self.chat_messages) > 100:
            self.chat_messages = self.chat_messages[-100:]
        
        # Broadcast chat message
        await self._broadcast_to_sessions({
            "type": "chat",
            "data": chat_msg,
        }, channel="chat")
        
        return chat_msg
    
    async def add_annotation(
        self,
        session_id: str,
        annotation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Add an annotation (marker, note, etc.) to the session.
        
        Args:
            session_id: Session ID
            annotation: Annotation data
        
        Returns:
            Annotation object with ID
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        if session.access_level in (AccessLevel.VIEW_ONLY,):
            raise PermissionError("Session does not have permission to add annotations")
        
        annotation["id"] = secrets.token_urlsafe(8)
        annotation["session_id"] = session_id
        annotation["client_name"] = session.client_name
        annotation["timestamp"] = time.time()
        
        session.annotations.append(annotation)
        
        # Broadcast annotation to all sessions
        await self._broadcast_to_sessions({
            "type": "annotation",
            "data": annotation,
        }, channel="annotations")
        
        return annotation
    
    async def _broadcast_to_sessions(
        self,
        message: Dict[str, Any],
        channel: str = "telemetry",
    ) -> None:
        """Broadcast message to all sessions subscribed to the channel."""
        async with self._lock:
            for session in self.sessions.values():
                if session.connected and channel in session.subscribed_channels:
                    # Call broadcast callbacks (e.g., WebSocket manager)
                    for callback in self.broadcast_callbacks:
                        try:
                            callback(message)
                        except Exception as e:
                            LOGGER.error("Error in broadcast callback: %s", e)
    
    def register_broadcast_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register a callback for broadcasting messages (e.g., WebSocket)."""
        self.broadcast_callbacks.append(callback)
    
    def get_session(self, session_id: str) -> Optional[RemoteSession]:
        """Get session by ID."""
        return self.sessions.get(session_id)
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions."""
        return [
            {
                "session_id": session.session_id,
                "client_name": session.client_name,
                "access_level": session.access_level.value,
                "ip_address": session.ip_address,
                "created_at": session.created_at,
                "last_activity": session.last_activity,
                "connected": session.connected,
            }
            for session in self.sessions.values()
        ]
    
    def get_telemetry_snapshot(self) -> Dict[str, Any]:
        """Get current telemetry data snapshot."""
        return {
            "telemetry": self.telemetry_data.copy(),
            "gps": self.gps_data.copy() if self.gps_data else None,
            "timestamp": time.time(),
        }
    
    def generate_access_link(
        self,
        session_id: str,
        base_url: Optional[str] = None,
    ) -> str:
        """Generate a shareable access link for a session."""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Get base URL from config if not provided
        if base_url is None:
            try:
                from config import API_BASE_URL
                base_url = API_BASE_URL
            except ImportError:
                import os
                base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        
        return f"{base_url}/remote/view?token={session.access_token}"
    
    async def shutdown(self) -> None:
        """Shutdown the service and disconnect all sessions."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        async with self._lock:
            for session_id in list(self.sessions.keys()):
                await self.disconnect_session(session_id)
        
        LOGGER.info("Remote access service shut down")


__all__ = [
    "RemoteAccessService",
    "RemoteSession",
    "RemoteAccessConfig",
    "AccessLevel",
]

