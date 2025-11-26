# Virtual Dyno Formula Analysis

**Date:** 2025-11-25  
**Analysis:** Comparison of Virtual Dyno formulas with dyno technical knowledge base

---

## Summary

**YES**, your virtual dyno module uses the **primary formula** from the knowledge base we just added:

### ✅ Formula Already in Use

**1. HP = (Torque × RPM) / 5252** ✅ **USED**

**Location:** `services/virtual_dyno.py:441`
```python
def _calculate_hp_from_torque(self, torque_ftlb: float, rpm: float) -> float:
    """
    Calculate horsepower from torque (if torque sensor available).
    
    Formula: HP = (Torque × RPM) / 5252
    """
    hp_crank = (torque_ftlb * rpm) / 5252.0
```

**Also used for reverse calculation:** `services/virtual_dyno.py:349`
```python
# HP = (Torque × RPM) / 5252
# Therefore: Torque = (HP × 5252) / RPM
calculated_torque = (hp_crank * 5252.0) / rpm
```

---

## Formulas NOT Currently Used (But Available in Knowledge Base)

### 1. Inertia Power Formula (375 Constant)

**Formula from Knowledge Base:**
```
InertiaPower = (InertialMass × Acceleration × RollSpeed) / 375
```

**Status:** ❌ **NOT USED** (but could be relevant)

**Why Not Used:**
- Your virtual dyno uses a different approach: `P = F × v` (force × velocity)
- The 375 constant formula is specific to chassis dyno rollers
- Your virtual dyno calculates from vehicle acceleration, not dyno roll acceleration

**Your Current Method:**
```python
# Power at wheels (Watts): P = F × v
P_wheel_watts = F_tractive * speed_mps
hp_wheel = P_wheel_watts * WATTS_TO_HP
```

**Analysis:** Your method is actually **more accurate** for real-world driving because:
- It accounts for aerodynamic drag and rolling resistance
- It uses actual vehicle acceleration, not dyno roll acceleration
- It's designed for road testing, not dyno testing

---

## Related Concepts from Knowledge Base

### 1. Dyno Losses ✅ **ACCOUNTED FOR**

**Knowledge Base:** Dyno losses include frictional losses, windage losses, etc.

**Your Implementation:**
- ✅ Accounts for drivetrain losses (15-20% typical)
- ✅ Accounts for aerodynamic drag
- ✅ Accounts for rolling resistance
- ✅ More comprehensive than typical dyno loss accounting

**Code:**
```python
F_drag = 0.5 * air_density * drag_coefficient * frontal_area * (speed_mps ** 2)
F_roll = rolling_resistance_coef * total_weight_kg * GRAVITY
drivetrain_efficiency = 1.0 - drivetrain_loss
```

---

### 2. Power Equation Components ✅ **USED**

**Knowledge Base:** Power = Force × Distance / Time = Force × Velocity

**Your Implementation:**
```python
# Compute total tractive force at the wheels
F_tractive = total_weight_kg * acceleration_mps2 + F_drag + F_roll

# Power at wheels (Watts): P = F × v
P_wheel_watts = F_tractive * speed_mps
```

**Status:** ✅ **CORRECTLY IMPLEMENTED**

---

### 3. Tire/Wheel Effects ⚠️ **NOT EXPLICITLY ACCOUNTED FOR**

**Knowledge Base:** Tire diameter and wheel weight affect dyno measurements

**Your Implementation:**
- ❌ Does not explicitly account for tire diameter changes
- ❌ Does not account for wheel/tire inertia separately
- ✅ Accounts for total vehicle weight (which includes wheels)

**Recommendation:** Could enhance by:
- Adding tire diameter to vehicle specs
- Accounting for wheel/tire rotational inertia separately
- Adjusting calculations based on effective tire radius

---

## Comparison: Virtual Dyno vs. Chassis Dyno Formulas

| Formula | Chassis Dyno | Virtual Dyno | Status |
|---------|--------------|--------------|--------|
| **HP = (Torque × RPM) / 5252** | ✅ Used | ✅ Used | **MATCH** |
| **InertiaPower = (Mass × Accel × Speed) / 375** | ✅ Used | ❌ Not used | Different approach |
| **P = F × v** | ✅ Used (implicit) | ✅ Used (explicit) | **MATCH** |
| **Dyno Losses** | ✅ Accounted | ✅ Accounted (better) | **ENHANCED** |
| **Tire Effects** | ⚠️ Affects results | ⚠️ Not explicitly modeled | Could improve |

---

## Recommendations

### 1. ✅ Keep Current Implementation
Your virtual dyno uses the correct fundamental formulas and is actually **more sophisticated** than basic chassis dyno calculations because it:
- Accounts for real-world forces (drag, rolling resistance)
- Uses actual vehicle acceleration
- Accounts for environmental conditions (air density, temperature)

### 2. ⚠️ Potential Enhancement: Tire/Wheel Effects
Consider adding explicit tire diameter and wheel inertia calculations:
```python
# Could add to VehicleSpecs:
tire_diameter_m: float  # Tire diameter in meters
wheel_inertia_kg_m2: float  # Rotational inertia of wheels

# Then account for in calculations:
effective_radius = tire_diameter_m / 2
rotational_inertia_effect = wheel_inertia_kg_m2 * angular_acceleration
```

### 3. ✅ Documentation Enhancement
Add comments referencing the knowledge base formulas:
```python
def _calculate_hp_from_torque(self, torque_ftlb: float, rpm: float) -> float:
    """
    Calculate horsepower from torque (if torque sensor available).
    
    Formula: HP = (Torque × RPM) / 5252
    This is the fundamental horsepower equation derived from James Watt's work.
    The constant 5252 comes from: 33,000 / (2 × π) = 5,252
    At 5252 RPM, torque and horsepower are numerically equal.
    
    See: Dyno Testing - Physics knowledge base entry for derivation.
    """
```

---

## Conclusion

**Your virtual dyno module correctly uses the primary formula from the knowledge base:**

✅ **HP = (Torque × RPM) / 5252** - Used correctly

**Additional formulas from the knowledge base:**
- The 375 constant formula is for chassis dyno rollers, not applicable to your road-based virtual dyno
- Your implementation uses the more fundamental `P = F × v` approach, which is correct
- Your loss accounting is actually more comprehensive than typical dyno implementations

**Status:** Your virtual dyno is **correctly implemented** and uses the appropriate formulas for its use case (road-based testing vs. chassis dyno testing).

---

**Source References:**
- Knowledge Base: Dyno Testing - Physics, Formulas, Technical Information
- Virtual Dyno Code: `services/virtual_dyno.py`
- Original Formula Source: James Watt (18th century)


