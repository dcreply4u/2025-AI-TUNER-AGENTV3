# Enable SSH on Raspberry Pi 5

**If SSH connection is refused, follow these steps:**

## Option 1: Enable SSH via Command Line (If you have keyboard/monitor)

1. **Connect keyboard and monitor to your Pi 5**

2. **Log in** with username `aituner` and password `aituner`

3. **Run these commands:**
   ```bash
   sudo systemctl enable ssh
   sudo systemctl start ssh
   sudo systemctl status ssh
   ```

4. **Verify SSH is running:**
   ```bash
   ss -tlnp | grep :22
   ```

5. **Try connecting from your Windows computer:**
   ```powershell
   ssh aituner@192.168.1.214
   ```

---

## Option 2: Enable SSH via raspi-config

1. **On the Pi (keyboard/monitor):**
   ```bash
   sudo raspi-config
   ```

2. **Navigate to:**
   - **Interface Options** → **SSH** → **Yes**

3. **Reboot:**
   ```bash
   sudo reboot
   ```

---

## Option 3: Enable SSH via Desktop (If you have desktop installed)

1. **Open Raspberry Pi Configuration:**
   - Menu → Preferences → Raspberry Pi Configuration

2. **Go to Interfaces tab**

3. **Enable SSH** checkbox

4. **Click OK** and reboot

---

## Option 4: Enable SSH Remotely (If you have another way in)

If you have access via VNC, web interface, or another method:

```bash
sudo systemctl enable ssh
sudo systemctl start ssh
```

---

## Verify SSH is Working

From your Windows computer:

```powershell
# Test connection
ssh -v aituner@192.168.1.214

# Or with password (if using sshpass or similar)
ssh aituner@192.168.1.214
```

**Expected output:**
```
The authenticity of host '192.168.1.214' can't be established...
Are you sure you want to continue connecting (yes/no)? yes
aituner@192.168.1.214's password: [enter password]
```

---

## Troubleshooting

### Still can't connect?

1. **Check if Pi is on the network:**
   ```powershell
   ping 192.168.1.214
   ```

2. **Check if SSH port is open:**
   ```powershell
   Test-NetConnection -ComputerName 192.168.1.214 -Port 22
   ```

3. **Check firewall on Pi:**
   ```bash
   sudo ufw status
   # If enabled, allow SSH:
   sudo ufw allow 22/tcp
   ```

4. **Check SSH service status:**
   ```bash
   sudo systemctl status ssh
   ```

5. **View SSH logs:**
   ```bash
   sudo journalctl -u ssh -n 50
   ```

---

## Once SSH is Working

Proceed with the full setup:

```bash
# On your Pi (via SSH)
cd ~
git clone https://github.com/dcreply4u/ai-tuner-agent.git AI-TUNER-AGENT
cd AI-TUNER-AGENT
chmod +x scripts/*.sh
sudo ./scripts/pi5_setup.sh
```







