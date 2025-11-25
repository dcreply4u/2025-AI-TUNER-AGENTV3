# Raspberry Pi 5 HAT Research & Modular Hardware Strategy

## Executive Summary

After researching available Raspberry Pi 5 HATs, a **modular, stackable HAT approach** is highly recommended. This allows offering different product tiers (Base, Pro, Ultimate) by stacking compatible HATs, providing flexibility and cost-effectiveness.

## Key Finding: reTerminal DM CAN Bus

**Note**: Our documentation indicates reTerminal DM has **dual CAN FD built-in**, but user reports suggest otherwise. **Verification needed** - may depend on:
- CM4 module variant
- Carrier board revision
- Device tree configuration

**Recommendation**: Verify actual reTerminal DM CAN capabilities before finalizing hardware strategy.

## Available Raspberry Pi 5 HATs

### 1. CAN Bus HATs

#### Single CAN HATs

**PiCAN3 CAN Bus HAT** (Copperhill Technologies)
- **CAN Controller**: MCP2515 (CAN 2.0B, 1 Mbps)
- **Features**: 3A SMPS, RTC with battery backup
- **Price**: ~$50-60
- **Pros**: Power supply built-in, RTC for logging
- **Cons**: Single CAN only, CAN 2.0B (not CAN FD)
- **GPIO Usage**: SPI bus (SPI0)

**RS485 + CAN-BUS HAT** (PMD Way)
- **CAN Controller**: MCP2515
- **Features**: Dual RS485 + CAN, ESD protection, isolation
- **Price**: ~$40-50
- **Pros**: Multiple interfaces, protected
- **Cons**: Single CAN only
- **GPIO Usage**: SPI bus

**PiCAN with GPS, Gyro, Accelerometer** (Copperhill Technologies) ⭐ **BEST FOR BASE MODEL**
- **CAN Controller**: MCP2515 (1 Mbps)
- **GPS**: MTK3339 (-165 dBm, 10 Hz, 66 channels)
- **IMU**: Gyroscope + Accelerometer
- **Features**: RTC, patch antenna, uFL connector
- **Price**: ~$80-100
- **Pros**: **All-in-one solution** - CAN + GPS + IMU in single HAT
- **Cons**: Single CAN, CAN 2.0B only
- **GPIO Usage**: SPI + UART (GPS)

#### Dual CAN HATs

**⚠️ Limited Options Found**
- Most HATs provide single CAN only
- **Solution**: Stack two single CAN HATs (if using different SPI buses)
- **Alternative**: Custom dual CAN HAT using MCP2518FD (CAN FD capable)

**Potential Custom Solution**:
- **MCP2518FD-based HAT**: Dual CAN FD (up to 5 Mbps)
- Would require custom design or finding existing dual CAN FD HAT
- **Estimated Cost**: $80-120 if custom

### 2. GPS HATs

**L76K GPS HAT** (Waveshare)
- **GNSS**: GPS, BeiDou, GLONASS, QZSS
- **Update Rate**: Up to 5 Hz
- **Features**: LNA, SAW filter, battery holder
- **Price**: ~$25-35
- **GPIO Usage**: UART
- **Pros**: Multi-GNSS, good sensitivity
- **Cons**: Lower update rate than MTK3339

**MAX-7Q GNSS HAT** (Waveshare)
- **GNSS**: GPS, GLONASS, QZSS, SBAS
- **Features**: Anti-spoofing, anti-jamming, A-GNSS
- **Price**: ~$30-40
- **GPIO Usage**: UART
- **Pros**: Professional features
- **Cons**: More expensive

### 3. IMU (Motion/Acceleration) HATs

**⚠️ Standalone IMU HATs are rare** - usually combined with other features

**Options**:
1. **PiCAN with GPS, Gyro, Accelerometer** (includes IMU)
2. **Separate I2C IMU modules**: BNO085, MPU6050, MPU9250
   - Can be added as separate I2C board (not HAT)
   - **Price**: $10-20
   - **GPIO Usage**: I2C bus

### 4. GPIO Expansion HATs

**Most GPIO HATs are for older Pi models** - Pi 5 has 40 GPIO pins (usually sufficient)

**Options**:
- **MCP23017-based I2C GPIO expander**: Adds 16 GPIO via I2C
- **Price**: $10-15
- **GPIO Usage**: I2C bus

## HAT Stacking Considerations

### Critical Factors

1. **GPIO Pin Conflicts**
   - SPI buses: Pi 5 has SPI0, SPI1, SPI2, SPI3, SPI4, SPI5
   - I2C buses: Multiple I2C buses available
   - UART: Multiple UARTs available
   - **Solution**: Use different buses for each HAT

2. **Power Requirements**
   - Pi 5 needs 5V 5A (27W) minimum
   - HATs may need additional power
   - **Solution**: Use HATs with built-in SMPS (like PiCAN3)

3. **Physical Clearance**
   - HATs must have GPIO passthrough headers
   - Stacking height limitations
   - **Solution**: Use stackable headers or HATs with passthrough

4. **Heat Management**
   - Stacked HATs can trap heat
   - **Solution**: Adequate spacing, cooling

## Recommended Modular Product Tiers

### Tier 1: Base Model (~$150-200)
**Target**: Entry-level users, basic telemetry

**Hardware**:
- Raspberry Pi 5 (4GB) - $75
- **PiCAN with GPS, Gyro, Accelerometer HAT** - $90
  - ✅ Single CAN bus
  - ✅ GPS (MTK3339)
  - ✅ IMU (Gyro + Accel)
  - ✅ RTC
- MicroSD card (64GB) - $15
- Case + Power Supply - $20

**Capabilities**:
- 1x CAN bus (1 Mbps)
- GPS tracking
- Motion/acceleration sensing
- 40 GPIO pins (native)
- RTC for timestamped logging

**Total Cost**: ~$200

---

### Tier 2: Pro Model (~$250-300)
**Target**: Intermediate users, dual ECU setups

**Hardware**:
- Raspberry Pi 5 (8GB) - $100
- **PiCAN3 CAN Bus HAT** (Bottom) - $60
  - ✅ Single CAN bus
  - ✅ 3A SMPS (powers Pi)
  - ✅ RTC
- **PiCAN with GPS, Gyro, Accelerometer HAT** (Top) - $90
  - ✅ Single CAN bus (second CAN)
  - ✅ GPS + IMU
- **L76K GPS HAT** (Optional, if needed) - $30
- MicroSD card (128GB) - $25
- Case + Cooling - $30

**Capabilities**:
- 2x CAN buses (1 Mbps each)
- GPS tracking (dual GPS if using L76K)
- Motion/acceleration sensing
- 40 GPIO pins (native)
- RTC for timestamped logging
- Built-in power supply

**Total Cost**: ~$335

**Note**: Stacking two CAN HATs requires:
- Different SPI buses (SPI0 vs SPI1)
- GPIO passthrough headers
- Verification of compatibility

---

### Tier 3: Ultimate Model (~$400-500)
**Target**: Professional users, maximum capabilities

**Hardware**:
- Raspberry Pi 5 (8GB) - $100
- **Custom Dual CAN FD HAT** (MCP2518FD) - $120
  - ✅ Dual CAN FD (up to 5 Mbps)
  - ✅ CAN FD support
  - ✅ 3A SMPS
  - ✅ RTC
- **PiCAN with GPS, Gyro, Accelerometer HAT** - $90
  - ✅ GPS + IMU
- **I2C GPIO Expander** (MCP23017) - $15
  - ✅ +16 GPIO pins
- **High-end GPS HAT** (MAX-7Q) - $40
  - ✅ Professional GPS features
- MicroSD card (256GB) - $40
- Premium case + cooling - $50

**Capabilities**:
- 2x CAN FD buses (5 Mbps)
- Dual GPS (redundancy/accuracy)
- Motion/acceleration sensing
- 56 GPIO pins (40 native + 16 expander)
- RTC for timestamped logging
- Professional-grade GPS

**Total Cost**: ~$455

---

## Alternative: Custom HAT Design

### Recommended Custom HAT Features

**"TelemetryIQ Pro HAT"** - Single custom HAT solution

**Specifications**:
- **Dual CAN FD**: MCP2518FD (2x CAN FD, 5 Mbps)
- **GPS**: MTK3339 or MAX-7Q
- **IMU**: BNO085 (9-axis: accel, gyro, mag)
- **GPIO Expansion**: MCP23017 (+16 GPIO)
- **Power**: 3A SMPS (12V input)
- **RTC**: DS3231 with battery
- **ADC**: ADS1115 (4-channel, 16-bit)
- **Isolation**: CAN bus isolation, ESD protection

**Estimated Cost**: $150-200 (if custom manufactured)
**Advantages**:
- Single HAT (no stacking issues)
- Optimized pin usage
- Professional appearance
- Better integration

**Disadvantages**:
- Higher upfront cost (tooling, MOQ)
- Longer development time
- Less flexibility

## Comparison: reTerminal DM vs Pi 5 + HATs

| Feature | reTerminal DM | Pi 5 + HATs |
|---------|---------------|-------------|
| **Display** | ✅ 10.1" built-in | ❌ External needed |
| **CAN Bus** | ⚠️ Verify (docs say dual CAN FD) | ✅ Via HATs |
| **GPS** | ❌ Not included | ✅ Via HAT |
| **IMU** | ❌ Not included | ✅ Via HAT |
| **Modularity** | ❌ Fixed hardware | ✅ Stackable HATs |
| **Cost** | ~$300-400 | ~$200-500 (tiered) |
| **Upgrade Path** | ❌ Limited | ✅ Add HATs |
| **Touchscreen** | ✅ Built-in | ❌ External needed |

## Recommendations

### ✅ **RECOMMENDED APPROACH: Modular Pi 5 + HATs**

**Why**:
1. **Flexibility**: Users can choose tier that fits needs
2. **Upgrade Path**: Start with Base, upgrade to Pro/Ultimate
3. **Cost-Effective**: Lower entry point ($200 vs $400)
4. **Market Segmentation**: Different price points for different users
5. **Future-Proof**: New HATs can be added as technology evolves

### Product Line Strategy

**Base Model** ($199):
- Pi 5 (4GB) + PiCAN GPS/IMU HAT
- Perfect for: Entry-level, single ECU, basic telemetry

**Pro Model** ($349):
- Pi 5 (8GB) + Dual CAN HATs + GPS/IMU
- Perfect for: Dual ECU, advanced telemetry, racing teams

**Ultimate Model** ($499):
- Pi 5 (8GB) + Custom Dual CAN FD HAT + Premium GPS + Full sensor suite
- Perfect for: Professional tuners, race teams, maximum capabilities

### Implementation Steps

1. **Verify reTerminal DM CAN capabilities** (may still be viable for all-in-one solution)
2. **Test HAT stacking compatibility** (SPI bus conflicts, power, heat)
3. **Develop custom dual CAN FD HAT** (for Ultimate model)
4. **Create hardware detection** for different HAT configurations
5. **Document HAT installation** and configuration
6. **Offer upgrade kits** (Base → Pro → Ultimate)

## Technical Considerations

### GPIO Pin Mapping Strategy

**Pi 5 GPIO Allocation**:
- **SPI0**: Primary CAN HAT
- **SPI1**: Secondary CAN HAT (if dual)
- **I2C0**: GPS HAT (if I2C-based)
- **UART0**: GPS HAT (if UART-based)
- **I2C1**: GPIO Expander, IMU, ADC
- **GPIO**: Direct sensor connections

### Software Detection

Need to detect:
- Which HATs are installed
- CAN bus count and types
- GPS availability
- IMU availability
- GPIO expansion

**Implementation**: Use device tree overlays and hardware detection in `hardware_platform.py`

## Implementation Status

1. ✅ Research complete
2. ✅ HAT detection module created (`core/hat_detector.py`)
3. ✅ Hardware platform updated to use HAT detection
4. ⏳ Verify reTerminal DM CAN capabilities
5. ⏳ Test HAT stacking (order HATs for testing)
6. ⏳ Design custom dual CAN FD HAT (if proceeding)
7. ⏳ Create installation guides
8. ⏳ Develop upgrade path documentation

## HAT Detection

The system now automatically detects installed HATs:

- **CAN HATs**: Detected via device tree, SPI devices, and CAN interfaces
- **GPS HATs**: Detected via UART devices and I2C scanning
- **IMU Sensors**: Detected via I2C addresses (MPU6050, BNO085, etc.)
- **GPIO Expanders**: Detected via I2C (MCP23017)
- **ADC Boards**: Detected via I2C (ADS1115)

The hardware platform automatically configures based on detected HATs.

## References

- [PiCAN with GPS, Gyro, Accelerometer](https://copperhilltech.com/pican-with-gps-gyro-accelerometer-can-bus-board-for-raspberry-pi/)
- [PiCAN3 CAN Bus HAT](https://copperhilltech.com/pican3-can-bus-board-for-raspberry-pi-4-with-3a-smps-and-rtc/)
- [L76K GPS HAT](https://www.waveshare.com/product/raspberry-pi/hats/l76k-gps-hat.htm)
- [Raspberry Pi 5 GPIO Documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html)

