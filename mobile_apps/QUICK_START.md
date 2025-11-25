# TelemetryIQ Mobile - Quick Start Guide

Get both mobile apps running in 5 minutes!

## Prerequisites

1. **TelemetryIQ API Server Running**
   ```bash
   cd AI-TUNER-AGENT
   python api/mobile_api_start.py
   ```

2. **Find Your Server IP**
   - Windows: `ipconfig` → Look for "IPv4 Address"
   - Mac/Linux: `ifconfig` → Look for "inet"

## Option 1: PWA (Fastest - 2 minutes)

1. **Update IP Address**
   ```bash
   # Edit mobile_apps/pwa_telemetryiq_mobile/js/app.js
   # Change: const API_BASE_URL = 'http://192.168.1.100:8000';
   # To: const API_BASE_URL = 'http://YOUR_IP:8000';
   ```

2. **Start Web Server**
   ```bash
   cd mobile_apps/pwa_telemetryiq_mobile
   python -m http.server 8080
   ```

3. **Open in Browser**
   - Desktop: `http://localhost:8080`
   - Mobile: `http://YOUR_IP:8080`

4. **Install to Home Screen** (Optional)
   - Android: Chrome menu → "Add to Home screen"
   - iOS: Safari share → "Add to Home Screen"

**Done!** 🎉

## Option 2: Flutter (5 minutes)

1. **Install Flutter** (if not installed)
   ```bash
   # Download from https://flutter.dev
   flutter doctor
   ```

2. **Update IP Address**
   ```bash
   # Edit these files in mobile_apps/flutter_telemetryiq_mobile/lib/:
   # - main.dart
   # - providers/telemetry_provider.dart
   # - services/api_service.dart
   # - services/websocket_service.dart
   # 
   # Replace 192.168.1.100 with YOUR_IP
   ```

3. **Get Dependencies**
   ```bash
   cd mobile_apps/flutter_telemetryiq_mobile
   flutter pub get
   ```

4. **Run App**
   ```bash
   flutter run
   ```

**Done!** 🎉

## Testing Connection

1. **Check API Server**
   - Open: `http://YOUR_IP:8000/health`
   - Should show: `{"status": "healthy"}`

2. **Check Mobile App**
   - Connection indicator should turn green
   - Telemetry data should appear
   - If not, check IP address is correct

## Common Issues

### "Connection Failed"
- ✅ API server running? (`python api/mobile_api_start.py`)
- ✅ IP address correct?
- ✅ Same network?
- ✅ Firewall allowing port 8000?

### "No Telemetry Data"
- ✅ Desktop app running? (pushes telemetry to API)
- ✅ WebSocket connected? (check indicator)
- ✅ Try refreshing

### Flutter Build Errors
```bash
flutter clean
flutter pub get
flutter run
```

## Next Steps

- Customize UI colors in theme files
- Add more features
- Deploy to app stores (Flutter)
- Deploy to web hosting (PWA)

## Need Help?

- [Mobile API Documentation](../docs/MOBILE_API_DOCUMENTATION.md)
- [Flutter README](flutter_telemetryiq_mobile/README.md)
- [PWA README](pwa_telemetryiq_mobile/README.md)
















