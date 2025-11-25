#!/bin/bash
#
# Raspberry Pi 5 Network Setup Script
# Helps configure WiFi and network settings for remote access
#
# Usage: sudo ./pi5_network_setup.sh
#

set -e

echo "=========================================="
echo "Raspberry Pi 5 Network Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Function to get current IP
get_ip() {
    hostname -I | awk '{print $1}'
}

# Function to show network interfaces
show_interfaces() {
    echo ""
    echo "Available network interfaces:"
    ip -4 addr show | grep -E "^[0-9]+:|inet " | sed 's/^[0-9]*: //' | sed 's/inet /  /'
}

# Show current network status
echo "Current network status:"
show_interfaces

CURRENT_IP=$(get_ip)
if [ -n "$CURRENT_IP" ]; then
    echo ""
    echo "Current IP address: $CURRENT_IP"
    echo "You can SSH to this Pi using:"
    echo "  ssh pi@$CURRENT_IP"
    echo "  or"
    echo "  ssh $USER@$CURRENT_IP"
else
    echo ""
    echo "⚠️  No IP address found. Network may not be configured."
fi

echo ""
echo "Network setup options:"
echo "1. Configure WiFi (wpa_supplicant)"
echo "2. Set static IP address"
echo "3. Enable SSH (if not already enabled)"
echo "4. Show network information"
echo "5. Test network connectivity"
echo "6. Exit"
echo ""

read -p "Select option (1-6): " choice

case $choice in
    1)
        echo ""
        echo "WiFi Configuration"
        echo "=================="
        read -p "SSID (network name): " ssid
        read -sp "Password: " password
        echo ""
        
        WPA_FILE="/etc/wpa_supplicant/wpa_supplicant.conf"
        
        # Backup original
        if [ -f "$WPA_FILE" ]; then
            cp "$WPA_FILE" "${WPA_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        fi
        
        # Add network
        cat >> "$WPA_FILE" << EOF

network={
    ssid="$ssid"
    psk="$password"
}
EOF
        
        echo "WiFi configuration added to $WPA_FILE"
        echo "Restarting WiFi..."
        wpa_cli -i wlan0 reconfigure 2>/dev/null || systemctl restart networking
        
        echo "WiFi configured. It may take a moment to connect."
        ;;
    
    2)
        echo ""
        echo "Static IP Configuration"
        echo "======================="
        read -p "IP address (e.g., 192.168.1.100): " static_ip
        read -p "Gateway (e.g., 192.168.1.1): " gateway
        read -p "Netmask (e.g., 255.255.255.0): " netmask
        read -p "DNS server (e.g., 8.8.8.8): " dns
        
        INTERFACE=$(ip route | grep default | awk '{print $5}' | head -1)
        
        if [ -z "$INTERFACE" ]; then
            echo "Could not determine network interface"
            exit 1
        fi
        
        DHCPCD_FILE="/etc/dhcpcd.conf"
        
        # Backup
        if [ -f "$DHCPCD_FILE" ]; then
            cp "$DHCPCD_FILE" "${DHCPCD_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        fi
        
        # Add static IP configuration
        cat >> "$DHCPCD_FILE" << EOF

# Static IP configuration for $INTERFACE
interface $INTERFACE
static ip_address=$static_ip/$netmask
static routers=$gateway
static domain_name_servers=$dns
EOF
        
        echo "Static IP configured in $DHCPCD_FILE"
        echo "Restart networking to apply: sudo systemctl restart dhcpcd"
        ;;
    
    3)
        echo ""
        echo "Enabling SSH..."
        systemctl enable ssh
        systemctl start ssh
        echo "✅ SSH enabled and started"
        echo ""
        echo "To connect from another computer:"
        IP=$(get_ip)
        if [ -n "$IP" ]; then
            echo "  ssh $USER@$IP"
        else
            echo "  ssh $USER@<pi-ip-address>"
        fi
        ;;
    
    4)
        echo ""
        echo "Network Information"
        echo "=================="
        echo ""
        echo "Hostname: $(hostname)"
        echo ""
        echo "IP Addresses:"
        hostname -I
        echo ""
        echo "Network Interfaces:"
        show_interfaces
        echo ""
        echo "Routing Table:"
        ip route
        echo ""
        echo "DNS Servers:"
        cat /etc/resolv.conf | grep nameserver
        ;;
    
    5)
        echo ""
        echo "Testing Network Connectivity"
        echo "============================"
        echo ""
        echo "Testing internet connectivity..."
        if ping -c 3 8.8.8.8 > /dev/null 2>&1; then
            echo "✅ Internet connectivity: OK"
        else
            echo "❌ Internet connectivity: FAILED"
        fi
        
        echo ""
        echo "Testing DNS..."
        if ping -c 3 google.com > /dev/null 2>&1; then
            echo "✅ DNS resolution: OK"
        else
            echo "❌ DNS resolution: FAILED"
        fi
        
        echo ""
        echo "Local network test..."
        GATEWAY=$(ip route | grep default | awk '{print $3}' | head -1)
        if [ -n "$GATEWAY" ]; then
            if ping -c 2 "$GATEWAY" > /dev/null 2>&1; then
                echo "✅ Gateway ($GATEWAY) reachable: OK"
            else
                echo "❌ Gateway ($GATEWAY) not reachable"
            fi
        fi
        ;;
    
    6)
        echo "Exiting..."
        exit 0
        ;;
    
    *)
        echo "Invalid option"
        exit 1
        ;;
esac

echo ""
echo "Setup complete!"



