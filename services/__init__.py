"""Service layer exports for the AI Tuner agent."""

from .advanced_analytics import AdvancedAnalytics, LapData, TrendAnalysis
from .drag_racing_analyzer import (
    DRAG_DISTANCES,
    DragCoachingAdvice,
    DragRacingAnalyzer,
    DragRun,
    DragSegment,
)
from .can_analyzer import CANAnalysis, CANAnalyzer
from .can_vendor_detector import CANVendor, CANVendorDetector, VendorSignature

# CAN decoder and simulator (optional)
try:
    from .can_decoder import CANDecoder, DecodedMessage, DecodedSignal
except ImportError:
    CANDecoder = None  # type: ignore
    DecodedMessage = None  # type: ignore
    DecodedSignal = None  # type: ignore

try:
    from .can_simulator import CANSimulator, MessageType, SimulatedMessage
except ImportError:
    CANSimulator = None  # type: ignore
    MessageType = None  # type: ignore
    SimulatedMessage = None  # type: ignore
from .cloud_sync import CloudSync
from .connectivity_manager import ConnectivityManager, ConnectivityStatus
from .database_manager import DatabaseConfig, DatabaseManager, DatabaseType
from .data_logger import DataLogger
from .ecu_auto_setup import ECUAutoSetup, ECUProfile, Manufacturer
from .ecu_control import ECUBackup, ECUChange, ECUControl, ECUOperation, ECUParameter, SafetyLevel
from .ecu_presets import ECUPreset, ECUPresetManager
from .display_manager import DisplayInfo, DisplayManager
from .geo_logger import GeoLogger
from .ai_pit_strategist import AIPitStrategist, PitStrategy, RaceConditions, TireCondition
from .ai_racing_coach import AIRacingCoach, CoachingAdvice, LapAnalysis
from .ar_racing_overlay import AROverlayElement, AROverlayMode, ARRacingOverlay
from .auto_tuning_engine import AutoTuningEngine, TuningAdjustment, TuningParameter
from .biometric_integration import BiometricData, BiometricIntegration, DriverPerformance, DriverState
from .blockchain_verified_records import BlockchainVerifiedRecords, VerifiedRecord
from .crowdsourced_track_database import CommunityTrackData, CrowdsourcedTrackDatabase, TrackSubmission
from .fleet_management import FleetManagement, FleetPerformance, PerformanceComparison, Vehicle
from .predictive_crash_prevention import DangerAlert, DangerLevel, PredictiveCrashPrevention
from .track_learning_ai import TrackLearningAI, TrackPoint, TrackProfile
from .voice_ecu_control import ECUAdjustment, VoiceCommand, VoiceECUControl
from .weather_adaptive_tuning import WeatherAdaptiveTuning, WeatherConditions, WeatherTuningAdjustment
from .live_streamer import LiveStreamer, StreamConfig, StreamingPlatform
from .logging_health_monitor import LoggingHealth, LoggingHealthMonitor, LoggingStatus
from .predictive_parts_ordering import FailurePrediction, Part, PartOrder, PartStatus, PredictivePartsOrdering
from .social_racing_platform import Achievement, AchievementType, Challenge, LeaderboardEntry, SocialRacingPlatform, UserProfile

# Optional imports
try:
    from .disk_cleanup import DiskCleanup
except ImportError:
    DiskCleanup = None  # type: ignore

try:
    from .optimized_streamer import HardwareAccel, OptimizedStreamConfig, OptimizedStreamer
except ImportError:
    HardwareAccel = None  # type: ignore
    OptimizedStreamConfig = None  # type: ignore
    OptimizedStreamer = None  # type: ignore
from .offline_manager import OfflineManager, SyncItem, SyncStatus
from .performance_tracker import PerformanceSnapshot, PerformanceTracker
from .system_diagnostics import ComponentDiagnostic, DiagnosticStatus, SystemDiagnostics
from .startup_diagnostics import DiagnosticResult, StartupDiagnostics
from .usb_manager import USBDevice, USBManager
from .video_logger import VideoLogger
from .voice_feedback import FeedbackEvent, FeedbackPriority, VoiceFeedback
from .virtual_dyno import (
    DynoCurve,
    DynoMethod,
    DynoReading,
    EnvironmentalConditions,
    VehicleSpecs,
    VirtualDyno,
)
from .dyno_analyzer import (
    DynoAnalyzer,
    DynoComparison,
    ModImpact,
    PowerBandAnalysis,
    WeatherStandard,
)
from .dyno_calibration import DynoCalibration

# Optional: Boost/Nitrous and Fuel/Additive management
try:
    from .boost_nitrous_advisor import BoostNitrousAdvisor, BoostNitrousAdvice, BoostNitrousRecommendation
except ImportError:
    BoostNitrousAdvisor = None  # type: ignore
    BoostNitrousAdvice = None  # type: ignore
    BoostNitrousRecommendation = None  # type: ignore

try:
    from .fuel_additive_manager import (
        AdditiveAdvice,
        FuelAdditiveManager,
        FuelAdditiveRecommendation,
        FuelAdditiveStatus,
        FuelAdditiveType,
    )
except ImportError:
    FuelAdditiveManager = None  # type: ignore
    FuelAdditiveType = None  # type: ignore
    AdditiveAdvice = None  # type: ignore
    FuelAdditiveStatus = None  # type: ignore
    FuelAdditiveRecommendation = None  # type: ignore

try:
    from .diesel_tuner import (
        DieselEngineProfile,
        DieselEngineType,
        DieselParameter,
        DieselTuner,
        DieselTuningRecommendation,
    )
except ImportError:
    DieselTuner = None  # type: ignore
    DieselEngineType = None  # type: ignore
    DieselParameter = None  # type: ignore
    DieselTuningRecommendation = None  # type: ignore
    DieselEngineProfile = None  # type: ignore

__all__ = [
    "AdvancedAnalytics",
    "LapData",
    "TrendAnalysis",
    "AIPitStrategist",
    "PitStrategy",
    "RaceConditions",
    "TireCondition",
    "AIRacingCoach",
    "CoachingAdvice",
    "LapAnalysis",
    "AROverlayElement",
    "AROverlayMode",
    "ARRacingOverlay",
    "AutoTuningEngine",
    "TuningAdjustment",
    "TuningParameter",
    "BiometricData",
    "BiometricIntegration",
    "DriverPerformance",
    "DriverState",
    "BlockchainVerifiedRecords",
    "VerifiedRecord",
    "CommunityTrackData",
    "CrowdsourcedTrackDatabase",
    "TrackSubmission",
    "FleetManagement",
    "FleetPerformance",
    "PerformanceComparison",
    "Vehicle",
    "DangerAlert",
    "DangerLevel",
    "PredictiveCrashPrevention",
    "TrackLearningAI",
    "TrackPoint",
    "TrackProfile",
    "ECUAdjustment",
    "VoiceCommand",
    "VoiceECUControl",
    "WeatherAdaptiveTuning",
    "WeatherConditions",
    "WeatherTuningAdjustment",
    "CANAnalysis",
    "CANAnalyzer",
    "CANVendor",
    "CANVendorDetector",
    "VendorSignature",
    "CANDecoder",
    "DecodedMessage",
    "DecodedSignal",
    "CANSimulator",
    "MessageType",
    "SimulatedMessage",
    "CloudSync",
    "ConnectivityManager",
    "ConnectivityStatus",
    "DatabaseConfig",
    "DatabaseManager",
    "DatabaseType",
    "DataLogger",
    "ComponentDiagnostic",
    "DiagnosticResult",
    "DiagnosticStatus",
    "StartupDiagnostics",
    "SystemDiagnostics",
    "ECUAutoSetup",
    "ECUProfile",
    "Manufacturer",
    "ECUBackup",
    "ECUChange",
    "ECUControl",
    "ECUOperation",
    "ECUParameter",
    "SafetyLevel",
    "ECUPreset",
    "ECUPresetManager",
    "DisplayInfo",
    "DisplayManager",
    "GeoLogger",
    "LiveStreamer",
    "LoggingHealth",
    "LoggingHealthMonitor",
    "LoggingStatus",
    "OfflineManager",
    "FailurePrediction",
    "Part",
    "PartOrder",
    "PartStatus",
    "PredictivePartsOrdering",
    "Achievement",
    "AchievementType",
    "Challenge",
    "LeaderboardEntry",
    "SocialRacingPlatform",
    "UserProfile",
    "SyncItem",
    "SyncStatus",
    "PerformanceTracker",
    "PerformanceSnapshot",
    "DragRacingAnalyzer",
    "DragRun",
    "DragCoachingAdvice",
    "DragSegment",
    "DRAG_DISTANCES",
    "StreamConfig",
    "StreamingPlatform",
    "SystemDiagnostics",
    "USBDevice",
    "USBManager",
    "VideoLogger",
    "VoiceFeedback",
    "FeedbackPriority",
    "FeedbackEvent",
    # Virtual Dyno
    "VirtualDyno",
    "DynoCurve",
    "DynoReading",
    "DynoMethod",
    "VehicleSpecs",
    "EnvironmentalConditions",
    "DynoAnalyzer",
    "DynoComparison",
    "ModImpact",
    "PowerBandAnalysis",
    "WeatherStandard",
    "DynoCalibration",
]

# Add optional fuel/additive management if available
if BoostNitrousAdvisor is not None:
    __all__.extend(["BoostNitrousAdvisor", "BoostNitrousAdvice", "BoostNitrousRecommendation"])

if FuelAdditiveManager is not None:
    __all__.extend([
        "FuelAdditiveManager",
        "FuelAdditiveType",
        "AdditiveAdvice",
        "FuelAdditiveStatus",
        "FuelAdditiveRecommendation",
    ])

if DieselTuner is not None:
    __all__.extend([
        "DieselTuner",
        "DieselEngineType",
        "DieselParameter",
        "DieselTuningRecommendation",
        "DieselEngineProfile",
    ])

# Add optional imports if available
if CANVendor is not None:
    __all__.extend(["CANVendor", "CANVendorDetector", "VendorSignature"])

if DiskCleanup is not None:
    __all__.append("DiskCleanup")

if HardwareAccel is not None:
    __all__.extend(["HardwareAccel", "OptimizedStreamConfig", "OptimizedStreamer"])

# Add CAN decoder and simulator if available
if CANDecoder is not None:
    __all__.extend(["CANDecoder", "DecodedMessage", "DecodedSignal"])

if CANSimulator is not None:
    __all__.extend(["CANSimulator", "MessageType", "SimulatedMessage"])

