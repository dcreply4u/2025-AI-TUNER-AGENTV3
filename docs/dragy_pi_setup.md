## Dragy-Style Pi HUD

### Hardware Checklist
- Raspberry Pi 4/5 with 64-bit OS
- USB or UART GNSS puck (10 Hz recommended)
- Optional: IMU for smoothing + CAN bridge for speed cross-check
- Sunlight-readable HDMI screen + 12V-to-5V converter

### Software Install
```bash
sudo apt update
sudo apt install python3-pip unclutter
pip install -r requirements.txt
```

Enable serial if you use `/dev/ttyAMA0`:
```bash
sudo raspi-config  # Interface Options → Serial → disable shell, enable hardware
```

### Launch the HUD
```bash
cd /path/to/AI-TUNER-AGENT
python -m ui.dragy_main
```

Set the app to start on boot (systemd example):
```bash
sudo tee /etc/systemd/system/dragy.service <<'EOF'
[Unit]
Description=AI Tuner Dragy HUD
After=network-online.target

[Service]
User=pi
WorkingDirectory=/home/pi/AI-TUNER-AGENT
Environment=QT_QPA_PLATFORM=eglfs
ExecStart=/usr/bin/python3 -m ui.dragy_main
Restart=always

[Install]
WantedBy=graphical.target
EOF

sudo systemctl enable --now dragy.service
```

### Tips
- Use `QT_QPA_PLATFORM=eglfs` for fullscreen kiosk without X11.
- Tweak `interfaces/GpsInterface` port/baud to match your receiver.
- Performance results live in `data_logs/performance_runs.json`; sync them when online. 

