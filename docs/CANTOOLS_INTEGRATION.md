# CANtools Integration Guide

## Overview

The AI Tuner Agent now includes comprehensive CAN message decoding using the [cantools](https://cantools.readthedocs.io/) library. This allows you to:

- Load DBC (Database Container) files for CAN message definitions
- Decode CAN messages in real-time with signal extraction
- View decoded signals with proper scaling and units
- Browse DBC database contents
- Encode CAN messages for transmission

## Installation

### Local Installation (Windows/Linux)

```bash
pip install cantools
```

### Raspberry Pi Installation

```bash
pip3 install cantools
```

The `cantools` package is already included in `requirements.txt`, so it will be installed automatically when setting up the project.

## Features

### 1. DBC File Loading

- **Location**: CAN Bus Interface Tab → "Load DBC File" button
- **Supported Formats**: 
  - DBC (Database Container) - Most common
  - KCD (Kvaser CAN Database)
  - SYM (Sym file format)
  - ARXML (AUTOSAR XML)
  - CDD (CANdela Diagnostic)

### 2. Real-Time Message Decoding

When a DBC file is loaded, incoming CAN messages are automatically decoded:
- Messages matching DBC definitions are decoded
- Signals are extracted with proper scaling
- Units and value ranges are displayed
- Choice strings (enumerated values) are shown when available

### 3. Decoded Messages View

- **Tab**: "Decoded Messages" in CAN Interface Tab
- Shows decoded messages in a tree view
- Expandable signal details
- Real-time updates as messages arrive

### 4. DBC Browser

- **Tab**: "DBC Browser" in CAN Interface Tab
- Browse all messages in loaded DBC files
- View signal definitions
- See message details (CAN ID, length, signal count)

## Usage

### Loading a DBC File

1. Open the **CAN Bus Interface** tab
2. Click **"Load DBC File"** button
3. Select your DBC file (`.dbc` extension)
4. The file will be loaded and available for decoding

### Viewing Decoded Messages

1. Ensure a DBC file is loaded
2. Switch to the **"Decoded Messages"** tab
3. Monitor incoming CAN traffic
4. Messages matching DBC definitions will appear decoded

### Browsing DBC Contents

1. Load a DBC file
2. Switch to the **"DBC Browser"** tab
3. Expand messages to see signal definitions
4. Double-click a message to see detailed information

### Multiple DBC Files

You can load multiple DBC files:
- Each file gets a unique name (based on filename)
- Select active database from the dropdown
- Switch between databases as needed

## Integration with Existing CAN Interface

The decoder integrates seamlessly with the existing `OptimizedCANInterface`:

```python
from interfaces.can_interface import OptimizedCANInterface
from services.can_decoder import CANDecoder

# Create CAN interface
can_interface = OptimizedCANInterface(channel="can0", bitrate=500000)

# Create decoder
decoder = CANDecoder()
decoder.load_dbc("vehicle.dbc")

# Connect and monitor
can_interface.connect()
can_interface.start_monitoring()

# Decode messages
def on_message(can_msg):
    decoded = decoder.decode_message(can_msg)
    if decoded:
        print(f"Message: {decoded.message_name}")
        for signal in decoded.signals:
            print(f"  {signal.name}: {signal.value} {signal.unit}")

can_interface.message_callback = on_message
```

## API Reference

### CANDecoder Class

#### Methods

- `load_dbc(dbc_path: str, name: Optional[str] = None) -> bool`
  - Load a DBC file
  - Returns True on success

- `decode_message(can_msg: CANMessage) -> Optional[DecodedMessage]`
  - Decode a CAN message
  - Returns DecodedMessage or None

- `encode_message(message_name: str, signals: Dict[str, float]) -> Optional[bytes]`
  - Encode a message from signal values
  - Returns data bytes or None

- `get_message_info(can_id: int) -> Optional[Dict]`
  - Get information about a CAN message
  - Returns message info dictionary

- `list_messages(database_name: Optional[str] = None) -> List[Dict]`
  - List all messages in a database
  - Returns list of message info dictionaries

- `list_databases() -> List[str]`
  - List all loaded database names

- `set_active_database(name: str) -> bool`
  - Set the active database for decoding

### DecodedMessage Class

#### Properties

- `message_name: str` - Name of the message
- `can_id: int` - CAN ID
- `signals: List[DecodedSignal]` - List of decoded signals
- `timestamp: float` - Message timestamp
- `channel: str` - CAN channel name
- `is_extended: bool` - Extended frame flag

### DecodedSignal Class

#### Properties

- `name: str` - Signal name
- `value: float` - Scaled/physical value
- `raw_value: int` - Raw integer value
- `unit: str` - Unit string
- `min_value: Optional[float]` - Minimum value
- `max_value: Optional[float]` - Maximum value
- `choices: Dict[int, str]` - Choice mappings
- `choice_string: Optional[str]` - Current choice string

## Example DBC Files

Common sources for DBC files:
- Vehicle manufacturers (OEM)
- ECU vendors (Holley, Haltech, MoTeC, etc.)
- OpenDBC project: https://github.com/commaai/opendbc
- Custom DBC files created with tools like CANdb++

## Troubleshooting

### "cantools not available" Warning

**Solution**: Install cantools:
```bash
pip install cantools
```

### DBC File Won't Load

**Possible Causes**:
- Invalid DBC file format
- File path incorrect
- File permissions issue

**Solution**: 
- Verify DBC file is valid using cantools command line:
  ```bash
  python -m cantools dump your_file.dbc
  ```

### Messages Not Decoding

**Possible Causes**:
- CAN ID not in DBC file
- Wrong DBC file loaded
- Message format mismatch

**Solution**:
- Verify CAN ID exists in DBC browser
- Check that correct DBC file is active
- Ensure message length matches DBC definition

## References

- [cantools Documentation](https://cantools.readthedocs.io/)
- [cantools GitHub](https://github.com/cantools/cantools)
- [DBC File Format](https://en.wikipedia.org/wiki/CAN_bus#DBC_file_format)

