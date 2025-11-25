# AI Tuner Agent

**AI-Powered Racing Telemetry and Tuning System**

A comprehensive edge computing platform for real-time vehicle telemetry, AI-driven tuning advice, performance tracking, and advanced racing analytics. Built for the reTerminal DM and compatible with Raspberry Pi 5.

## 🚀 Features

### Core Capabilities
- **Real-time Telemetry**: OBD-II, RaceCapture, and CAN bus integration
- **AI-Powered Insights**: Predictive fault detection, tuning advisor, and conversational agent
- **Performance Tracking**: Dragy-style 0-60, quarter-mile, and lap timing with GPS
- **Multi-Camera Support**: Front/rear camera recording with customizable telemetry overlays
- **Voice Control**: Voice commands, responses, and proactive feedback
- **Live Streaming**: Direct streaming to YouTube and RTMP services
- **Auto USB Detection**: Automatic USB storage detection and configuration

### Modern Racing UI
- **Customizable Dashboard**: Digital gauges, warning indicators, and real-time data display
- **Floating AI Advisor**: Always-accessible AI assistant with chat overlay
- **Voice Commands**: Hands-free operation with speech recognition
- **Map Comparison**: Side-by-side and overlay comparison of tuning maps
- **Haptic Feedback**: Tactile feedback for critical actions
- **Panic Button**: Emergency safe stock map flash
- **Connection Status**: Visual indicators for hardware connectivity

### Advanced Features
- **AI Racing Coach**: Real-time coaching with optimal driving line suggestions
- **Auto-Tuning Engine**: AI-driven automatic ECU parameter optimization
- **Predictive Parts Ordering**: Predict failures and auto-order replacements
- **Blockchain-Verified Records**: Tamper-proof performance records
- **Fleet Management**: Manage and compare multiple vehicles
- **Social Racing Platform**: Leaderboards, challenges, and achievements
- **AR Racing Overlay**: Augmented reality telemetry overlays
- **Boost & Nitrous Advisor**: Monitor and optimize boost/nitrous levels

### Hardware Support
- **reTerminal DM** (Primary platform)
- **Raspberry Pi 5**
- **Jetson Nano** (with modifications)
- Onboard CAN bus support
- GPS, Bluetooth, Wi-Fi, 4G LTE
- Multiple USB/Wi-Fi cameras

## 📋 Quick Start

### Prerequisites
- Python 3.9+
- reTerminal DM or compatible hardware
- CAN bus interface (onboard or USB)

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/ai-tuner-agent.git
cd ai-tuner-agent

# Install dependencies
pip install -r requirements.txt

# Run demo (no hardware required)
python demo.py

# Run full application
python ui/main.py
```

### Windows Quick Start
```bash
# See QUICK_START_WINDOWS.md for detailed instructions
python demo.py --no-voice
```

## 📖 Documentation

- [Quick Start Guide](QUICK_START.md)
- [reTerminal DM Setup](docs/RETERMINAL_DM_SETUP.md)
- [Hardware Connections](docs/HARDWARE_CONNECTIONS.md)
- [CAN Bus Guide](docs/CAN_BUS_GUIDE.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Unique Features](docs/UNIQUE_FEATURES.md)

## 🎯 Use Cases

- **Drag Racing**: 0-60, quarter-mile timing, launch control
- **Track Racing**: Lap timing, GPS trace recording, racing line analysis
- **Street Tuning**: Real-time ECU monitoring, AI tuning advice
- **Fleet Management**: Multi-vehicle performance comparison
- **Live Streaming**: Broadcast racing sessions with telemetry overlays

## 🛠️ Project Structure

```
AI-TUNER-AGENT/
├── ai/                 # AI modules (fault detection, tuning advisor)
├── controllers/        # Data stream and camera controllers
├── core/              # Core platform (hardware detection, config)
├── interfaces/        # Hardware interfaces (OBD, CAN, GPS, cameras)
├── services/          # Services (logging, cloud sync, analytics)
├── ui/                # PySide6 GUI components
├── tests/             # Unit and integration tests
└── docs/              # Documentation
```

## 🔧 Configuration

Configuration is managed through `config.py` and hardware-specific settings are auto-detected. See [docs/RETERMINAL_DM_SETUP.md](docs/RETERMINAL_DM_SETUP.md) for platform-specific setup.

## 🤝 Contributing

This is a Kickstarter project. Contributions and feedback are welcome!

## 📄 License

[Add your license here]

## 🙏 Acknowledgments

Built for the racing community. Special thanks to all beta testers and contributors.

---

**Status**: Active Development | **Platform**: reTerminal DM / Raspberry Pi 5 | **Language**: Python 3.9+

