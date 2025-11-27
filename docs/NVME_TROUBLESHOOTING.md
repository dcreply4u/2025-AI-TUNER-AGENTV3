# NVMe M.2 Drive Troubleshooting Guide

## ElectroCookie PCIe NVMe M.2 HAT for Raspberry Pi 5

### Current Status
- ✅ PCIe link is active (5.0 GT/s x4)
- ✅ RP1 South Bridge detected
- ❌ NVMe device not detected on PCIe bus
- ❌ No `/dev/nvme*` devices found

### Physical Connection Checklist

#### 1. FFC Ribbon Cable Connection
- **Check**: The FFC (Flat Flexible Cable) ribbon must be properly inserted into the Pi 5's PCIe connector
- **Location**: The PCIe connector is on the bottom of the Pi 5 board
- **Action**: 
  - Power off the Pi 5
  - Remove and re-seat the FFC ribbon cable
  - Ensure the cable is fully inserted and the locking mechanism is engaged
  - The cable should be straight, not twisted or kinked

#### 2. M.2 SSD Installation
- **Check**: The M.2 SSD must be fully seated in the HAT's M.2 slot
- **Action**:
  - Power off the Pi 5
  - Remove the HAT from the Pi
  - Remove and re-insert the M.2 SSD
  - Ensure the SSD is pushed all the way in until it clicks or sits flush
  - Secure with the mounting screw if provided

#### 3. Power Supply
- **Requirement**: Raspberry Pi 5 needs a **5V 5A power supply** minimum
- **Check**: Your power supply must provide sufficient power for both the Pi and the NVMe drive
- **Action**: Use the official Raspberry Pi 5 power supply or equivalent (5V 5A)

#### 4. SSD Compatibility
**Known Incompatible SSD Controllers:**
- SMI2263XT
- SMI2263EN
- MAP1202
- Phison series controllers

**Known Incompatible SSDs:**
- Inland TN446
- Corsair MP600
- Micron 2450
- Kingston OM8SEP4256Q-A0
- WD Blue SN550 / SN580
- WD Green SN350
- WD Black SN850 / SN770
- Kingspec series

**Action**: Check your SSD model and controller. If it's on the incompatible list, you may need a different SSD.

#### 5. HAT Orientation
- **Check**: The HAT must be properly oriented on the Pi 5
- **Action**: Ensure the HAT is correctly aligned with the GPIO header and PCIe connector

### Diagnostic Commands

Run these commands to check the current status:

```bash
# Check PCIe bus
lspci -tv

# Check for NVMe devices
ls -la /dev/nvme*

# Load NVMe modules and check again
sudo modprobe nvme
sudo modprobe nvme-core
sleep 2
ls -la /dev/nvme*
lspci | grep -i nvme

# Check PCIe link status
dmesg | grep -i 'pcie.*link'

# Check for errors
dmesg | grep -iE 'pcie.*error|pcie.*fail'
```

### Expected Results When Working

When the NVMe drive is properly detected, you should see:

1. **PCIe Bus**: A second device on bus 0002 (e.g., `0002:02:00.0`)
2. **Device Type**: `Non-Volatile memory controller` or similar
3. **Device Files**: `/dev/nvme0`, `/dev/nvme0n1`, etc.
4. **Kernel Messages**: NVMe initialization messages in `dmesg`

Example of working detection:
```
0002:02:00.0 Non-Volatile memory controller: [vendor:device] NVMe SSD Controller
/dev/nvme0
/dev/nvme0n1
```

### Next Steps

1. **Power cycle**: Completely power off the Pi 5, wait 10 seconds, then power back on
2. **Re-seat connections**: Remove and re-insert both the FFC cable and M.2 SSD
3. **Check SSD compatibility**: Verify your SSD model is compatible
4. **Try different SSD**: If available, test with a known-compatible SSD
5. **Check HAT**: Inspect the ElectroCookie HAT for any physical damage

### If Still Not Detected

If after all physical checks the device is still not detected:

1. The HAT may be faulty
2. The FFC cable may be damaged
3. The SSD may be incompatible or faulty
4. There may be a Pi 5 hardware issue

Consider:
- Testing the HAT on another Pi 5 (if available)
- Testing a different compatible SSD
- Contacting ElectroCookie support

### Once Detected

Once the NVMe drive is detected, proceed with:

1. Run `scripts/setup_hard_drive.sh` to format and mount the drive
2. Run `scripts/copy_from_usb_to_hdd.sh` to copy project files
3. Run `scripts/setup_hdd_sync.sh` to set up synchronization
4. Run `scripts/migrate_to_hdd.sh` to run from the hard drive

