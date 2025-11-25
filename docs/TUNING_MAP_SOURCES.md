# Tuning Map Sources & Import Guide

Guide to finding and importing tuning maps into the TelemetryIQ database.

## ⚠️ Important Legal & Safety Notice

**Before importing any tuning maps:**

1. **Verify Licensing:** Ensure maps are legally shareable (check licenses, terms of service)
2. **Safety First:** All maps should be validated and marked as "use at your own risk"
3. **Vehicle Compatibility:** Verify maps match your vehicle's exact specifications
4. **Professional Review:** Have a professional tuner review maps before use
5. **Disclaimer Required:** All imported maps must include appropriate disclaimers

---

## 📥 Available Map Sources

### 1. Open Source / Community Maps

#### TuneECU Map Database
- **URL:** [tuneecu.net/Map_Database.html](https://tuneecu.net/Map_Database.html)
- **Format:** Proprietary (may need conversion)
- **License:** Check individual map licenses
- **Vehicles:** Primarily motorcycles
- **Notes:** Maps are compressed, need extraction

#### DIY AutoTune Forums
- **URL:** [msextra.com](https://www.msextra.com) / [msefi.com](https://www.msefi.com)
- **Format:** Various (MSQ, BIN, CSV)
- **License:** Community shared (verify individual licenses)
- **Vehicles:** Wide range (mostly DIY ECU projects)
- **Notes:** User-shared maps, verify compatibility

#### Lambda Tuning Base Maps
- **URL:** [lambdatuning.com/support/downloads](https://lambdatuning.com/support/downloads)
- **Format:** Proprietary
- **License:** Check website terms
- **Vehicles:** Subaru models
- **Notes:** Base maps for stock configurations

### 2. Commercial Map Sources (Require Purchase/License)

#### COBB Tuning
- **URL:** [cobbtuning.com/maps](https://www.cobbtuning.com/maps)
- **Format:** Proprietary (Accessport format)
- **License:** Commercial (requires purchase)
- **Vehicles:** Wide range (Subaru, Ford, BMW, etc.)
- **Notes:** OTS (Off-The-Shelf) maps available

#### JaviTuned
- **URL:** [javi-tuned.com](https://javi-tuned.com)
- **Format:** Proprietary
- **License:** Commercial
- **Vehicles:** Honda/Acura
- **Notes:** Base maps and custom tunes

#### PatTuned
- **URL:** [pattuned.com](https://www.pattuned.com)
- **Format:** JB4 format
- **License:** Commercial
- **Vehicles:** Boosted vehicles (BMW, VW, etc.)
- **Notes:** Custom maps based on setup

### 3. ECU-Specific Sources

#### Holley EFI
- **Format:** HEF files
- **License:** Proprietary
- **Notes:** Holley provides base maps with their software
- **Import:** May require conversion tool

#### MoTeC
- **Format:** M1T files
- **License:** Proprietary
- **Notes:** MoTeC provides base calibrations
- **Import:** May require conversion tool

#### AEM
- **Format:** AEM format
- **License:** Proprietary
- **Notes:** AEM provides base maps
- **Import:** May require conversion tool

---

## 🔧 Importing Maps

### Method 1: Using Import Script

```bash
# Import single JSON file (our native format)
python scripts/import_tuning_maps.py path/to/tune.json

# Import from directory
python scripts/import_tuning_maps.py path/to/tunes/ --format json

# Import CSV with metadata
python scripts/import_tuning_maps.py data.csv --format csv --metadata metadata.json

# Verbose output
python scripts/import_tuning_maps.py tune.json --verbose
```

### Method 2: Programmatic Import

```python
from services.tune_map_database import TuneMapDatabase, TuneMap, TuneType
from services.tune_map_database import VehicleIdentifier, TuningMap, MapCategory

# Initialize database
db = TuneMapDatabase()

# Create tune
tune = TuneMap(
    tune_id=None,  # Will be auto-generated
    name="Honda Civic Si - Stage 1",
    description="Stage 1 tune for stock turbo",
    tune_type=TuneType.PERFORMANCE,
    vehicle=VehicleIdentifier(
        make="Honda",
        model="Civic",
        year=2020,
        engine_code="L15B7",
    ),
    ecu_type="Hondata",
    maps=[
        TuningMap(
            category=MapCategory.FUEL_MAP,
            name="Fuel Map",
            description="Stage 1 fuel adjustments",
            data={
                "rpm_axis": [1000, 2000, 3000, 4000, 5000, 6000, 7000],
                "load_axis": [0, 20, 40, 60, 80, 100],
                "values": [[...], [...], ...]  # 2D array
            }
        )
    ],
    tags=["stage1", "honda", "civic"],
)

# Add to database
db.add_tune(tune)
```

### Method 3: Batch Import from Directory

```python
from pathlib import Path
from scripts.import_tuning_maps import TuningMapImporter

importer = TuningMapImporter()
results = importer.import_from_directory(Path("community_maps/"), "*.json")
print(f"Imported: {results['imported']}, Failed: {results['failed']}")
```

---

## 📋 Map Format Requirements

### JSON Format (Native)

```json
{
  "tune_id": "honda_civic_2020_stage1",
  "name": "Honda Civic 2020 - Stage 1",
  "description": "Stage 1 performance tune",
  "tune_type": "performance",
  "vehicle": {
    "make": "Honda",
    "model": "Civic",
    "year": 2020,
    "engine_code": "L15B7",
    "fuel_type": "gasoline",
    "forced_induction": "turbo"
  },
  "ecu_type": "Hondata",
  "maps": [
    {
      "category": "fuel_map",
      "name": "Fuel Map",
      "description": "Stage 1 fuel adjustments",
      "data": {
        "rpm_axis": [1000, 2000, 3000, 4000, 5000, 6000, 7000],
        "load_axis": [0, 20, 40, 60, 80, 100],
        "values": [
          [14.7, 14.5, 14.2, 13.8, 13.5, 13.0],
          [14.7, 14.4, 14.0, 13.6, 13.2, 12.8],
          // ... more rows
        ]
      }
    }
  ],
  "hardware_requirements": [
    {
      "component": "Aftermarket intake",
      "description": "Cold air intake recommended",
      "required": false
    }
  ],
  "performance_gains": {
    "hp_gain": 25,
    "torque_gain": 30,
    "notes": "Dyno tested on 93 octane"
  },
  "tags": ["stage1", "honda", "civic", "turbo"],
  "safety_warnings": [
    "Requires 93 octane fuel minimum",
    "Not for use with stock intercooler"
  ]
}
```

### CSV Format (with metadata.json)

**metadata.json:**
```json
{
  "name": "Honda Civic 2020 - Stage 1",
  "make": "Honda",
  "model": "Civic",
  "year": 2020,
  "ecu_type": "Hondata",
  "tune_type": "performance",
  "tags": ["stage1", "honda"]
}
```

**data.csv:**
```csv
map_type,rpm,load_0,load_20,load_40,load_60,load_80,load_100
fuel_map,1000,14.7,14.7,14.7,14.7,14.7,14.7
fuel_map,2000,14.7,14.5,14.2,13.8,13.5,13.0
fuel_map,3000,14.7,14.4,14.0,13.6,13.2,12.8
...
```

---

## 🛠️ Creating Your Own Maps

### Template Generator

```python
from services.tune_map_database import (
    TuneMap, TuneType, VehicleIdentifier, TuningMap, MapCategory
)

def create_base_map_template(make: str, model: str, year: int, ecu_type: str):
    """Create a base map template."""
    tune = TuneMap(
        tune_id=None,
        name=f"{make} {model} {year} - Base Map",
        description="Safe base map for stock configuration",
        tune_type=TuneType.BASE_MAP,
        vehicle=VehicleIdentifier(
            make=make,
            model=model,
            year=year,
        ),
        ecu_type=ecu_type,
        maps=[
            # Add your maps here
        ],
        safety_warnings=[
            "This is a base map - verify all parameters before use",
            "Use at your own risk",
        ],
    )
    return tune
```

---

## ✅ Validation Checklist

Before adding maps to the database:

- [ ] **Legal:** Map is legally shareable (check license)
- [ ] **Format:** Map is in correct format or can be converted
- [ ] **Compatibility:** Map matches vehicle specifications
- [ ] **Safety:** Map includes safety warnings
- [ ] **Documentation:** Map has proper description and notes
- [ ] **Testing:** Map has been tested (if available)
- [ ] **Disclaimer:** Appropriate disclaimers are included

---

## 📚 Recommended Community Maps to Add

### Safe Base Maps (Good Starting Points)

1. **Honda Civic Type R (FK8)** - Base map
2. **Subaru WRX (VA)** - Stage 1 base
3. **Ford Focus ST** - Base map
4. **Mazda Miata (ND)** - Base map
5. **Toyota 86/BRZ** - Base map

### Performance Maps (Use with Caution)

1. **Stage 1 Maps** - Conservative performance gains
2. **E85 Maps** - For E85 fuel conversions
3. **Track Maps** - For track use only

---

## 🔒 Legal Considerations

### What You Can Do:
- ✅ Import maps you own or have license to use
- ✅ Import open-source maps with permissive licenses
- ✅ Create your own maps and share them
- ✅ Import community-shared maps (with proper attribution)

### What You Cannot Do:
- ❌ Import copyrighted maps without permission
- ❌ Redistribute proprietary maps (Holley, MoTeC, etc.) without license
- ❌ Remove attribution from community maps
- ❌ Claim ownership of maps you didn't create

### Best Practices:
1. **Always include attribution** for community maps
2. **Include disclaimers** for all maps
3. **Mark maps with source** (where they came from)
4. **Respect licenses** - check before importing
5. **Contact map creators** if unsure about licensing

---

## 🚀 Quick Start: Adding Your First Map

1. **Find a compatible map** (see sources above)
2. **Convert to JSON format** (if needed)
3. **Validate the map** (check vehicle compatibility)
4. **Import using script:**
   ```bash
   python scripts/import_tuning_maps.py your_map.json
   ```
5. **Verify in database:**
   ```python
   from services.tune_map_database import TuneMapDatabase
   db = TuneMapDatabase()
   tunes = db.search_tunes(make="Honda", model="Civic")
   ```

---

## 📞 Support

For questions about:
- **Map compatibility:** Check vehicle specifications
- **Import errors:** Run with `--verbose` flag
- **Format conversion:** See format requirements above
- **Legal questions:** Consult with legal counsel

---

**Last Updated:** December 2024



