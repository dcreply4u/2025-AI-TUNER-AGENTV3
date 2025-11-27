#!/bin/bash
# Diagnostic script for ElectroCookie PCIe NVMe M.2 HAT detection on Raspberry Pi 5

set -e

echo "=========================================="
echo "NVMe M.2 Drive Diagnostic Script"
echo "=========================================="
echo ""

echo "1. Checking PCIe bus status..."
echo "----------------------------------------"
lspci -tv
echo ""

echo "2. Checking for NVMe devices..."
echo "----------------------------------------"
ls -la /dev/nvme* 2>&1 || echo "No NVMe devices found in /dev/"
echo ""

echo "3. Checking PCIe devices..."
echo "----------------------------------------"
lspci -nn | grep -i nvme || echo "No NVMe devices in PCIe bus"
echo ""

echo "4. Checking NVMe kernel modules..."
echo "----------------------------------------"
lsmod | grep -i nvme || echo "NVMe modules not loaded"
echo ""

echo "5. Loading NVMe modules..."
echo "----------------------------------------"
sudo modprobe nvme 2>&1 || echo "Failed to load nvme module"
sudo modprobe nvme-core 2>&1 || echo "Failed to load nvme-core module"
sleep 2
echo ""

echo "6. Re-checking for NVMe devices after module load..."
echo "----------------------------------------"
ls -la /dev/nvme* 2>&1 || echo "Still no NVMe devices found"
lspci | grep -i nvme || echo "Still no NVMe devices in PCIe bus"
echo ""

echo "7. Recent PCIe-related kernel messages..."
echo "----------------------------------------"
dmesg | grep -iE 'pcie|nvme' | tail -20
echo ""

echo "8. Checking PCIe link status..."
echo "----------------------------------------"
dmesg | grep -i 'pcie.*link' | tail -5
echo ""

echo "9. Checking for any PCIe errors..."
echo "----------------------------------------"
dmesg | grep -iE 'pcie.*error|pcie.*fail' || echo "No PCIe errors found"
echo ""

echo "=========================================="
echo "Diagnostic Complete"
echo "=========================================="
echo ""
echo "If no NVMe device is detected, check:"
echo "  1. ElectroCookie HAT is properly connected to Pi 5 PCIe connector"
echo "  2. M.2 SSD is fully seated in the HAT's M.2 slot"
echo "  3. SSD is compatible (not SMI2263XT, SMI2263EN, MAP1202, Phison)"
echo "  4. Pi 5 has sufficient power supply (5V 5A recommended)"
echo "  5. FFC ribbon cable is properly connected"
echo ""

