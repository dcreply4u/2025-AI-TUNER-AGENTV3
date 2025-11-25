"""
Integration Review Script
Comprehensive review of all modules, integration, and UI consistency
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_imports():
    """Check all critical imports."""
    print("=" * 60)
    print("CHECKING IMPORTS")
    print("=" * 60)
    
    errors = []
    warnings = []
    
    # Check UI tabs
    ui_tabs = [
        "ui.main_container",
        "ui.ecu_tuning_main",
        "ui.import_ecu_tab",
        "ui.domestic_ecu_tab",
        "ui.advanced_parameters_tab",
        "ui.cylinder_control_tab",
        "ui.advanced_features_tab",
        "ui.ai_intelligence_tab",
        "ui.sensors_tab",
        "ui.dashboard_tab",
        "ui.telemetryiq_tabs",
        "ui.dyno_tab",
        "ui.drag_racing_tab",
        "ui.track_learning_tab",
        "ui.auto_tuning_tab",
        "ui.video_overlay_tab",
    ]
    
    for module_name in ui_tabs:
        try:
            __import__(module_name)
            print(f"✓ {module_name}")
        except ImportError as e:
            errors.append(f"✗ {module_name}: {e}")
            print(f"✗ {module_name}: {e}")
        except Exception as e:
            warnings.append(f"⚠ {module_name}: {e}")
            print(f"⚠ {module_name}: {e}")
    
    # Check services
    services = [
        "services.advanced_diagnostics_intelligence",
        "services.advanced_self_learning_intelligence",
    ]
    
    for module_name in services:
        try:
            __import__(module_name)
            print(f"✓ {module_name}")
        except ImportError as e:
            warnings.append(f"⚠ {module_name}: {e} (optional dependency)")
            print(f"⚠ {module_name}: {e} (optional dependency)")
        except Exception as e:
            warnings.append(f"⚠ {module_name}: {e}")
            print(f"⚠ {module_name}: {e}")
    
    print(f"\nErrors: {len(errors)}, Warnings: {len(warnings)}")
    return errors, warnings

def check_main_container_integration():
    """Check main container integration."""
    print("\n" + "=" * 60)
    print("CHECKING MAIN CONTAINER INTEGRATION")
    print("=" * 60)
    
    try:
        from ui.main_container import MainContainerWindow
        
        # Check if class can be instantiated
        print("✓ MainContainerWindow class found")
        
        # Check for required methods
        required_methods = [
            "setup_ui",
            "update_telemetry",
            "_update_all_tabs",
        ]
        
        for method in required_methods:
            if hasattr(MainContainerWindow, method):
                print(f"✓ Method '{method}' found")
            else:
                print(f"✗ Method '{method}' missing")
        
        return True
    except Exception as e:
        print(f"✗ Error checking main container: {e}")
        return False

def check_ui_consistency():
    """Check UI consistency."""
    print("\n" + "=" * 60)
    print("CHECKING UI CONSISTENCY")
    print("=" * 60)
    
    # Check for consistent styling
    ui_files = list(Path("ui").glob("*_tab.py"))
    
    scaling_usage = 0
    styling_usage = 0
    
    for ui_file in ui_files:
        try:
            content = ui_file.read_text(encoding='utf-8')
            
            if "ui_scaling" in content or "UIScaler" in content:
                scaling_usage += 1
                print(f"✓ {ui_file.name}: Uses UI scaling")
            else:
                print(f"⚠ {ui_file.name}: May not use UI scaling")
            
            if "#1a1a1a" in content or "#2a2a2a" in content:
                styling_usage += 1
                print(f"✓ {ui_file.name}: Uses consistent styling")
            
        except Exception as e:
            print(f"⚠ {ui_file.name}: Could not check ({e})")
    
    print(f"\nScaling usage: {scaling_usage}/{len(ui_files)} files")
    print(f"Styling usage: {styling_usage}/{len(ui_files)} files")
    
    return scaling_usage, styling_usage

def check_update_telemetry_methods():
    """Check all tabs have update_telemetry methods."""
    print("\n" + "=" * 60)
    print("CHECKING UPDATE_TELEMETRY METHODS")
    print("=" * 60)
    
    ui_files = list(Path("ui").glob("*_tab.py"))
    
    has_method = 0
    missing_method = []
    
    for ui_file in ui_files:
        try:
            content = ui_file.read_text(encoding='utf-8')
            
            if "def update_telemetry" in content:
                has_method += 1
                print(f"✓ {ui_file.name}: Has update_telemetry method")
            else:
                missing_method.append(ui_file.name)
                print(f"⚠ {ui_file.name}: Missing update_telemetry method")
        
        except Exception as e:
            print(f"⚠ {ui_file.name}: Could not check ({e})")
    
    print(f"\nTabs with update_telemetry: {has_method}/{len(ui_files)}")
    if missing_method:
        print(f"Missing methods in: {', '.join(missing_method)}")
    
    return has_method, missing_method

def main():
    """Run comprehensive review."""
    print("\n" + "=" * 60)
    print("TELEMETRYIQ INTEGRATION REVIEW")
    print("=" * 60)
    print()
    
    # Change to project root
    import os
    os.chdir(project_root)
    
    # Run checks
    errors, warnings = check_imports()
    main_container_ok = check_main_container_integration()
    scaling_count, styling_count = check_ui_consistency()
    telemetry_count, missing_telemetry = check_update_telemetry_methods()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Import Errors: {len(errors)}")
    print(f"Import Warnings: {len(warnings)}")
    print(f"Main Container: {'✓ OK' if main_container_ok else '✗ FAILED'}")
    print(f"UI Scaling Usage: {scaling_count} files")
    print(f"UI Styling Usage: {styling_count} files")
    print(f"Update Telemetry Methods: {telemetry_count} files")
    
    if errors:
        print("\n✗ CRITICAL ERRORS FOUND:")
        for error in errors:
            print(f"  {error}")
        return 1
    
    if missing_telemetry:
        print("\n⚠ WARNINGS:")
        print(f"  Some tabs missing update_telemetry: {', '.join(missing_telemetry)}")
    
    print("\n✓ Integration review complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
















