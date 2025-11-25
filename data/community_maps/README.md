# Community Tuning Maps

This directory contains community-contributed tuning maps for both cars and motorcycles.

## Directory Structure

```
community_maps/
├── cars/              # Car tuning maps
│   ├── base/         # Base maps (safe starting points)
│   ├── stage1/       # Stage 1 performance maps
│   └── stage2/       # Stage 2+ performance maps
├── motorcycles/      # Motorcycle tuning maps
│   ├── base/         # Base maps
│   ├── performance/  # Performance maps
│   └── race/        # Race maps
└── README.md        # This file
```

## Map Categories

### Base Maps
- Safe starting points for stock vehicles
- Conservative parameters
- Good for initial startup and leak checks
- **Use these first!**

### Stage 1 Maps
- Conservative performance improvements
- Usually require minimal modifications
- Good for daily driving
- **Requires professional review**

### Stage 2+ Maps
- More aggressive tuning
- Usually require significant modifications
- Track/race use recommended
- **Professional tuning required**

## File Naming Convention

Format: `{make}_{model}_{year}_{tune_type}_{version}.json`

Examples:
- `honda_civic_2020_base_v1.json`
- `yamaha_r1_2021_stage1_v2.json`
- `subaru_wrx_2019_stage2_v1.json`

## Safety

⚠️ **IMPORTANT:** All maps in this directory are provided "as-is" without warranty.

- Always verify map compatibility with your vehicle
- Have a professional tuner review maps before use
- Start with base maps and work up
- Use at your own risk

## Contributing Maps

To contribute a map:

1. Validate the map: `python scripts/validate_tuning_map.py your_map.json`
2. Ensure proper disclaimers are included
3. Follow naming convention
4. Include complete metadata
5. Submit for review

## Legal

- Maps must be legally shareable
- Include proper attribution
- Respect original creator's license
- No proprietary maps (Holley, MoTeC, etc.) without permission



