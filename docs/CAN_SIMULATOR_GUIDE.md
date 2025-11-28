# CAN Bus Simulator Guide

## Overview

The AI Tuner Agent includes a comprehensive CAN bus simulator that allows you to simulate CAN traffic without physical hardware. This is perfect for:

- Testing and development
- Debugging CAN message decoding
- Validating DBC file definitions
- Training and demonstrations
- Integration testing

## Features

### 1. Virtual CAN Bus
- Uses python-can's `virtual` interface (works on all platforms)
- No physical hardware required
- Supports standard CAN bitrates (125k, 250k, 500k, 1M bps)

### 2. Message Simulation
- **Periodic Messages**: Send messages at regular intervals
- **On-Demand Messages**: Send messages when requested
- **Event-Driven**: Trigger messages based on conditions

### 3. DBC Integration
- Generate messages from DBC file definitions
- Automatic signal encoding
- Support for multiple DBC databases

### 4. Real-Time Control
- Start/stop simulation
- Enable/disable individual messages
- Update signal values dynamically
- Monitor transmission statistics

## Usage

### Basic Usage

```python
from services.can_simulator import CANSimulator

# Create simulator
simulator = CANSimulator(channel="vcan0", bitrate=500000)

# Add a simple message
simulator.add_message(
    message_name="EngineRPM",
    can_id=0x180,
    data=bytes([0x00, 0x64, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]),
    period=0.1,  # Send every 100ms
)

# Start simulator
simulator.start()

# Simulator runs in background thread
# Messages are sent automatically

# Stop when done
simulator.stop()
```

### Using DBC Files

```python
from services.can_decoder import CANDecoder
from services.can_simulator import CANSimulator

# Load DBC file
decoder = CANDecoder()
decoder.load_dbc("vehicle.dbc")

# Create simulator with decoder
simulator = CANSimulator(
    channel="vcan0",
    dbc_decoder=decoder
)

# Add message from DBC
simulator.add_dbc_message(
    message_name="EngineData",
    signal_values={
        "RPM": 3000.0,
        "ThrottlePosition": 45.5,
        "CoolantTemp": 85.0,
    },
    period=0.1,  # 10 Hz
)

# Update signal values dynamically
simulator.update_message_signals(
    "EngineData",
    {"RPM": 3500.0}  # Update RPM
)

simulator.start()
```

### GUI Usage

1. Open the **CAN Bus Interface** tab
2. Navigate to the **"Simulator"** tab
3. Click **"▶ Start Simulator"**
4. Click **"➕ Add Message"** to add messages
5. Messages will be sent automatically on the virtual bus

## API Reference

### CANSimulator Class

#### Constructor

```python
CANSimulator(
    channel: str = "vcan0",
    bitrate: int = 500000,
    dbc_decoder: Optional[CANDecoder] = None
)
```

#### Methods

**`create_virtual_bus() -> bool`**
- Create a virtual CAN bus interface
- Returns True on success

**`add_message(message_name, can_id, data=None, period=0.1, ...) -> bool`**
- Add a message to simulate
- `message_name`: Unique identifier
- `can_id`: CAN ID (0-0x7FF for standard, 0-0x1FFFFFFF for extended)
- `data`: Raw data bytes (8 bytes default)
- `period`: Period in seconds for periodic messages
- Returns True on success

**`add_dbc_message(message_name, signal_values, period=0.1, ...) -> bool`**
- Add a message from DBC file
- `message_name`: Message name from DBC
- `signal_values`: Dictionary of signal names to values
- `period`: Period in seconds
- Returns True on success

**`update_message_signals(message_name, signal_values) -> bool`**
- Update signal values for a DBC-based message
- Automatically re-encodes the message

**`remove_message(message_name) -> bool`**
- Remove a simulated message

**`enable_message(message_name) -> bool`**
- Enable a message (start sending)

**`disable_message(message_name) -> bool`**
- Disable a message (stop sending)

**`send_message(message_name) -> bool`**
- Send a message on demand (for on_demand type)

**`start() -> bool`**
- Start the simulator
- Begins sending periodic messages

**`stop() -> None`**
- Stop the simulator
- Stops all message transmission

**`get_statistics() -> Dict`**
- Get simulator statistics
- Returns: total_sent, runtime, messages_per_second, etc.

**`list_messages() -> List[Dict]`**
- List all configured messages
- Returns list of message information

## Examples

### Simulating Engine Data

```python
simulator = CANSimulator(channel="vcan0")

# Simulate engine RPM (0x180)
simulator.add_message(
    "EngineRPM",
    can_id=0x180,
    data=bytes([0x00, 0x64, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]),
    period=0.1,  # 10 Hz
)

# Simulate throttle position (0x181)
simulator.add_message(
    "ThrottlePosition",
    can_id=0x181,
    data=bytes([0x2D, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]),
    period=0.05,  # 20 Hz
)

simulator.start()
```

### Simulating Multiple ECUs

```python
simulator = CANSimulator(channel="vcan0")

# ECU 1: Engine Control
simulator.add_message("ECU1_Engine", 0x100, period=0.1)
simulator.add_message("ECU1_Fuel", 0x101, period=0.1)

# ECU 2: Transmission Control
simulator.add_message("ECU2_Trans", 0x200, period=0.05)
simulator.add_message("ECU2_Status", 0x201, period=0.2)

# ECU 3: Body Control
simulator.add_message("ECU3_Body", 0x300, period=0.5)

simulator.start()
```

### Dynamic Signal Updates

```python
decoder = CANDecoder()
decoder.load_dbc("vehicle.dbc")

simulator = CANSimulator(dbc_decoder=decoder)
simulator.add_dbc_message("EngineData", {"RPM": 2000.0}, period=0.1)
simulator.start()

# Update RPM over time
import time
for rpm in range(2000, 6000, 100):
    simulator.update_message_signals("EngineData", {"RPM": float(rpm)})
    time.sleep(0.1)
```

## Integration with Monitoring

The simulator works seamlessly with the CAN monitor:

1. Start the simulator on `vcan0`
2. Open CAN Interface tab
3. Monitor will detect `vcan0` channel
4. Messages will appear in the monitor
5. If DBC is loaded, messages will be decoded automatically

## Virtual CAN Interface Setup

### Linux (SocketCAN)

```bash
# Create virtual CAN interface
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0

# For CAN-FD
sudo ip link set vcan0 mtu 72
```

### Windows/Mac

The `virtual` interface in python-can works automatically - no setup required!

## Troubleshooting

### "Failed to create virtual CAN bus"

**Solution**: 
- On Linux, ensure `vcan` module is loaded: `sudo modprobe vcan`
- Try using `virtual` bustype instead of `socketcan`
- Check that python-can is installed: `pip install python-can`

### Messages Not Appearing

**Possible Causes**:
- Simulator not started
- Message not enabled
- Wrong channel name
- Monitor not connected to same channel

**Solution**:
- Verify simulator is running (check status)
- Ensure message is enabled
- Use same channel name in simulator and monitor
- Check that monitor is listening on correct channel

### DBC Messages Not Encoding

**Possible Causes**:
- DBC file not loaded
- Signal names don't match
- Signal values out of range

**Solution**:
- Load DBC file first
- Verify signal names in DBC browser
- Check signal min/max values

## Best Practices

1. **Use DBC Files**: Always use DBC files when available for accurate message encoding
2. **Realistic Periods**: Use realistic message periods (e.g., 10 Hz for engine data, 1 Hz for status)
3. **Start Small**: Begin with a few messages, then add more
4. **Monitor Statistics**: Watch message rates to avoid bus overload
5. **Clean Shutdown**: Always call `stop()` when done

## References

- [python-can Documentation](https://python-can.readthedocs.io/)
- [cantools Documentation](https://cantools.readthedocs.io/)
- [SocketCAN Documentation](https://www.kernel.org/doc/html/latest/networking/can.html)

