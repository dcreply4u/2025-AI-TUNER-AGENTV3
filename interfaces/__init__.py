"""\
============================================================
Interfaces Facade – where silicon meets Python imports
============================================================
This namespace collects every hardware/transport abstraction so downstream code can do
clean imports like `from interfaces import OBDInterface`.  Treat it as the sliding door
between silicon and software.
"""

from .gps_interface import GPSInterface, GPSFix, GPSOptimization, DGPSMode, SolutionType
try:
    from .dual_antenna_gps import DualAntennaGPS, DualAntennaFix, DualAntennaStatus
except ImportError:  # pragma: no cover
    DualAntennaGPS = None  # type: ignore
    DualAntennaFix = None  # type: ignore
    DualAntennaStatus = None  # type: ignore

try:
    from .rtk_interface import RTKInterface, NTRIPClient, DGPSMode, SolutionType, RTKStatus
except ImportError:  # pragma: no cover
    RTKInterface = None  # type: ignore
    NTRIPClient = None  # type: ignore
    DGPSMode = None  # type: ignore
    SolutionType = None  # type: ignore
    RTKStatus = None  # type: ignore

try:
    from .imu_interface import IMUInterface, IMUReading, IMUType, IMUStatus
except ImportError:  # pragma: no cover
    IMUInterface = None  # type: ignore
    IMUReading = None  # type: ignore
    IMUType = None  # type: ignore
    IMUStatus = None  # type: ignore
from .obd_interface import OBDInterface
from .racecapture_interface import RaceCaptureInterface
from .sensor_interface import ExternalSensorInterface

try:
    from .voice_interface import VoiceInterface
except ImportError:  # pragma: no cover
    VoiceInterface = None  # type: ignore

try:
    from .voice_output import VoiceOutput
except ImportError:  # pragma: no cover
    VoiceOutput = None  # type: ignore

try:
    from .can_interface import CAN_ID_DATABASE, CANMessage, CANMessageType, CANStatistics, OptimizedCANInterface
except ImportError:  # pragma: no cover
    OptimizedCANInterface = None  # type: ignore
    CANMessage = None  # type: ignore
    CANMessageType = None  # type: ignore
    CANStatistics = None  # type: ignore
    CAN_ID_DATABASE = None  # type: ignore

try:
    from .camera_interface import CameraConfig, CameraInterface, CameraManager, CameraType, Frame
except ImportError:  # pragma: no cover
    CameraConfig = None  # type: ignore
    CameraInterface = None  # type: ignore
    CameraManager = None  # type: ignore
    CameraType = None  # type: ignore
    Frame = None  # type: ignore

try:
    from .ems_interface import EMSDataInterface
except ImportError:  # pragma: no cover
    EMSDataInterface = None  # type: ignore

try:
    from .treehopper_adapter import TreehopperAdapter, get_treehopper_adapter
except ImportError:  # pragma: no cover
    TreehopperAdapter = None  # type: ignore
    get_treehopper_adapter = None  # type: ignore

try:
    from .unified_io_manager import UnifiedIOManager, get_unified_io_manager
except ImportError:  # pragma: no cover
    UnifiedIOManager = None  # type: ignore
    get_unified_io_manager = None  # type: ignore

try:
    from .gpio_adapter_detector import GPIOAdapterDetector
except ImportError:  # pragma: no cover
    GPIOAdapterDetector = None  # type: ignore

try:
    from .obd2_adapter_detector import OBD2AdapterDetector
except ImportError:  # pragma: no cover
    OBD2AdapterDetector = None  # type: ignore

try:
    from .serial_adapter_detector import SerialAdapterDetector
except ImportError:  # pragma: no cover
    SerialAdapterDetector = None  # type: ignore

try:
    from .unified_adapter_manager import (
        UnifiedAdapterManager,
        AdapterHealthMonitor,
        get_unified_adapter_manager,
    )
except ImportError:  # pragma: no cover
    UnifiedAdapterManager = None  # type: ignore
    AdapterHealthMonitor = None  # type: ignore
    get_unified_adapter_manager = None  # type: ignore

try:
    from .cellular_modem_interface import CellularModem, CellularModemDetector
except ImportError:  # pragma: no cover
    CellularModem = None  # type: ignore
    CellularModemDetector = None  # type: ignore

try:
    from .nucleo_interface import (
        NucleoInterface,
        NucleoConnectionType,
        NucleoSensorType,
        NucleoSensorConfig,
        NucleoSensorReading,
        NucleoStatus,
    )
except ImportError:  # pragma: no cover
    NucleoInterface = None  # type: ignore
    NucleoConnectionType = None  # type: ignore
    NucleoSensorType = None  # type: ignore
    NucleoSensorConfig = None  # type: ignore
    NucleoSensorReading = None  # type: ignore
    NucleoStatus = None  # type: ignore

try:
    from .can_hardware_detector import (
        CANHardwareDetector,
        CANHardwareInfo,
        get_can_hardware_detector,
        detect_can_hardware,
        is_waveshare_can,
    )
except ImportError:  # pragma: no cover
    CANHardwareDetector = None  # type: ignore
    CANHardwareInfo = None  # type: ignore
    get_can_hardware_detector = None  # type: ignore
    detect_can_hardware = None  # type: ignore
    is_waveshare_can = None  # type: ignore

try:
    from .waveshare_environmental_hat import (
        WaveshareEnvironmentalHAT,
        EnvironmentalReading,
        get_environmental_hat,
    )
except ImportError:  # pragma: no cover
    WaveshareEnvironmentalHAT = None  # type: ignore
    EnvironmentalReading = None  # type: ignore
    get_environmental_hat = None  # type: ignore

__all__ = [
    "EMSDataInterface",
    "CameraConfig",
    "CameraInterface",
    "CameraManager",
    "CameraType",
    "Frame",
    "CAN_ID_DATABASE",
    "CANMessage",
    "CANMessageType",
    "CANStatistics",
    "OptimizedCANInterface",
    "GPSInterface",
    "GPSFix",
    "GPSOptimization",
    "DGPSMode",
    "SolutionType",
    "OBDInterface",
    "RaceCaptureInterface",
    "ExternalSensorInterface",
]

# Add voice interfaces if available
if VoiceInterface is not None:
    __all__.append("VoiceInterface")
if VoiceOutput is not None:
    __all__.append("VoiceOutput")

# Add Treehopper interfaces if available
if TreehopperAdapter is not None:
    __all__.extend(["TreehopperAdapter", "get_treehopper_adapter"])
if UnifiedIOManager is not None:
    __all__.extend(["UnifiedIOManager", "get_unified_io_manager"])

# Add adapter detection interfaces if available
if GPIOAdapterDetector is not None:
    __all__.append("GPIOAdapterDetector")
if OBD2AdapterDetector is not None:
    __all__.append("OBD2AdapterDetector")
if SerialAdapterDetector is not None:
    __all__.append("SerialAdapterDetector")
if UnifiedAdapterManager is not None:
    __all__.extend(["UnifiedAdapterManager", "AdapterHealthMonitor", "get_unified_adapter_manager"])
if CellularModem is not None:
    __all__.extend(["CellularModem", "CellularModemDetector"])

# Add NUCLEO interface if available
if NucleoInterface is not None:
    __all__.extend([
        "NucleoInterface",
        "NucleoConnectionType",
        "NucleoSensorType",
        "NucleoSensorConfig",
        "NucleoSensorReading",
        "NucleoStatus",
    ])

# Add CAN hardware detector if available
if CANHardwareDetector is not None:
    __all__.extend([
        "CANHardwareDetector",
        "CANHardwareInfo",
        "get_can_hardware_detector",
        "detect_can_hardware",
        "is_waveshare_can",
    ])

# Add dual antenna GPS if available
if DualAntennaGPS is not None:
    __all__.extend(["DualAntennaGPS", "DualAntennaFix", "DualAntennaStatus"])

# Add RTK interface if available
if RTKInterface is not None:
    __all__.extend(["RTKInterface", "NTRIPClient", "DGPSMode", "SolutionType", "RTKStatus"])

# Add IMU interface if available
if IMUInterface is not None:
    __all__.extend(["IMUInterface", "IMUReading", "IMUType", "IMUStatus"])

# Add Waveshare Environmental HAT if available
if WaveshareEnvironmentalHAT is not None:
    __all__.extend(["WaveshareEnvironmentalHAT", "EnvironmentalReading", "get_environmental_hat"])
