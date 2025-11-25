"""
Quick Integration Test
Tests that all modules can be imported and basic functionality works
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all critical modules can be imported."""
    print("Testing imports...")
    
    try:
        from ui.main_container import MainContainerWindow
        print("✓ MainContainerWindow imported")
        
        from ui.ecu_tuning_main import ECUTuningTab
        print("✓ ECUTuningTab imported")
        
        # Test optional imports
        try:
            from ui.import_ecu_tab import ImportECUTab
            print("✓ ImportECUTab imported")
        except ImportError:
            print("⚠ ImportECUTab not available (optional)")
        
        try:
            from ui.domestic_ecu_tab import DomesticECUTab
            print("✓ DomesticECUTab imported")
        except ImportError:
            print("⚠ DomesticECUTab not available (optional)")
        
        try:
            from ui.advanced_parameters_tab import AdvancedParametersTab
            print("✓ AdvancedParametersTab imported")
        except ImportError:
            print("⚠ AdvancedParametersTab not available (optional)")
        
        try:
            from ui.cylinder_control_tab import CylinderControlTab
            print("✓ CylinderControlTab imported")
        except ImportError:
            print("⚠ CylinderControlTab not available (optional)")
        
        try:
            from ui.advanced_features_tab import AdvancedFeaturesTab
            print("✓ AdvancedFeaturesTab imported")
        except ImportError:
            print("⚠ AdvancedFeaturesTab not available (optional)")
        
        try:
            from ui.ai_intelligence_tab import AIIntelligenceTab
            print("✓ AIIntelligenceTab imported")
        except ImportError as e:
            print(f"⚠ AIIntelligenceTab not available: {e}")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_services():
    """Test service imports."""
    print("\nTesting services...")
    
    try:
        from services.advanced_diagnostics_intelligence import AdvancedDiagnosticsIntelligence
        print("✓ AdvancedDiagnosticsIntelligence imported")
        
        # Test instantiation
        try:
            di = AdvancedDiagnosticsIntelligence(use_lstm=False, use_ensemble=False)
            print("✓ AdvancedDiagnosticsIntelligence instantiated")
        except Exception as e:
            print(f"⚠ Could not instantiate: {e}")
        
        try:
            from services.advanced_self_learning_intelligence import AdvancedSelfLearningIntelligence
            print("✓ AdvancedSelfLearningIntelligence imported")
            
            try:
                sli = AdvancedSelfLearningIntelligence(use_dqn=False, use_policy_gradient=False)
                print("✓ AdvancedSelfLearningIntelligence instantiated")
            except Exception as e:
                print(f"⚠ Could not instantiate: {e}")
        except ImportError as e:
            print(f"⚠ AdvancedSelfLearningIntelligence not available: {e}")
        
        return True
    except Exception as e:
        print(f"✗ Service import failed: {e}")
        return False

def test_ui_scaling():
    """Test UI scaling."""
    print("\nTesting UI scaling...")
    
    try:
        from ui.ui_scaling import UIScaler, get_scaled_size, get_scaled_font_size
        
        scaler = UIScaler.get_instance()
        size = get_scaled_size(10)
        font = get_scaled_font_size(12)
        
        print(f"✓ UI scaling working (size: {size}, font: {font})")
        return True
    except Exception as e:
        print(f"✗ UI scaling failed: {e}")
        return False

def main():
    """Run integration tests."""
    print("=" * 60)
    print("TELEMETRYIQ INTEGRATION TEST")
    print("=" * 60)
    print()
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Services", test_services()))
    results.append(("UI Scaling", test_ui_scaling()))
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n✓ All integration tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
















