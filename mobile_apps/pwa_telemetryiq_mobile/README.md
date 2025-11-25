# TelemetryIQ Mobile - PWA

Progressive Web App version of TelemetryIQ Mobile. Works on all platforms with a single codebase.

## Features

- ✅ Real-time telemetry streaming via WebSocket
- ✅ TelemetryIQ desktop UI theme matching
- ✅ Configuration management with AI warnings
- ✅ AI Advisor "Q" chat interface
- ✅ Installable to home screen
- ✅ Offline support (Service Worker)
- ✅ Works on Android, iOS, and Desktop

## Quick Start

1. **Start TelemetryIQ API Server**
   ```bash
   python api/mobile_api_start.py
   ```

2. **Update API URL**
   
   Edit `js/app.js` and replace `192.168.1.100` with your server IP:
   ```javascript
   const API_BASE_URL = 'http://YOUR_SERVER_IP:8000';
   const WS_URL = 'ws://YOUR_SERVER_IP:8000/ws/telemetry';
   ```

3. **Serve the PWA**
   
   Option 1: Simple HTTP server
   ```bash
   cd mobile_apps/pwa_telemetryiq_mobile
   python -m http.server 8080
   ```
   
   Option 2: Node.js
   ```bash
   npx serve .
   ```
   
   Option 3: VS Code Live Server extension

4. **Open in Browser**
   - Desktop: `http://localhost:8080`
   - Mobile: `http://YOUR_SERVER_IP:8080`

5. **Install to Home Screen**
   - **Android (Chrome)**: Menu → "Add to Home screen"
   - **iOS (Safari)**: Share → "Add to Home Screen"

## File Structure

```
pwa_telemetryiq_mobile/
├── index.html           # Main HTML
├── manifest.json        # PWA manifest
├── sw.js                # Service Worker
├── styles/
│   ├── theme.css        # TelemetryIQ theme
│   └── components.css   # Component styles
└── js/
    ├── api.js           # REST API client
    ├── websocket.js     # WebSocket client
    └── app.js           # Main application
```

## PWA Features

### Installable
- Add to home screen on Android/iOS
- Standalone app experience
- No browser UI when installed

### Offline Support
- Service Worker caches app files
- Works offline (limited functionality)
- Automatic updates when online

### Responsive Design
- Works on phones, tablets, desktops
- Touch-friendly interface
- Optimized for mobile

## API Integration

The PWA connects to TelemetryIQ Mobile API server:

- **REST API**: `http://YOUR_SERVER_IP:8000/api/`
- **WebSocket**: `ws://YOUR_SERVER_IP:8000/ws/telemetry`

See [Mobile API Documentation](../../docs/MOBILE_API_DOCUMENTATION.md) for complete API reference.

## Browser Support

### Full Support
- Chrome 67+ (Android, Desktop)
- Edge 79+ (Android, Desktop)
- Safari 11.3+ (iOS, macOS)
- Firefox 60+ (Android, Desktop)

### Limited Support
- Older browsers may not support all PWA features
- WebSocket support required

## Troubleshooting

### Service Worker Not Registering
- Must be served over HTTPS (or localhost)
- Check browser console for errors
- Verify `sw.js` file exists

### WebSocket Not Connecting
- Check server is running
- Verify WebSocket URL is correct
- Check network/firewall settings
- Some networks block WebSocket connections

### Installation Not Available
- **Android**: Requires Chrome 67+
- **iOS**: Requires Safari 11.3+
- Must be served over HTTPS (or localhost)
- Must have valid `manifest.json`

### Styling Issues
- Clear browser cache
- Hard refresh (Ctrl+Shift+R / Cmd+Shift+R)
- Check CSS files are loading

## Development

### Local Development
```bash
# Simple server
python -m http.server 8080

# With HTTPS (for Service Worker testing)
# Use ngrok or similar for HTTPS tunnel
```

### Testing on Mobile Device
1. Find your computer's IP: `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
2. Start server: `python -m http.server 8080`
3. On mobile: Open `http://YOUR_IP:8080`

### Updating
- Changes are automatically reflected
- Service Worker updates in background
- Users get new version on next visit

## Performance Tips

- Service Worker caches static files
- WebSocket for real-time data (efficient)
- Minimal JavaScript footprint
- Optimized CSS (no frameworks)

## License

Part of TelemetryIQ project.
















