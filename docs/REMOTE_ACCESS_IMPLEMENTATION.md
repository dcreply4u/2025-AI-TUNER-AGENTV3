# Remote Access Implementation

## Overview

The Remote Access feature enables remote tuners, technicians, and other authorized personnel to view real-time telemetry data from a vehicle tuning session. This allows for collaborative tuning, remote diagnostics, and real-time monitoring without requiring physical presence.

## Features

### Core Capabilities

1. **Real-Time Telemetry Streaming**
   - Live telemetry data (RPM, speed, temperatures, pressures, etc.)
   - GPS location and track data
   - Low-latency WebSocket communication
   - Configurable update rates

2. **Session Management**
   - Create and manage multiple remote access sessions
   - Access level controls (View Only, View & Annotate, View & Control, Full Access)
   - Session timeout and automatic cleanup
   - IP address tracking and user agent logging

3. **Web-Based Viewer**
   - Modern, responsive web interface
   - Real-time metric display
   - Chat functionality for communication
   - No installation required

4. **Security Features**
   - Access token authentication
   - Session-based access control
   - Configurable permission levels
   - Rate limiting support

5. **Additional Features**
   - Chat messaging between tuners
   - Annotations and markers
   - Video streaming support (future)
   - Session history and logging

## Architecture

### Components

1. **RemoteAccessService** (`services/remote_access_service.py`)
   - Core service for managing sessions and broadcasting telemetry
   - Session lifecycle management
   - Access control and permissions
   - Telemetry data broadcasting

2. **Remote Access API** (`api/remote_access_api.py`)
   - REST API endpoints for session management
   - WebSocket endpoint for real-time streaming
   - Web viewer HTML interface
   - Authentication and authorization

3. **Remote Access Tab** (`ui/remote_access_tab.py`)
   - Desktop UI for managing remote access
   - Session creation and management
   - Access link generation
   - Session monitoring

### Data Flow

```
Desktop App (DataStreamController)
    ↓
update_telemetry(data)
    ↓
RemoteAccessService.update_telemetry(data)
    ↓
Broadcast to all connected WebSocket sessions
    ↓
Remote Viewer (Web Browser)
```

## Usage

### Creating a Remote Access Session

1. **Via Desktop UI:**
   - Navigate to the "Remote Access" tab
   - Enter a client name (e.g., "Remote Tuner", "John's Laptop")
   - Select access level
   - Click "Create Session"
   - Copy the generated access link

2. **Via API:**
   ```python
   POST /remote/session/create
   {
       "client_name": "Remote Tuner",
       "access_level": "view_only"
   }
   ```

### Accessing Remote Viewer

1. Open the access link in a web browser
2. The viewer will automatically connect via WebSocket
3. Real-time telemetry data will be displayed
4. Use the chat feature to communicate with the primary tuner

### Access Levels

- **View Only**: Can only view telemetry data
- **View & Annotate**: Can view and add annotations/markers
- **View & Control**: Can view and make limited configuration changes
- **Full Access**: Complete access (owner/admin only)

## API Endpoints

### REST Endpoints

- `POST /remote/session/create` - Create a new session
- `GET /remote/session/authenticate?token=...` - Authenticate a session
- `GET /remote/session/list` - List all active sessions
- `POST /remote/session/{session_id}/disconnect` - Disconnect a session
- `GET /remote/telemetry/snapshot?token=...` - Get current telemetry snapshot
- `POST /remote/chat/send?token=...` - Send a chat message
- `GET /remote/chat/history?token=...` - Get chat history
- `POST /remote/annotation/add?token=...` - Add an annotation

### WebSocket Endpoint

- `WS /remote/ws/{token}` - Real-time telemetry streaming

### Web Viewer

- `GET /remote/view?token=...` - Web-based remote viewer interface

## Configuration

### RemoteAccessConfig

```python
RemoteAccessConfig(
    enabled=True,                    # Enable/disable remote access
    require_authentication=True,      # Require token authentication
    default_access_level=AccessLevel.VIEW_ONLY,
    max_sessions=10,                 # Maximum concurrent sessions
    session_timeout_minutes=60,      # Session idle timeout
    allow_anonymous=False,            # Allow anonymous access
    rate_limit_per_minute=1000,      # Rate limit per session
    enable_chat=True,                # Enable chat functionality
    enable_annotations=True,          # Enable annotations
    enable_video_streaming=True,      # Enable video streaming
)
```

## Integration

### With Mobile API Server

The remote access API is automatically integrated with the mobile API server:

```python
# In mobile_api_server.py
from api.remote_access_api import router as remote_access_router, initialize_remote_access
app.include_router(remote_access_router)

# On startup
initialize_remote_access(RemoteAccessConfig(enabled=True))
```

### With Telemetry Updates

Telemetry updates are automatically pushed to remote access service:

```python
# In main_container.py
def update_telemetry(self, data: Dict[str, float]) -> None:
    # ... existing code ...
    
    # Push to remote access service
    if remote_service:
        await remote_service.update_telemetry(data)
```

## Security Considerations

1. **Access Tokens**: Use strong, randomly generated tokens
2. **HTTPS/WSS**: Use secure connections in production
3. **Rate Limiting**: Implement rate limiting to prevent abuse
4. **Session Timeout**: Configure appropriate timeout values
5. **IP Whitelisting**: Consider IP whitelisting for sensitive operations
6. **Access Level Control**: Use appropriate access levels for different users

## Future Enhancements

1. **Video Streaming**: Stream camera feeds to remote viewers
2. **Screen Sharing**: Share desktop application screen
3. **Recording**: Record sessions for later review
4. **Advanced Permissions**: Granular permission controls
5. **Multi-Vehicle Support**: Support multiple vehicles simultaneously
6. **Mobile App Integration**: Native mobile app for remote viewing
7. **Cloud Relay**: Cloud-based relay for NAT traversal

## Troubleshooting

### Common Issues

1. **WebSocket Connection Fails**
   - Check firewall settings
   - Verify API server is running
   - Check access token validity

2. **No Telemetry Data**
   - Verify telemetry updates are being sent
   - Check remote access service is initialized
   - Verify session is connected

3. **Session Expires Immediately**
   - Check session timeout configuration
   - Verify client is sending ping messages
   - Check network connectivity

## Examples

### Creating a Session Programmatically

```python
from services.remote_access_service import RemoteAccessService, RemoteAccessConfig, AccessLevel

service = RemoteAccessService(RemoteAccessConfig(enabled=True))

session = await service.create_session(
    client_name="Remote Tuner",
    access_level=AccessLevel.VIEW_ONLY,
    ip_address="192.168.1.100",
)

access_link = service.generate_access_link(session.session_id)
print(f"Access link: {access_link}")
```

### Broadcasting Custom Data

```python
# Update telemetry
await service.update_telemetry({
    "RPM": 3500,
    "Speed": 65,
    "Boost_Pressure": 15.5,
})

# Update GPS
await service.update_gps({
    "lat": 40.7128,
    "lon": -74.0060,
    "speed": 65,
})
```

## Files Created/Modified

### New Files

- `services/remote_access_service.py` - Core remote access service
- `api/remote_access_api.py` - REST API and WebSocket endpoints
- `ui/remote_access_tab.py` - Desktop UI for managing remote access
- `docs/REMOTE_ACCESS_IMPLEMENTATION.md` - This documentation

### Modified Files

- `api/mobile_api_server.py` - Integrated remote access router
- `ui/main_container.py` - Added remote access tab and telemetry integration

## Summary

The Remote Access feature provides a comprehensive solution for enabling remote tuners and technicians to view real-time telemetry data. With secure authentication, flexible access controls, and a modern web-based interface, it enables collaborative tuning and remote diagnostics while maintaining security and performance.

