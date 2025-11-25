# Mobile App Quick Start Guide

Quick start guide for connecting Android/iOS apps to TelemetryIQ.

## Prerequisites

1. **Python 3.8+** installed
2. **FastAPI dependencies** installed:
   ```bash
   pip install fastapi uvicorn websockets aiohttp
   ```

## Starting the Mobile API Server

### Option 1: Direct Python Script
```bash
python api/mobile_api_start.py
```

### Option 2: Uvicorn Command
```bash
uvicorn api.mobile_api_server:app --host 0.0.0.0 --port 8000
```

### Option 3: Background Service (Windows)
```powershell
Start-Process python -ArgumentList "api/mobile_api_start.py" -WindowStyle Hidden
```

## Server Status

Once started, verify the server is running:

- **API Root**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc

## Mobile App Connection

### Finding Your Server IP

**Windows:**
```powershell
ipconfig
# Look for "IPv4 Address" under your active network adapter
```

**Linux/Mac:**
```bash
ifconfig
# or
ip addr show
```

### Android Connection Example

```kotlin
// Replace with your server IP
val baseUrl = "http://192.168.1.100:8000"

// Retrofit setup
val retrofit = Retrofit.Builder()
    .baseUrl(baseUrl)
    .addConverterFactory(GsonConverterFactory.create())
    .build()

val api = retrofit.create(TelemetryIQAPI::class.java)

// Get current telemetry
val telemetry = api.getCurrentTelemetry().execute()
```

### iOS Connection Example

```swift
// Replace with your server IP
let baseURL = URL(string: "http://192.168.1.100:8000")!

// URLSession request
let url = baseURL.appendingPathComponent("api/telemetry/current")
let task = URLSession.shared.dataTask(with: url) { data, response, error in
    // Handle response
}
task.resume()
```

## WebSocket Connection

### Android (OkHttp)

```kotlin
val request = Request.Builder()
    .url("ws://192.168.1.100:8000/ws/telemetry")
    .build()

val client = OkHttpClient()
val ws = client.newWebSocket(request, object : WebSocketListener() {
    override fun onMessage(webSocket: WebSocket, text: String) {
        // Parse JSON telemetry data
        val data = Gson().fromJson(text, TelemetryData::class.java)
    }
})
```

### iOS (URLSessionWebSocketTask)

```swift
let url = URL(string: "ws://192.168.1.100:8000/ws/telemetry")!
let ws = URLSession.shared.webSocketTask(with: url)
ws.resume()

// Receive messages
ws.receive { result in
    switch result {
    case .success(let message):
        if case .string(let text) = message {
            // Parse JSON telemetry data
        }
    case .failure(let error):
        print("Error: \(error)")
    }
}
```

## Key Endpoints for Mobile Apps

### 1. Real-time Telemetry
- **WebSocket**: `ws://<server-ip>:8000/ws/telemetry`
- **REST**: `GET /api/telemetry/current`

### 2. Configuration Changes
- **POST** `/api/config/change` - Apply config change with AI warnings

### 3. AI Advisor
- **POST** `/api/ai/ask` - Ask Q questions
- **GET** `/api/ai/suggestions` - Get question suggestions

### 4. Backup Management
- **POST** `/api/backup/create` - Create backup
- **GET** `/api/backup/list` - List backups
- **POST** `/api/backup/revert/{file_path}/{backup_id}` - Revert to backup

### 5. Hardware Control
- **GET** `/api/hardware/interfaces` - List hardware
- **GET/POST** `/api/hardware/gpio/{interface_id}/{pin}` - GPIO control

### 6. Camera Feeds
- **GET** `/api/cameras` - List cameras
- **GET** `/api/cameras/{device_id}/preview` - Camera preview (JPEG)

## Testing with curl

### Get Current Telemetry
```bash
curl http://localhost:8000/api/telemetry/current
```

### Apply Configuration Change
```bash
curl -X POST http://localhost:8000/api/config/change \
  -H "Content-Type: application/json" \
  -d '{
    "change_type": "ecu_tuning",
    "category": "Ignition Timing",
    "parameter": "base_timing",
    "new_value": 32.0,
    "old_value": 28.0
  }'
```

### Ask AI Advisor
```bash
curl -X POST http://localhost:8000/api/ai/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I configure boost control?",
    "context": {}
  }'
```

## Desktop App Integration

The desktop app automatically connects to the mobile API server when running. Telemetry data is pushed to the server in real-time.

To verify desktop app is connected:
1. Start the mobile API server
2. Start the desktop app (`python demo.py`)
3. Check `/api/system/status` - should show active telemetry updates

## Troubleshooting

### Server Won't Start
- Check if port 8000 is already in use
- Verify Python dependencies are installed
- Check firewall settings

### Mobile App Can't Connect
- Verify server IP address is correct
- Check both devices are on same network
- Verify firewall allows port 8000
- Test with `curl` from mobile device (if possible)

### WebSocket Connection Fails
- Verify WebSocket URL uses `ws://` (not `http://`)
- Check server logs for connection errors
- Ensure WebSocket support in mobile app framework

## Security Notes

⚠️ **Current Implementation**: No authentication required

**For Production:**
1. Implement JWT authentication
2. Restrict CORS origins
3. Add rate limiting
4. Use HTTPS/WSS
5. Add API key authentication

## Next Steps

1. **Start the server**: `python api/mobile_api_start.py`
2. **Test connection**: Visit http://localhost:8000/docs
3. **Connect mobile app**: Use your server's IP address
4. **Monitor telemetry**: Connect via WebSocket for real-time data

## Full Documentation

See [MOBILE_API_DOCUMENTATION.md](./MOBILE_API_DOCUMENTATION.md) for complete API reference.
















