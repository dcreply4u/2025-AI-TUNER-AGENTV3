#!/bin/bash
# Enable SSH on Raspberry Pi 5
# Run this script on the Pi itself (via keyboard/monitor or if you have another way in)

echo "🔧 Enabling SSH on Raspberry Pi 5..."

# Enable SSH service
sudo systemctl enable ssh
sudo systemctl start ssh

# Check status
echo "📊 SSH Status:"
sudo systemctl status ssh --no-pager

# Check if SSH is listening
echo ""
echo "🌐 Network Status:"
ss -tlnp | grep :22 || echo "SSH not listening on port 22"

# Show IP address
echo ""
echo "📍 Your IP address:"
hostname -I

echo ""
echo "✅ SSH should now be enabled!"
echo "   Try connecting from your computer:"
echo "   ssh aituner@$(hostname -I | awk '{print $1}')"







