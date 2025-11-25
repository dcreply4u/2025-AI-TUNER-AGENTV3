#!/usr/bin/env python3
"""Fix import errors in services/__init__.py"""

import importlib
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Map of expected imports to actual module exports
IMPORT_FIXES = {
    'services.predictive_parts_ordering': {
        'PartPrediction': None,  # Check what actually exists
        'PartStatus': None,
    },
}

def check_module_exports(module_name):
    """Check what a module actually exports."""
    try:
        module = importlib.import_module(module_name)
        exports = []
        for attr in dir(module):
            if not attr.startswith('_'):
                obj = getattr(module, attr)
                if not callable(obj) or isinstance(obj, type):
                    exports.append(attr)
        return exports
    except Exception as e:
        print(f"Error checking {module_name}: {e}")
        return []

# Check predictive_parts_ordering
parts_exports = check_module_exports('services.predictive_parts_ordering')
print(f"predictive_parts_ordering exports: {parts_exports}")







