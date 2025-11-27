"""
Test script for enhanced Race Setup Recommender
Tests telemetry-aware recommendations with various scenarios.
"""

import sys
from services.race_setup_recommender import RaceSetupRecommender

def test_tire_temp_analysis():
    """Test tire temperature analysis."""
    print("=" * 60)
    print("Test 1: Tire Temperature Analysis")
    print("=" * 60)
    
    recommender = RaceSetupRecommender()
    
    # Test road course scenario with high tire temps
    telemetry = {
        "Tire_Temp_Front_Left": 210,
        "Tire_Temp_Front_Right": 195,
        "Tire_Temp_Rear_Left": 205,
        "Tire_Temp_Rear_Right": 200,
    }
    
    result = recommender.get_recommendation(
        "How do I improve mid corner balance on road course?",
        telemetry
    )
    
    print("\nQuestion: How do I improve mid corner balance on road course?")
    print(f"\nTelemetry: {telemetry}")
    print(f"\nRecommendation:\n{result}\n")
    
    # Test drag scenario with low tire temps
    telemetry2 = {
        "Tire_Temp_Rear_Left": 130,
        "Tire_Temp_Rear_Right": 135,
    }
    
    result2 = recommender.get_recommendation(
        "What's the best launch setup for drag racing?",
        telemetry2
    )
    
    print("\n" + "-" * 60)
    print("Question: What's the best launch setup for drag racing?")
    print(f"\nTelemetry: {telemetry2}")
    print(f"\nRecommendation:\n{result2}\n")


def test_gforce_analysis():
    """Test G-force analysis."""
    print("=" * 60)
    print("Test 2: G-Force Analysis")
    print("=" * 60)
    
    recommender = RaceSetupRecommender()
    
    # High lateral G scenario
    telemetry = {
        "GForce_Lateral": 1.3,
        "GForce_Longitudinal": -0.9,
    }
    
    result = recommender.get_recommendation(
        "How can I optimize my time attack setup?",
        telemetry
    )
    
    print("\nQuestion: How can I optimize my time attack setup?")
    print(f"\nTelemetry: {telemetry}")
    print(f"\nRecommendation:\n{result}\n")


def test_suspension_analysis():
    """Test suspension travel analysis."""
    print("=" * 60)
    print("Test 3: Suspension Travel Analysis")
    print("=" * 60)
    
    recommender = RaceSetupRecommender()
    
    # Suspension imbalance scenario
    telemetry = {
        "Suspension_Travel_FL": 45,
        "Suspension_Travel_FR": 60,
        "Suspension_Travel_RL": 50,
        "Suspension_Travel_RR": 52,
    }
    
    result = recommender.get_recommendation(
        "My car feels unbalanced in corners, what should I adjust?",
        telemetry
    )
    
    print("\nQuestion: My car feels unbalanced in corners, what should I adjust?")
    print(f"\nTelemetry: {telemetry}")
    print(f"\nRecommendation:\n{result}\n")


def test_temperature_analysis():
    """Test engine temperature analysis."""
    print("=" * 60)
    print("Test 4: Engine Temperature Analysis (Endurance)")
    print("=" * 60)
    
    recommender = RaceSetupRecommender()
    
    # High temperature scenario
    telemetry = {
        "CoolantTemp": 225,
        "OilTemp": 260,
        "EGT": 1650,
    }
    
    result = recommender.get_recommendation(
        "How do I manage heat during a long endurance race?",
        telemetry
    )
    
    print("\nQuestion: How do I manage heat during a long endurance race?")
    print(f"\nTelemetry: {telemetry}")
    print(f"\nRecommendation:\n{result}\n")


def test_suspension_scenario():
    """Test new suspension-specific scenario."""
    print("=" * 60)
    print("Test 5: Suspension-Specific Scenario")
    print("=" * 60)
    
    recommender = RaceSetupRecommender()
    
    result = recommender.get_recommendation(
        "How do I tune my suspension damping for better handling?",
        {}
    )
    
    print("\nQuestion: How do I tune my suspension damping for better handling?")
    print(f"\nRecommendation:\n{result}\n")


def test_autocross_scenario():
    """Test autocross scenario."""
    print("=" * 60)
    print("Test 6: Autocross Scenario")
    print("=" * 60)
    
    recommender = RaceSetupRecommender()
    
    result = recommender.get_recommendation(
        "What's the best setup for autocross on a tight technical course?",
        {}
    )
    
    print("\nQuestion: What's the best setup for autocross on a tight technical course?")
    print(f"\nRecommendation:\n{result}\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Race Setup Recommender - Enhanced Telemetry Tests")
    print("=" * 60 + "\n")
    
    try:
        test_tire_temp_analysis()
        test_gforce_analysis()
        test_suspension_analysis()
        test_temperature_analysis()
        test_suspension_scenario()
        test_autocross_scenario()
        
        print("=" * 60)
        print("All tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

