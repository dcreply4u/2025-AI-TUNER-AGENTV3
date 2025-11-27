# FFC Cable Orientation Guide for ElectroCookie PCIe NVMe HAT

## Critical: Cable Orientation

The FFC (Flat Flexible Cable) **MUST** be inserted with the correct orientation or it will not work.

### General Rule
**Gold contacts face UP** when inserting into both connectors.

### Step-by-Step Connection

#### 1. Identify the Cable
- Look at the FFC cable - you'll see gold contacts on one side
- The side with gold contacts is the "top"
- The other side (usually white/beige) is the "bottom"

#### 2. Raspberry Pi 5 Connection
- **Location**: PCIe connector on the **bottom** of the Pi 5 board
- **Orientation**: 
  - Hold the Pi 5 with GPIO header at the top
  - The PCIe connector is on the bottom edge
  - Insert the FFC cable with **gold contacts facing UP** (toward the top of the board)
  - Push the cable in until it's fully seated
  - **Lock the connector** - there should be a small lever or clip to secure it

#### 3. HAT Connection
- **Location**: PCIe connector on the ElectroCookie HAT
- **Orientation**:
  - Insert the FFC cable with **gold contacts facing UP** (same orientation as Pi 5)
  - Push the cable in until it's fully seated
  - **Lock the connector** - secure the locking mechanism

### Visual Check
- Both ends should have the **same orientation** (contacts up on both)
- The cable should be straight, not twisted
- Both connectors should be locked/secured

### Common Mistakes
❌ **Wrong**: Contacts facing down
❌ **Wrong**: Cable twisted (one end up, one end down)
❌ **Wrong**: Cable not fully inserted
❌ **Wrong**: Connector not locked

✅ **Correct**: Contacts facing up on both ends, fully inserted, locked

### If Still Not Working
1. Power off completely
2. Remove the cable
3. Flip it over (try contacts down if contacts up didn't work)
4. Re-insert and lock
5. Power on and test

**Note**: Some connectors may be labeled or have indicators. Check the HAT documentation for any specific markings.

