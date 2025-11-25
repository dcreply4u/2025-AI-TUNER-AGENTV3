# Tune/Map Database Documentation

## Overview

The Tune/Map Database is a comprehensive system for storing, managing, and sharing ECU tuning maps. It provides vehicle-specific categorization, safety validation, and community sharing capabilities.

## Features

### Core Features

1. **Base Maps**: Safe starting point tunes for specific vehicles
2. **Performance Tunes**: Optimized tunes for power gains
3. **Vehicle-Specific Categorization**: Search by make, model, year, engine code
4. **Hardware Requirements**: Lists required/recommended modifications
5. **Performance Gains**: Expected HP/torque improvements
6. **Map Sharing**: Share tunes with community
7. **Safety Validation**: Warnings and validation for dangerous parameters

### Supported Map Types

The database supports all essential tuning map types:

- **IAP/TPS Fuel Maps**: Air/fuel mixture control across engine load and RPM
- **Ignition Timing Maps**: Spark advance optimization
- **RPM Limiters**: Engine rev limit configuration
- **Secondary Throttle Plate (STP) Opening Maps**: STP control for smooth power delivery
- **Fan Temperature Controls**: Cooling fan activation management
- **Throttle Response/Mapping**: Throttle curve modification
- **Boost Control**: Forced induction boost pressure control
- **O2/Lambda Sensor Control**: Wideband sensor configuration
- **Idle Control**: Idle speed and stability
- **Launch Control**: Launch RPM and timing
- **Anti-Lag**: Turbo anti-lag system control
- **Nitrous Control**: Nitrous system integration

## Usage

### Accessing the Database

1. Open the **ECU Tuning** tab
2. Click on the **Tune Database** sub-tab
3. Browse available tunes or search/filter by vehicle

### Searching for Tunes

Use the search and filter options:

- **Search**: Search by tune name, description, or tags
- **Make/Model/Year**: Filter by vehicle
- **ECU Type**: Filter by ECU manufacturer (Holley, Haltech, AEM, etc.)
- **Tune Type**: Filter by tune category (Base Map, Performance, Race, etc.)

### Loading a Tune

1. Select a tune from the table
2. Click **View Details** to see full information
3. Review hardware requirements and safety warnings
4. Click **Load Tune** to apply to your ECU

### Creating a Tune from Current ECU

1. Connect to your ECU
2. Configure your current settings
3. Click **Create Tune from Current ECU**
4. Enter tune name and description
5. The tune will be saved to your database

### Sharing Tunes

1. Select a tune you want to share
2. Click **Share Tune**
3. A unique Share ID will be generated
4. Share the ID with others to download your tune

### Downloading Shared Tunes

1. Get the Share ID from another user
2. Use the API or import function to download
3. The tune will be added to your local database

## Database Structure

### TuneMap Object

Each tune contains:

- **Basic Info**: Name, description, type, version
- **Vehicle Info**: Make, model, year, engine code, fuel type
- **ECU Type**: Compatible ECU manufacturer
- **Maps**: List of tuning maps (fuel, ignition, etc.)
- **Hardware Requirements**: Required/recommended modifications
- **Performance Gains**: Expected HP/torque improvements
- **Safety Warnings**: Important safety information
- **Metadata**: Creation date, author, ratings, download count

### TuningMap Object

Individual maps within a tune:

- **Category**: Type of map (fuel, ignition, etc.)
- **Name**: Map name
- **Description**: What the map controls
- **Data**: Map values (tables, scalars, etc.)
- **Units**: Measurement units
- **Safety Level**: safe, caution, warning, dangerous

## Integration with ECU Control

The database integrates seamlessly with the ECU Control system:

```python
from services.tune_map_database import TuneMapDatabase
from services.ecu_control import ECUControl

# Initialize
tune_db = TuneMapDatabase()
ecu_control = ECUControl()

# Connect to ECU
ecu_control.connect_ecu("Holley", {})

# Load and apply a tune
tune_id = "honda_civic_type_r_base_map_abc123"
success, warnings = tune_db.apply_tune(tune_id, ecu_control)

if success:
    print("Tune applied successfully")
    if warnings:
        print("Warnings:", warnings)
```

## Safety Features

### Validation

- **Parameter Validation**: Checks parameter ranges before applying
- **Safety Warnings**: Alerts for potentially dangerous changes
- **Hardware Checks**: Verifies required modifications are present

### Backup

- **Auto-Backup**: Current ECU settings backed up before applying tune
- **Rollback**: Easy restoration of previous settings
- **Change History**: Track all modifications

## Best Practices

### Using Base Maps

1. **Start with Base Map**: Always load a base map first for your vehicle
2. **Verify Hardware**: Ensure all required modifications are installed
3. **Check for Leaks**: Use base map to verify no leaks or issues
4. **Gradual Tuning**: Make small adjustments from base map

### Creating Custom Tunes

1. **Start from Base**: Begin with a validated base map
2. **Document Changes**: Note all modifications and why
3. **Test Thoroughly**: Validate on dyno or track before sharing
4. **Include Warnings**: Document any safety concerns

### Sharing Tunes

1. **Validate First**: Ensure tune is safe and tested
2. **Document Hardware**: List all required modifications
3. **Include Warnings**: Document any risks or limitations
4. **Provide Support**: Be available for questions

## File Structure

```
data/
└── tune_map_database/
    ├── tunes/          # Local tunes
    │   └── *.json      # Individual tune files
    └── shared/         # Shared tunes
        └── *.json      # Shared tune files
```

## API Reference

### TuneMapDatabase Class

#### Methods

- `add_tune(tune: TuneMap) -> bool`: Add tune to database
- `get_tune(tune_id: str) -> Optional[TuneMap]`: Get tune by ID
- `search_tunes(...) -> List[TuneMap]`: Search tunes by criteria
- `get_base_maps(vehicle, ecu_type) -> List[TuneMap]`: Get base maps
- `apply_tune(tune_id, ecu_control) -> Tuple[bool, List[str]]`: Apply tune
- `share_tune(tune_id) -> Optional[str]`: Share tune
- `download_shared_tune(share_id) -> Optional[TuneMap]`: Download shared tune
- `create_tune_from_current_ecu(...) -> Optional[TuneMap]`: Create from ECU

### TuneMap Class

#### Attributes

- `tune_id`: Unique identifier
- `name`: Tune name
- `description`: Description
- `tune_type`: Type (BASE_MAP, PERFORMANCE, etc.)
- `vehicle`: VehicleIdentifier object
- `ecu_type`: ECU manufacturer
- `maps`: List of TuningMap objects
- `hardware_requirements`: List of required hardware
- `performance_gains`: Expected performance improvements
- `safety_warnings`: Safety warnings
- `shared`: Whether tune is shared
- `share_id`: Unique share identifier

## Examples

### Example: Loading a Base Map

```python
from services.tune_map_database import TuneMapDatabase, VehicleIdentifier
from services.ecu_control import ECUControl

# Initialize
tune_db = TuneMapDatabase()
ecu_control = ECUControl()

# Connect to ECU
ecu_control.connect_ecu("Holley", {})

# Define vehicle
vehicle = VehicleIdentifier(
    make="Honda",
    model="Civic Type R",
    year=2020,
    engine_code="K20C1",
    fuel_type="gasoline",
    forced_induction="turbo",
)

# Get base maps
base_maps = tune_db.get_base_maps(vehicle, "Holley")

if base_maps:
    # Load first base map
    tune = base_maps[0]
    success, warnings = tune_db.apply_tune(tune.tune_id, ecu_control)
    
    if success:
        print(f"Loaded base map: {tune.name}")
        if warnings:
            print("Warnings:", warnings)
```

### Example: Creating a Custom Tune

```python
from services.tune_map_database import (
    TuneMapDatabase,
    TuneMap,
    VehicleIdentifier,
    TuningMap,
    MapCategory,
    TuneType,
    HardwareRequirement,
    PerformanceGains,
)

# Initialize
tune_db = TuneMapDatabase()

# Define vehicle
vehicle = VehicleIdentifier(
    make="Subaru",
    model="WRX",
    year=2021,
    engine_code="FA20",
    fuel_type="gasoline",
    forced_induction="turbo",
)

# Create tune
tune = TuneMap(
    tune_id="",  # Auto-generated
    name="WRX Stage 2 Performance Tune",
    description="Performance tune for WRX with aftermarket exhaust and intake",
    tune_type=TuneType.PERFORMANCE,
    vehicle=vehicle,
    ecu_type="Denso",
    maps=[
        TuningMap(
            category=MapCategory.FUEL_MAP,
            name="Fuel Map",
            description="Optimized fuel map for stage 2 modifications",
            data={"afr_target": 12.5, "load_rpm_table": {}},
            unit="AFR",
            safety_level="warning",
        ),
        TuningMap(
            category=MapCategory.IGNITION_TIMING,
            name="Ignition Timing",
            description="Advanced timing for performance",
            data={"timing_advance": 18.0},
            unit="degrees",
            safety_level="warning",
        ),
    ],
    hardware_requirements=[
        HardwareRequirement(
            component="Aftermarket Exhaust",
            description="Full exhaust system required",
            required=True,
        ),
        HardwareRequirement(
            component="Cold Air Intake",
            description="High-flow intake recommended",
            required=False,
        ),
    ],
    performance_gains=PerformanceGains(
        hp_gain=50,
        torque_gain=60,
        notes="Dyno tested on 91 octane",
    ),
    safety_warnings=[
        "Requires 91+ octane fuel",
        "Monitor AFR closely during initial runs",
    ],
    tags=["subaru", "wrx", "stage2", "performance"],
)

# Add to database
tune_db.add_tune(tune)
print(f"Created tune: {tune.tune_id}")
```

## Troubleshooting

### Tune Not Found

- Verify tune ID is correct
- Check if tune is in local database
- Try refreshing the database

### Tune Won't Apply

- Ensure ECU is connected
- Check ECU type matches tune
- Verify all hardware requirements are met
- Review safety warnings

### Sharing Issues

- Verify tune is saved locally first
- Check file permissions
- Ensure share directory exists

## Future Enhancements

- Cloud sync for tune database
- Community ratings and reviews
- Automatic tune updates
- Tune comparison tools
- Dyno result integration
- AI-powered tune recommendations



