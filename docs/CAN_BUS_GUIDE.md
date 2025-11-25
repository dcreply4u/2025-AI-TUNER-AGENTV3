# CAN Bus Integration Guide

## Overview

The AI Tuner Agent includes a comprehensive, optimized CAN bus system with support for 100+ CAN IDs across multiple vendors, real-time monitoring, and advanced analysis capabilities.

## Features

### 1. Extended CAN ID Database
- **100+ CAN IDs** across 10+ vendors
- Holley, Haltech, AEM, Link, MegaSquirt, MoTec, Emtron, FuelTech, RaceCapture, OBD-II
- Racing-specific IDs (FlexFuel, Methanol, Nitrous, Transbrake)
- Automatic ID recognition and naming

### 2. Optimized Performance
- **High-speed message processing** with buffering
- **Multi-channel support** (dual CAN for reTerminal DM)
- **Message filtering** for reduced CPU usage
- **Statistics tracking** in real-time

### 3. Real-Time Monitoring
- Background monitoring threads
- Message callbacks for custom processing
- Statistics (messages/sec, bus load, error frames)
- Recent message buffer (last 1000 messages)

### 4. Advanced Analysis
- Bus load calculation
- Timing analysis per CAN ID
- Anomaly detection
- Protocol compliance checking
- Pattern recognition

## Usage

### Basic CAN Interface

```python
from interfaces import OptimizedCANInterface

# Initialize CAN interface
can_interface = OptimizedCANInterface(
    channel="can0",
    bitrate=500000,
    secondary_channel="can1",  # Optional for dual CAN
    message_callback=my_callback,  # Optional
    filter_ids={0x180, 0x181},  # Optional filter
)

# Connect and start monitoring
can_interface.connect()
can_interface.start_monitoring()

# Read messages
message = can_interface.read_message(timeout=1.0)
if message:
    print(f"CAN ID: 0x{message.arbitration_id:X}")
    print(f"Data: {message.data.hex()}")

# Get statistics
stats = can_interface.get_statistics()
print(f"Messages/sec: {stats.messages_per_second:.1f}")
print(f"Unique IDs: {len(stats.unique_ids)}")

# Stop monitoring
can_interface.stop_monitoring()
can_interface.disconnect()
```

### CAN Analyzer

```python
from services import CANAnalyzer
from interfaces import OptimizedCANInterface

# Initialize analyzer
analyzer = CANAnalyzer()

# Set up CAN interface with callback
def on_message(msg):
    analyzer.add_message(msg)

can_interface = OptimizedCANInterface(
    channel="can0",
    message_callback=on_message,
)
can_interface.start_monitoring()

# Perform analysis
analysis = analyzer.analyze()
print(f"Bus Load: {analysis.bus_load_percent:.1f}%")
print(f"Average Rate: {analysis.average_message_rate:.1f} msg/s")
print(f"Peak Rate: {analysis.peak_message_rate:.1f} msg/s")

# Check for anomalies
if analysis.anomalies:
    print("Anomalies detected:")
    for anomaly in analysis.anomalies:
        print(f"  - {anomaly}")
```

### Vendor Detection

```python
from services import CANVendorDetector

# Initialize detector
detector = CANVendorDetector(
    can_channel="can0",
    bitrate=500000,
)

# Detect vendor
vendor = detector.detect_vendor(sample_time=5.0)
print(f"Detected vendor: {vendor.value if vendor else 'Unknown'}")

# Load DBC file for detected vendor
if vendor:
    detector.load_dbc(vendor)
    
    # Decode messages
    decoded = detector.decode_message(can_id=0x180, data=b"\x01\x02\x03...")
    if decoded:
        print(f"Message: {decoded['name']}")
        print(f"Signals: {decoded['signals']}")
```

### CAN Monitor Tool

Use the command-line monitor tool:

```bash
# Basic monitoring
python -m tools.can_monitor --channel can0

# With filtering
python -m tools.can_monitor --channel can0 --filter 0x180 0x181

# List all known CAN IDs
python -m tools.can_monitor --list-ids

# Custom bitrate
python -m tools.can_monitor --channel can0 --bitrate 1000000
```

## Supported CAN IDs

### Holley EFI
- `0x180` - Engine Data (RPM, MAP, TPS)
- `0x181` - Temperature Data
- `0x182` - Fuel Data
- `0x183` - Ignition Data
- `0x184` - System Status
- `0x185` - Extended Parameters
- `0x186` - FlexFuel
- `0x187` - Boost Control

### Haltech
- `0x200-0x207` - Various ECU parameters

### AEM Infinity
- `0x300-0x305` - Engine, Fuel, Ignition, I/O

### Racing-Specific IDs
- `0x18FF65E5` - FlexFuel Percent (Ethanol Content)
- `0x18FF70E5` - Methanol Injection Duty
- `0x18FF75E5` - Methanol Tank Level
- `0x18EF12A0` - Nitrous Bottle Pressure
- `0x18EF12A1` - Nitrous Solenoid State
- `0x18EF12A2` - Transbrake Status

### OBD-II
- `0x7DF` - OBD Request
- `0x7E0-0x7EB` - OBD Responses

## Performance Optimization

### Filtering
Filter only the CAN IDs you need to reduce CPU usage:

```python
# Monitor only specific IDs
filter_ids = {0x180, 0x181, 0x182}
can_interface.set_filter(filter_ids)
```

### Multi-Channel Support
For reTerminal DM with dual CAN:

```python
can_interface = OptimizedCANInterface(
    channel="can0",
    secondary_channel="can1",  # Second CAN bus
    bitrate=500000,
)
```

### Statistics
Monitor bus health:

```python
stats = can_interface.get_statistics()
if stats.messages_per_second > 1000:
    print("High bus load detected")
if stats.error_frames > 0:
    print(f"Error frames: {stats.error_frames}")
```

## Integration with Data Stream Controller

The CAN interface integrates seamlessly with the data stream controller:

```python
from controllers.data_stream_controller import DataStreamController
from interfaces import OptimizedCANInterface

# Create CAN interface
can_interface = OptimizedCANInterface(channel="can0")

# The controller will automatically use CAN if configured
# See config.py for CAN_CHANNEL and CAN_BITRATE settings
```

## Troubleshooting

### No CAN Messages
1. Check CAN interface is up: `ip link show can0`
2. Verify bitrate matches bus: `ip -details link show can0`
3. Check permissions: May need `sudo` or add user to `dialout` group

### High CPU Usage
1. Use message filtering to reduce processing
2. Increase buffer size if needed
3. Check bus load - may be too high

### Detection Issues
1. Increase sample time for vendor detection
2. Verify CAN IDs match expected vendor
3. Check DBC file exists for vendor

## Advanced Features

### Custom DBC Files
Place vendor-specific DBC files in `dbc/` directory:
- `dbc/holley.dbc`
- `dbc/haltech.dbc`
- `dbc/aem.dbc`
- etc.

### Message Decoding
With DBC loaded, messages are automatically decoded:

```python
can_msg = can_interface.read_message()
decoded = can_interface.decode_message(can_msg)
if decoded:
    print(f"Signals: {decoded['signals']}")
```

### Timing Analysis
Analyze message timing patterns:

```python
stats = analyzer.get_id_statistics(0x180)
if stats:
    print(f"Average interval: {stats['avg_interval']:.3f}s")
    print(f"Message rate: {stats['message_rate']:.1f} msg/s")
```

