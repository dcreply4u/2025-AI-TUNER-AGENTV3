# TelemetryIQ Mobile Apps

Complete mobile app implementations for TelemetryIQ - both Flutter and PWA versions that match the desktop UI theme exactly.

## 📱 Apps Included

### 1. Flutter App (`flutter_telemetryiq_mobile/`)
- Native Android/iOS app
- Matches TelemetryIQ desktop UI theme
- Real-time telemetry via WebSocket
- Configuration management
- AI Advisor integration

### 2. PWA (`pwa_telemetryiq_mobile/`)
- Progressive Web App
- Works on all platforms (Android, iOS, Desktop)
- Same features as Flutter app
- Installable from browser

## 🎨 UI Theme

Both apps use the **exact same theme** as the desktop TelemetryIQ interface:

- **Background**: Deep black (#0a0a0a), Dark charcoal (#1a1a1a)
- **Accent Colors**: Electric blue (#00e0ff), Vibrant orange (#ff8000), Vivid red (#ff0000)
- **Status Colors**: Green (optimal), Electric blue (adjustable), Red (critical)
- **Typography**: Segoe UI font family
- **Design**: High-contrast, industrial realism aesthetic

## 🚀 Quick Start

### Flutter App

```bash
cd flutter_telemetryiq_mobile
flutter pub get
flutter run
```

**Update API URL** in `lib/main.dart`:
```dart
APIService(baseUrl: 'http://YOUR_SERVER_IP:8000')
```

### PWA

1. Start TelemetryIQ API server:
```bash
python api/mobile_api_start.py
```

2. Open `pwa_telemetryiq_mobile/index.html` in a browser

3. Or serve with a web server:
```bash
cd pwa_telemetryiq_mobile
python -m http.server 8080
```

4. Open `http://localhost:8080` in browser

**Update API URL** in `js/app.js`:
```javascript
const API_BASE_URL = 'http://YOUR_SERVER_IP:8000';
```

## 📋 Features

Both apps include:

- ✅ Real-time telemetry dashboard
- ✅ WebSocket streaming (10 Hz updates)
- ✅ Telemetry gauges (RPM, Boost, AFR, Coolant)
- ✅ Configuration management
- ✅ AI Advisor "Q" chat
- ✅ Configuration history
- ✅ Proactive warnings on config changes
- ✅ Connection status indicator
- ✅ TelemetryIQ racing theme

## 🔧 Configuration

### API Server URL

**Flutter**: Edit `lib/main.dart` and `lib/providers/telemetry_provider.dart`

**PWA**: Edit `js/app.js`

Replace `192.168.1.100` with your actual server IP address.

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

## 📦 Dependencies

### Flutter
- `http: ^1.1.0` - REST API calls
- `web_socket_channel: ^2.4.0` - WebSocket support
- `provider: ^6.1.1` - State management

### PWA
- No dependencies - pure JavaScript
- Works in all modern browsers

## 🎯 Next Steps

1. **Start API Server**: `python api/mobile_api_start.py`
2. **Update IP Address**: Replace `192.168.1.100` with your server IP
3. **Run Flutter App**: `flutter run` (for native)
4. **Open PWA**: Open `index.html` in browser (for web)

## 📱 Platform Support

### Flutter
- ✅ Android 5.0+
- ✅ iOS 11.0+
- ✅ Native performance

### PWA
- ✅ Android (Chrome, Firefox, Edge)
- ✅ iOS (Safari 11.3+)
- ✅ Desktop browsers
- ✅ Installable to home screen

## 🎨 Theme Colors Reference

```dart
// Flutter
Color(0xFF0A0A0A)  // BG_PRIMARY
Color(0xFF1A1A1A)  // BG_SECONDARY
Color(0xFF00E0FF)  // ACCENT_NEON_BLUE
Color(0xFFFF8000)  // ACCENT_NEON_ORANGE
Color(0xFFFF0000)  // ACCENT_NEON_RED
Color(0xFF00FF00)  // STATUS_OPTIMAL
```

```css
/* PWA */
--bg-primary: #0a0a0a;
--bg-secondary: #1a1a1a;
--accent-neon-blue: #00e0ff;
--accent-neon-orange: #ff8000;
--accent-neon-red: #ff0000;
--status-optimal: #00ff00;
```

## 📚 Documentation

- [Mobile API Documentation](../docs/MOBILE_API_DOCUMENTATION.md)
- [Mobile App Development Options](../docs/MOBILE_APP_DEVELOPMENT_OPTIONS.md)
- [Flutter & PWA Runtime Explained](../docs/FLUTTER_PWA_RUNTIME_EXPLAINED.md)
















