# TelemetryIQ Mobile - Flutter App

Professional ECU/TCU Tuning Interface for Android and iOS.

## Features

- ✅ Real-time telemetry streaming via WebSocket
- ✅ TelemetryIQ desktop UI theme matching
- ✅ Configuration management with AI warnings
- ✅ AI Advisor "Q" chat interface
- ✅ Configuration history
- ✅ Connection status monitoring
- ✅ High-performance native app

## Prerequisites

- Flutter SDK 3.0.0 or higher
- Android Studio (for Android development)
- Xcode (for iOS development, Mac only)

## Setup

1. **Install Flutter**
   ```bash
   # Download from https://flutter.dev/docs/get-started/install
   flutter doctor
   ```

2. **Get Dependencies**
   ```bash
   cd mobile_apps/flutter_telemetryiq_mobile
   flutter pub get
   ```

3. **Configure API Server**
   
   Update the API server URL in:
   - `lib/main.dart`
   - `lib/providers/telemetry_provider.dart`
   - `lib/services/api_service.dart`
   - `lib/services/websocket_service.dart`
   
   Replace `192.168.1.100` with your actual server IP address.

4. **Run the App**
   ```bash
   # Android
   flutter run
   
   # iOS (Mac only)
   flutter run -d ios
   
   # Specific device
   flutter devices
   flutter run -d <device-id>
   ```

## Building for Production

### Android APK
```bash
flutter build apk --release
# Output: build/app/outputs/flutter-apk/app-release.apk
```

### Android App Bundle (for Play Store)
```bash
flutter build appbundle --release
# Output: build/app/outputs/bundle/release/app-release.aab
```

### iOS (Mac only)
```bash
flutter build ios --release
# Then open in Xcode to archive and upload
```

## Project Structure

```
lib/
├── main.dart                 # App entry point
├── theme/
│   └── telemetryiq_colors.dart  # Theme colors
├── services/
│   ├── api_service.dart     # REST API client
│   └── websocket_service.dart   # WebSocket client
├── providers/
│   ├── telemetry_provider.dart  # Telemetry state
│   └── config_provider.dart     # Config state
├── screens/
│   ├── dashboard_screen.dart    # Main dashboard
│   ├── config_screen.dart       # Config management
│   └── ai_advisor_screen.dart   # AI chat
└── widgets/
    ├── telemetry_gauge.dart     # Gauge widget
    └── telemetry_grid.dart      # Telemetry grid
```

## API Integration

The app connects to TelemetryIQ Mobile API server:

- **REST API**: `http://YOUR_SERVER_IP:8000/api/`
- **WebSocket**: `ws://YOUR_SERVER_IP:8000/ws/telemetry`

See [Mobile API Documentation](../../docs/MOBILE_API_DOCUMENTATION.md) for complete API reference.

## Troubleshooting

### Connection Issues
- Verify API server is running: `python api/mobile_api_start.py`
- Check server IP address is correct
- Ensure device and server are on same network
- Check firewall settings

### Build Issues
```bash
flutter clean
flutter pub get
flutter run
```

### WebSocket Not Connecting
- Check server logs for WebSocket errors
- Verify WebSocket URL is correct
- Check network connectivity

## License

Part of TelemetryIQ project.
















