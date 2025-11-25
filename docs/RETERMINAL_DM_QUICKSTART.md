# reTerminal DM Quick Start

## Hardware Detection

The AI Tuner Agent automatically detects the reTerminal DM platform and configures:
- **Dual CAN FD buses** (can0 and can1)
- **10.1" touchscreen** (1280x800)
- **Physical buttons** (Home, Back, Function)
- **Wide voltage power** (9-36V DC)

## Quick Setup

1. **Flash CM4** with Raspberry Pi OS (64-bit recommended)

2. **Enable CAN interfaces**:
   ```bash
   sudo python3 tools/setup_can_reterminal.py
   # Choose option 1 to bring up interfaces
   ```

3. **Install dependencies**:
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip can-utils
   pip3 install -r requirements.txt
   ```

4. **Verify hardware detection**:
   ```bash
   python3 -c "from core import get_hardware_config; print(get_hardware_config())"
   ```

5. **Launch UI**:
   ```bash
   python3 -m ui.main
   ```

## CAN Interface Usage

The reTerminal DM has **two CAN buses** available:

- **can0** - Primary CAN bus (default)
- **can1** - Secondary CAN bus

Both are automatically detected and can be used simultaneously. Configure in `config.py`:

```python
CAN_CHANNEL = "can0"  # Primary
CAN_CHANNEL_SECONDARY = "can1"  # Secondary (auto-detected)
```

## Display

The 10.1" touchscreen is automatically configured. The UI will use the full screen resolution (1280x800).

## Physical Buttons

Button mappings (can be customized):
- **Home** (GPIO5) - Return to main screen
- **Back** (GPIO6) - Navigation back
- **Function** (GPIO13) - Quick action

## Troubleshooting

**CAN interfaces not showing?**
```bash
# Check if interfaces exist
ip link show

# Check kernel messages
dmesg | grep -i can

# Manually bring up
sudo ip link set can0 up type can bitrate 500000
sudo ip link set can1 up type can bitrate 500000
```

**Display issues?**
```bash
# Check display
xrandr

# Check touchscreen
xinput list
```

## Auto-start on Boot

See `docs/RETERMINAL_DM_SETUP.md` for systemd service configuration.

## More Information

- Full setup guide: `docs/RETERMINAL_DM_SETUP.md`
- Seeed documentation: https://wiki.seeedstudio.com/reTerminal-DM/

