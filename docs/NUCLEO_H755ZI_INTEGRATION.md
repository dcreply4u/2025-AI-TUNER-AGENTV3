# NUCLEO-H755ZI-Q Integration Guide

## Overview

The **NUCLEO-H755ZI-Q** development board features the **STM32H755ZI** dual-core MCU (Cortex-M7 + Cortex-M4), making it an excellent companion to the Raspberry Pi 5 for real-time data acquisition, processing, and control in the AI Tuner application.

## Why Integrate NUCLEO-H755ZI-Q?

### Key Advantages:
1. **Real-Time Performance**: Dual-core architecture (M7 @ 480MHz + M4 @ 240MHz) for deterministic real-time operations
2. **Rich I/O**: Multiple UART, SPI, I2C, CAN FD, USB, Ethernet interfaces
3. **Low Latency**: Hardware-level sensor reading and filtering
4. **Offload Processing**: Free up Pi 5 CPU for AI/ML and UI tasks
5. **Industrial Grade**: Robust STM32 platform for automotive/racing applications

### Use Cases:
- **Real-time sensor data acquisition** (temperature, pressure, RPM, etc.)
- **CAN bus gateway/bridge** (multiple CAN channels, filtering, forwarding)
- **High-speed ADC sampling** (analog sensors at high rates)
- **Real-time control loops** (boost control, fuel injection timing)
- **Safety monitoring** (watchdog, limit checking, emergency shutdown)
- **Data logging buffer** (local storage before Pi transmission)

---

## Integration Options

### Option 1: UART/Serial Communication (Recommended for Start)

**Best for**: Simple bidirectional communication, easy setup

**Hardware Connections:**
```
NUCLEO-H755ZI-Q          Raspberry Pi 5
─────────────────        ────────────────
USART3_TX (PD8)   ────>  GPIO 15 (UART0_RX)
USART3_RX (PD9)   <────  GPIO 14 (UART0_TX)
GND               ────>  GND
```

**Advantages:**
- Simple wiring (3 wires)
- Built-in support in application
- Reliable for moderate data rates
- Easy debugging

**Limitations:**
- Lower bandwidth (~115200-921600 baud typical)
- Single channel

**Data Rate**: Up to ~115KB/s at 921600 baud

---

### Option 2: SPI Communication (High Speed)

**Best for**: High-speed data streaming, real-time sensor data

**Hardware Connections:**
```
NUCLEO-H755ZI-Q          Raspberry Pi 5
─────────────────        ────────────────
SPI1_MOSI (PA7)   ────>  GPIO 10 (SPI0_MOSI)
SPI1_MISO (PA6)   <────  GPIO 9  (SPI0_MISO)
SPI1_SCK  (PA5)   ────>  GPIO 11 (SPI0_SCLK)
SPI1_NSS  (PA4)   ────>  GPIO 8  (SPI0_CE0)
GND               ────>  GND
```

**Advantages:**
- Very high speed (up to 50+ MHz)
- Full-duplex communication
- Low latency
- Supports multiple devices (with CS lines)

**Limitations:**
- More complex wiring
- Master/slave relationship (Pi = Master, NUCLEO = Slave)

**Data Rate**: Up to ~6MB/s at 50MHz

---

### Option 3: I2C Communication (Multi-Device)

**Best for**: Multiple sensors, simple wiring, moderate speed

**Hardware Connections:**
```
NUCLEO-H755ZI-Q          Raspberry Pi 5
─────────────────        ────────────────
I2C1_SDA (PB7)    ────>  GPIO 2  (I2C1_SDA)
I2C1_SCL (PB6)    ────>  GPIO 3  (I2C1_SCL)
GND               ────>  GND
```

**Advantages:**
- Simple wiring (2 data lines + power/ground)
- Multi-device support (up to 127 devices)
- Built-in addressing
- Standard protocol

**Limitations:**
- Lower speed than SPI (~400kHz-1MHz typical)
- Shared bus (can bottleneck)

**Data Rate**: Up to ~50KB/s at 400kHz

---

### Option 4: CAN Bus (Automotive Integration)

**Best for**: Direct ECU communication, automotive sensors, racing applications

**Hardware Connections:**
```
NUCLEO-H755ZI-Q          Raspberry Pi 5 / CAN HAT
─────────────────        ────────────────────────
CAN1_TX (PB9)     ────>  CAN_H
CAN1_RX (PB8)     ────>  CAN_L
GND               ────>  GND
```

**Advantages:**
- Native automotive protocol
- Robust error handling
- Multi-node support
- Industry standard

**Limitations:**
- Requires CAN transceiver on Pi side (or CAN HAT)
- More complex setup

**Data Rate**: Up to 1Mbps (CAN FD)

---

### Option 5: USB Communication (Plug & Play)

**Best for**: Easy connection, high bandwidth, power delivery

**Hardware Connections:**
```
NUCLEO-H755ZI-Q          Raspberry Pi 5
─────────────────        ────────────────
USB-C Connector   ────>  USB 3.0 Port
```

**Advantages:**
- No wiring required
- High speed (USB 2.0/3.0)
- Power delivery
- Hot-pluggable

**Limitations:**
- Requires USB device mode on NUCLEO
- May need custom USB descriptor

**Data Rate**: Up to 480Mbps (USB 2.0) or 5Gbps (USB 3.0)

---

### Option 6: Ethernet (Network Integration)

**Best for**: Remote monitoring, network-based architecture, multiple devices

**Hardware Connections:**
```
NUCLEO-H755ZI-Q          Raspberry Pi 5
─────────────────        ────────────────
Ethernet Port     ────>  Network Switch
                    └──>  Pi 5 Ethernet
```

**Advantages:**
- Standard network protocol
- Remote access
- Multiple devices
- High bandwidth

**Limitations:**
- Requires network infrastructure
- Higher latency than direct connections

**Data Rate**: Up to 100Mbps (Ethernet)

---

## Recommended Architecture

### Hybrid Approach (Best Performance)

Use **multiple interfaces** for different purposes:

1. **UART**: Command/control, configuration, status updates
2. **SPI**: High-speed sensor data streaming
3. **CAN**: Direct ECU/automotive device communication
4. **I2C**: Additional sensor expansion

```
┌─────────────────┐
│  Raspberry Pi 5 │
│  (AI/ML/UI)     │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼───┐
│  UART │ │ SPI  │  ← Control & High-Speed Data
└───┬───┘ └──┬───┘
    │        │
┌───▼────────▼───┐
│ NUCLEO-H755ZI-Q │
│  (Real-Time)    │
└───┬─────────────┘
    │
┌───▼───┐ ┌──▼───┐ ┌──▼───┐
│ CAN   │ │ ADC  │ │ I2C  │  ← Sensors & Devices
└───────┘ └──────┘ └──────┘
```

---

## Implementation Plan

### Phase 1: UART Integration (Quick Start)

1. **STM32 Firmware** (NUCLEO side):
   - Configure USART3 for 921600 baud
   - Implement simple command protocol
   - Read sensors and send JSON data

2. **Python Interface** (Pi side):
   - Extend `serial_adapter_detector.py`
   - Create `nucleo_interface.py`
   - Add to `data_stream_controller.py`

### Phase 2: SPI High-Speed Data

1. **STM32 Firmware**:
   - Configure SPI1 as slave
   - Implement DMA for zero-copy transfers
   - Buffer sensor data

2. **Python Interface**:
   - Use `spidev` library
   - Implement streaming protocol
   - Add to telemetry pipeline

### Phase 3: CAN Integration

1. **STM32 Firmware**:
   - Configure CAN1/CAN2
   - Implement CAN FD support
   - Filter and forward messages

2. **Python Interface**:
   - Integrate with existing `can_interface.py`
   - Add NUCLEO as CAN gateway

---

## Communication Protocol Design

### UART Protocol (JSON-based)

**Request Format:**
```json
{
  "cmd": "read_sensors",
  "sensors": ["temp1", "pressure1", "rpm"],
  "rate": 100
}
```

**Response Format:**
```json
{
  "timestamp": 1234567890.123,
  "data": {
    "temp1": 85.5,
    "pressure1": 12.3,
    "rpm": 6500
  },
  "status": "ok"
}
```

### SPI Protocol (Binary)

**Frame Format:**
```
[Header: 4 bytes][Data: N bytes][CRC: 2 bytes]
```

**Header:**
- Byte 0: Message type (0x01 = sensor data, 0x02 = status)
- Byte 1-2: Data length (little-endian)
- Byte 3: Sequence number

---

## STM32 Firmware Requirements

### Required Features:
1. **Sensor Reading**: ADC, I2C sensors, CAN messages
2. **Data Buffering**: Circular buffers for high-rate sampling
3. **Protocol Handler**: UART/SPI/I2C communication
4. **Real-Time Scheduling**: FreeRTOS for deterministic timing
5. **Watchdog**: Safety monitoring

### Recommended STM32CubeMX Configuration:
- **USART3**: 921600 baud, 8N1, DMA enabled
- **SPI1**: Slave mode, 8MHz, DMA enabled
- **I2C1**: 400kHz, standard mode
- **CAN1**: CAN FD, 1Mbps
- **ADC1**: Multi-channel, DMA, 1MHz sampling
- **FreeRTOS**: Task scheduler for real-time operations

---

## Python Integration Code

### New Interface Module

Create `interfaces/nucleo_interface.py`:

```python
"""
NUCLEO-H755ZI-Q Interface
Supports UART, SPI, I2C, and CAN communication
"""

from enum import Enum
from typing import Dict, Optional, List
import logging
import serial
import time

LOGGER = logging.getLogger(__name__)

class NucleoConnectionType(Enum):
    """Connection types for NUCLEO board."""
    UART = "uart"
    SPI = "spi"
    I2C = "i2c"
    CAN = "can"
    USB = "usb"
    ETHERNET = "ethernet"

class NucleoInterface:
    """Interface for NUCLEO-H755ZI-Q development board."""
    
    def __init__(self, connection_type: NucleoConnectionType, **kwargs):
        self.connection_type = connection_type
        self.connected = False
        self._interface = None
        self._config = kwargs
        
    def connect(self) -> bool:
        """Connect to NUCLEO board."""
        try:
            if self.connection_type == NucleoConnectionType.UART:
                self._interface = serial.Serial(
                    port=self._config.get('port', '/dev/ttyUSB0'),
                    baudrate=self._config.get('baudrate', 921600),
                    timeout=self._config.get('timeout', 1.0)
                )
                self.connected = True
                LOGGER.info("NUCLEO connected via UART")
                return True
            # Add other connection types...
        except Exception as e:
            LOGGER.error(f"Failed to connect to NUCLEO: {e}")
            return False
    
    def read_sensors(self, sensor_list: List[str]) -> Dict[str, float]:
        """Read sensor values from NUCLEO."""
        # Implementation...
        pass
    
    def send_command(self, command: Dict) -> bool:
        """Send command to NUCLEO."""
        # Implementation...
        pass
```

---

## Wiring Diagrams

### UART Connection (Simplest)
```
                    ┌─────────────┐
                    │  Pi 5 GPIO  │
                    │             │
                    │ 14 (TX)     │──────┐
                    │ 15 (RX)     │◄─────┤
                    │ GND         │──────┤
                    └─────────────┘      │
                                          │
                    ┌─────────────┐      │
                    │ NUCLEO      │      │
                    │             │      │
                    │ PD9 (RX)    │◄─────┘
                    │ PD8 (TX)    │──────┐
                    │ GND         │──────┘
                    └─────────────┘
```

### SPI Connection (High Speed)
```
                    ┌─────────────┐
                    │  Pi 5 GPIO  │
                    │             │
                    │ 10 (MOSI)   │──────┐
                    │ 9  (MISO)   │◄─────┤
                    │ 11 (SCLK)   │──────┤
                    │ 8  (CE0)    │──────┤
                    │ GND         │──────┤
                    └─────────────┘      │
                                          │
                    ┌─────────────┐      │
                    │ NUCLEO      │      │
                    │             │      │
                    │ PA7 (MOSI)  │◄─────┘
                    │ PA6 (MISO)  │──────┐
                    │ PA5 (SCLK)  │◄─────┤
                    │ PA4 (NSS)   │◄─────┤
                    │ GND         │──────┘
                    └─────────────┘
```

---

## Performance Considerations

### Latency Targets:
- **UART**: < 10ms (at 921600 baud)
- **SPI**: < 1ms (at 8MHz)
- **I2C**: < 5ms (at 400kHz)
- **CAN**: < 2ms (at 1Mbps)

### Data Throughput:
- **UART**: ~115KB/s (921600 baud)
- **SPI**: ~6MB/s (50MHz)
- **I2C**: ~50KB/s (400kHz)
- **CAN**: ~125KB/s (1Mbps)

---

## Next Steps

1. **Choose primary interface** (recommend UART for start)
2. **Develop STM32 firmware** using STM32CubeMX
3. **Implement Python interface** in application
4. **Test with sample sensors**
5. **Add to data stream controller**
6. **Expand to additional interfaces** as needed

---

## Resources

- [NUCLEO-H755ZI-Q User Manual](https://www.st.com/resource/en/user_manual/um3013-stm32-nucleo144-boards-mb1364-stmicroelectronics.pdf)
- [STM32H755ZI Datasheet](https://www.st.com/resource/en/datasheet/stm32h755zi.pdf)
- [STM32CubeMX](https://www.st.com/en/development-tools/stm32cubemx.html)
- [Python Serial Library](https://pyserial.readthedocs.io/)
- [Python SPI Library](https://github.com/doceme/py-spidev)

---

**Status**: Ready for implementation. Start with UART interface for quick integration, then expand to SPI for high-speed data.

