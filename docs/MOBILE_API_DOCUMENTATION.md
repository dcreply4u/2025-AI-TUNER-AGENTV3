# TelemetryIQ Mobile API Documentation

Complete API documentation for Android/iOS mobile app integration.

## Base URL

```
http://<server-ip>:8000
```

For local development:
```
http://localhost:8000
```

## Authentication

Currently, the API is open (no authentication required). In production, implement JWT authentication.

## API Endpoints

### Health & Status

#### GET `/`
Root endpoint - service information.

**Response:**
```json
{
  "service": "TelemetryIQ Mobile API",
  "version": "1.0.0",
  "status": "online"
}
```

#### GET `/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1234567890.123,
  "services": {
    "config_monitor": true,
    "ai_advisor": true,
    "backup_manager": true,
    "hardware_manager": true,
    "camera_manager": true
  }
}
```

### Telemetry

#### GET `/api/telemetry/current`
Get current telemetry data.

**Query Parameters:**
- `sensors` (optional): Comma-separated list of sensor names

**Response:**
```json
{
  "timestamp": 1234567890.123,
  "data": {
    "RPM": 3500.0,
    "Boost_Pressure": 15.5,
    "AFR": 14.7,
    "Coolant_Temp": 90.0
  }
}
```

#### GET `/api/telemetry/sensors`
List all available sensors.

**Response:**
```json
{
  "sensors": ["RPM", "Boost_Pressure", "AFR", "Coolant_Temp"],
  "count": 4
}
```

#### WebSocket `/ws/telemetry`
Real-time telemetry streaming via WebSocket.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/telemetry');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // data.type = "telemetry"
  // data.timestamp = 1234567890.123
  // data.data = { "RPM": 3500, ... }
};
```

**Keep-alive:**
Send `{"type": "ping"}` periodically. Server responds with `{"type": "pong"}`.

### Configuration

#### POST `/api/config/change`
Apply a configuration change.

**Request Body:**
```json
{
  "change_type": "ecu_tuning",
  "category": "Ignition Timing",
  "parameter": "base_timing",
  "new_value": 32.0,
  "old_value": 28.0
}
```

**Response:**
```json
{
  "status": "success",
  "warnings": [
    {
      "severity": "critical",
      "message": "⚠️ CRITICAL: High ignition advance (32.0°) detected!",
      "suggestion": "Reduce timing to 25° or less",
      "alternative_value": 25.0,
      "reasoning": "High timing + boost = high knock risk"
    }
  ],
  "change_applied": true
}
```

#### GET `/api/config/history`
Get configuration change history.

**Query Parameters:**
- `category` (optional): Filter by category
- `limit` (optional): Maximum number of records (default: 50)

**Response:**
```json
{
  "changes": [
    {
      "change_id": "1234567890_abc123",
      "timestamp": 1234567890.123,
      "category": "Ignition Timing",
      "parameter": "base_timing",
      "old_value": 28.0,
      "new_value": 32.0,
      "severity": "high",
      "outcome": "success"
    }
  ],
  "count": 1
}
```

#### GET `/api/config/best`
Get best performing configuration.

**Query Parameters:**
- `config_type`: "ecu_tuning" or "motorsport"
- `metric`: Performance metric name (default: "power")

**Response:**
```json
{
  "snapshot_id": "snapshot_1234567890_abc123",
  "timestamp": 1234567890.123,
  "configuration": {
    "base_timing": 28.5,
    "boost_target": 22.0
  },
  "performance_metrics": {
    "power": 450.0,
    "torque": 380.0
  },
  "description": "Best performing configuration"
}
```

### AI Advisor

#### POST `/api/ai/ask`
Ask AI advisor Q a question.

**Request Body:**
```json
{
  "question": "How do I configure boost control?",
  "context": {
    "current_tab": "Boost Control"
  }
}
```

**Response:**
```json
{
  "response": "Boost control configuration...",
  "timestamp": 1234567890.123
}
```

#### GET `/api/ai/suggestions`
Get question suggestions.

**Query Parameters:**
- `partial` (optional): Partial question text

**Response:**
```json
{
  "suggestions": [
    "How do I configure ECU tuning?",
    "What are the keyboard shortcuts?",
    "How do I set up backups?"
  ]
}
```

### Backup & Version Control

#### POST `/api/backup/create`
Create a backup.

**Request Body:**
```json
{
  "file_path": "/path/to/tuning/file.cal",
  "backup_type": "ecu_calibration",
  "description": "Before major changes"
}
```

**Response:**
```json
{
  "status": "success",
  "backup_id": "1234567890_abc123",
  "timestamp": 1234567890.123,
  "file_path": "/path/to/tuning/file.cal"
}
```

#### GET `/api/backup/list`
List backups for a file.

**Query Parameters:**
- `file_path`: Path to file

**Response:**
```json
{
  "backups": [
    {
      "backup_id": "1234567890_abc123",
      "timestamp": 1234567890.123,
      "description": "Before major changes",
      "file_size": 1024000,
      "file_hash": "abc123def456..."
    }
  ],
  "count": 1
}
```

#### POST `/api/backup/revert/{file_path}/{backup_id}`
Revert file to backup.

**Response:**
```json
{
  "status": "success",
  "message": "File reverted successfully"
}
```

### Hardware

#### GET `/api/hardware/interfaces`
List all hardware interfaces.

**Response:**
```json
{
  "interfaces": [
    {
      "interface_id": "gpio_rpi",
      "interface_type": "gpio_direct",
      "board_type": "raspberry_pi",
      "name": "Raspberry Pi GPIO",
      "description": "Built-in GPIO pins",
      "connected": true,
      "gpio_pins": 5
    }
  ],
  "count": 1
}
```

#### GET `/api/hardware/gpio/{interface_id}/{pin}`
Read GPIO pin value.

**Response:**
```json
{
  "interface_id": "gpio_rpi",
  "pin": 18,
  "value": true
}
```

#### POST `/api/hardware/gpio/{interface_id}/{pin}`
Write GPIO pin value.

**Request Body:**
```json
{
  "value": true
}
```

**Response:**
```json
{
  "status": "success",
  "interface_id": "gpio_rpi",
  "pin": 18,
  "value": true
}
```

### Cameras

#### GET `/api/cameras`
List all detected cameras.

**Response:**
```json
{
  "cameras": [
    {
      "device_id": "0",
      "vendor": "logitech",
      "model": "C920",
      "driver": "v4l2",
      "max_fps": 30,
      "supported_resolutions": [[640, 480], [1280, 720], [1920, 1080]]
    }
  ],
  "count": 1
}
```

#### GET `/api/cameras/{device_id}/preview`
Get camera preview frame (JPEG image).

**Response:**
JPEG image stream

### System Status

#### GET `/api/system/status`
Get overall system status.

**Response:**
```json
{
  "timestamp": 1234567890.123,
  "telemetry": {
    "sensors_count": 15,
    "last_update": 1234567890.123
  },
  "websockets": {
    "active_connections": 2
  },
  "services": {
    "config_monitor": true,
    "ai_advisor": true,
    "backup_manager": true,
    "hardware_manager": true,
    "camera_manager": true
  }
}
```

## WebSocket Protocol

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/telemetry');
```

### Message Types

#### Telemetry Update (Server → Client)
```json
{
  "type": "telemetry",
  "timestamp": 1234567890.123,
  "data": {
    "RPM": 3500.0,
    "Boost_Pressure": 15.5,
    "AFR": 14.7
  }
}
```

#### Ping (Client → Server)
```json
{
  "type": "ping"
}
```

#### Pong (Server → Client)
```json
{
  "type": "pong",
  "timestamp": 1234567890.123
}
```

## Mobile App Integration Examples

### Android (Kotlin)

```kotlin
// Retrofit interface
interface TelemetryIQAPI {
    @GET("api/telemetry/current")
    suspend fun getCurrentTelemetry(): TelemetryResponse
    
    @POST("api/config/change")
    suspend fun applyConfigChange(@Body request: ConfigChangeRequest): ConfigChangeResponse
    
    @WebSocket("ws/telemetry")
    fun createWebSocket(): WebSocket
}

// Usage
val api = Retrofit.create(TelemetryIQAPI::class.java)
val telemetry = api.getCurrentTelemetry()
```

### iOS (Swift)

```swift
// URLSession
let url = URL(string: "http://localhost:8000/api/telemetry/current")!
let task = URLSession.shared.dataTask(with: url) { data, response, error in
    // Handle response
}
task.resume()

// WebSocket
let ws = URLSessionWebSocketTask(url: URL(string: "ws://localhost:8000/ws/telemetry")!)
ws.resume()
```

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message here"
}
```

**HTTP Status Codes:**
- `200`: Success
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `500`: Internal Server Error
- `503`: Service Unavailable

## Rate Limiting

Currently no rate limiting. In production, implement rate limiting per client.

## CORS

CORS is enabled for all origins. In production, restrict to specific domains.

## Starting the Server

```bash
python api/mobile_api_start.py
```

Or:

```bash
uvicorn api.mobile_api_server:app --host 0.0.0.0 --port 8000
```

## API Documentation

Interactive API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
















