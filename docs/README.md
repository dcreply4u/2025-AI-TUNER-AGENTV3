# AI Tuner Agent - Documentation

## Quick Links

- **Quick Start (Desktop Demo)**: [QUICK_START.md](../QUICK_START.md)
- **Architecture & Services**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Optimization Summary**: [OPTIMIZATION_OPPORTUNITIES.md](OPTIMIZATION_OPPORTUNITIES.md)
- **Virtual Dyno Enhancements**: [DYNO_ENHANCEMENTS_SUMMARY.md](DYNO_ENHANCEMENTS_SUMMARY.md)
- **Windows Laptop Edition**:
  - [WINDOWS_IMPLEMENTATION_SUMMARY.md](WINDOWS_IMPLEMENTATION_SUMMARY.md)
  - [WINDOWS_PORTING_GUIDE.md](WINDOWS_PORTING_GUIDE.md)
  - [WINDOWS_LAPTOP_VERSION_OPTIONS.md](WINDOWS_LAPTOP_VERSION_OPTIONS.md)
- **Fuel Modules**:
  - [METHANOL_MODULE.md](METHANOL_MODULE.md)
  - [NITROMETHANE_MODULE.md](NITROMETHANE_MODULE.md)
- **Advanced Tuning**:
  - [ADVANCED_TUNING_LOGIC.md](ADVANCED_TUNING_LOGIC.md)
- **Licensing & Protection**:
  - [LICENSING_OPTIONS.md](LICENSING_OPTIONS.md)
  - [LICENSING_QUICK_REFERENCE.md](LICENSING_QUICK_REFERENCE.md)
  - [YUBIKEY_INTEGRATION.md](YUBIKEY_INTEGRATION.md)
- **Mobile Apps**:
  - [MOBILE_API_DOCUMENTATION.md](MOBILE_API_DOCUMENTATION.md)
  - [MOBILE_APP_QUICK_START.md](MOBILE_APP_QUICK_START.md)
- **Setup Guides**:
  - [RETERMINAL_DM_SETUP.md](RETERMINAL_DM_SETUP.md)
  - [RETERMINAL_DM_QUICKSTART.md](RETERMINAL_DM_QUICKSTART.md)

## Documentation Structure

### Architecture & Design
- **ARCHITECTURE.md**: Complete system architecture
- **INTELLECTUAL_PROPERTY.md**: IP assets and competitive advantages

### Setup & Configuration
- **RETERMINAL_DM_SETUP.md**: Detailed reTerminal DM setup
- **RETERMINAL_DM_QUICKSTART.md**: Quick reference guide

### Development
- FastAPI mobile API server (`api/mobile_api_server.py`)
- Flutter + PWA mobile clients (`mobile_apps/`)
- Windows hardware adapter + installer (`interfaces/windows_hardware_adapter.py`, `installer/`)
- Virtual Dyno logging, session export, and air density improvements
- Advanced tuning engine with multi-objective optimization, predictive modeling, and closed-loop control
- Code is fully type-hinted and documented with inline comments

## Getting Started

### For Users
1. Read [QUICK_START.md](../QUICK_START.md) to launch the desktop demo
2. Use [MOBILE_APP_QUICK_START.md](MOBILE_APP_QUICK_START.md) to connect Flutter/PWA builds
3. See [VIRTUAL_DYNO_GUIDE.md](VIRTUAL_DYNO_GUIDE.md) for horsepower logging
4. Review setup guides for your hardware target (reTerminal, Windows laptop, etc.)

### For Developers
1. Read [ARCHITECTURE.md](ARCHITECTURE.md) for core services
2. Review [MOBILE_API_DOCUMENTATION.md](MOBILE_API_DOCUMENTATION.md) for REST/WebSocket integration
3. Check [WINDOWS_PORTING_GUIDE.md](WINDOWS_PORTING_GUIDE.md) before deploying on laptops
4. Use [DYNO_ENHANCEMENTS_SUMMARY.md](DYNO_ENHANCEMENTS_SUMMARY.md) when editing horsepower logic

### For Investors/Acquirers
1. See `../assessment/` for investor packets
2. Review [WINDOWS_IMPLEMENTATION_SUMMARY.md](WINDOWS_IMPLEMENTATION_SUMMARY.md) for market expansion
3. Check [INTELLECTUAL_PROPERTY.md](INTELLECTUAL_PROPERTY.md) for IP protections

## Support

For questions or issues:
- Check documentation first
- Review code comments
- See architecture docs
- Check test examples

