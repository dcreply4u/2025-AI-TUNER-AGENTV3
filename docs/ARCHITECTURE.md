# AI Tuner Agent - System Architecture

## Overview

The AI Tuner Agent is a comprehensive edge computing platform for automotive telemetry, performance tracking, and intelligent tuning assistance. Built with a modular, service-oriented architecture designed for reliability, extensibility, and real-time performance.

## Architecture Principles

1. **Modular Design**: Loosely coupled components with clear interfaces
2. **Hardware Abstraction**: Platform-agnostic with hardware-specific optimizations
3. **Fault Tolerance**: Graceful degradation and automatic recovery
4. **Real-time Performance**: Optimized for low-latency data processing
5. **Extensibility**: Easy to add new data sources, vendors, and features

## System Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│  (UI Components, Dashboards, Visualizations)               │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                    Control Layer                             │
│  (Controllers, Orchestration, State Management)              │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                             │
│  (Business Logic, Data Processing, Analytics)                │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                    Interface Layer                           │
│  (Hardware Interfaces, Protocols, Communication)             │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                    Core Layer                                │
│  (Platform Detection, Error Handling, Configuration)         │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                    Hardware Layer                            │
│  (CAN Bus, OBD-II, GPS, Cameras, USB Storage)                │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Core Layer (`core/`)

**Purpose**: Foundation services and platform abstraction

**Components**:
- `hardware_platform.py`: Hardware detection and configuration
- `error_handler.py`: Centralized error handling and recovery
- `config_manager.py`: Persistent configuration and profiles
- `data_validator.py`: Data quality and validation
- `security_manager.py`: Encryption and credential management
- `performance_manager.py`: Resource monitoring and optimization

**Key Features**:
- Automatic hardware detection (reTerminal DM, Raspberry Pi, Jetson)
- Error recovery strategies
- Configuration persistence
- Data validation and outlier detection

### 2. Interface Layer (`interfaces/`)

**Purpose**: Hardware and protocol abstraction

**Components**:
- `obd_interface.py`: OBD-II protocol support
- `racecapture_interface.py`: RaceCapture Pro integration
- `gps_interface.py`: GPS/NMEA support
- `camera_interface.py`: USB/WiFi camera support
- `voice_interface.py`: Speech recognition
- `voice_output.py`: Text-to-speech
- `simulated_interface.py`: Demo/testing data source

**Key Features**:
- Unified interface for all data sources
- Automatic source detection
- Protocol abstraction
- Simulated mode for testing

### 3. Service Layer (`services/`)

**Purpose**: Business logic and data processing

**Components**:
- `data_logger.py`: CSV logging
- `database_manager.py`: Local SQLite + Cloud PostgreSQL
- `cloud_sync.py`: Cloud synchronization
- `offline_manager.py`: Offline queue and sync
- `performance_tracker.py`: Dragy-style metrics
- `geo_logger.py`: GPS trace logging
- `video_logger.py`: Video recording with overlays
- `live_streamer.py`: YouTube/Twitch streaming
- `voice_feedback.py`: Proactive announcements
- `advanced_analytics.py`: Lap comparison, trends
- `usb_manager.py`: USB storage management
- `logging_health_monitor.py`: Logging status monitoring

**Key Features**:
- Fast local database (SQLite) with cloud fallback
- Automatic USB detection and setup
- Real-time performance tracking
- Video overlay system
- Offline-first architecture

### 4. Control Layer (`controllers/`)

**Purpose**: Orchestration and state management

**Components**:
- `data_stream_controller.py`: Main data flow orchestration
- `camera_manager.py`: Camera and video management
- `voice_controller.py`: Voice command handling
- `dragy_controller.py`: Performance tracking UI

**Key Features**:
- Qt-friendly (thread-safe)
- Automatic reconnection
- State management
- Event-driven architecture

### 5. AI Layer (`ai/`)

**Purpose**: Machine learning and intelligent analysis

**Components**:
- `predictive_fault_detector.py`: Anomaly detection (IsolationForest)
- `tuning_advisor.py`: Rule-based tuning recommendations
- `conversational_agent.py`: Natural language interaction
- `health_scoring_engine.py`: Engine health scoring

**Key Features**:
- Real-time anomaly detection
- Predictive maintenance
- Natural language queries
- Health scoring algorithms

### 6. Presentation Layer (`ui/`)

**Purpose**: User interface and visualization

**Components**:
- `main.py`: Main application window
- `telemetry_panel.py`: Real-time sensor display
- `health_score_widget.py`: Health gauge
- `ai_insight_panel.py`: AI recommendations
- `dragy_view.py`: Performance dashboard
- `fault_panel.py`: DTC display
- `status_bar.py`: System status
- `onboarding_wizard.py`: First-time setup
- `overlay_config_dialog.py`: Video overlay configuration
- `camera_config_dialog.py`: Camera setup
- `usb_setup_dialog.py`: USB configuration

**Key Features**:
- Modern Qt6/PySide6 UI
- Real-time updates
- Dragy-style performance view
- Customizable video overlays

## Data Flow

```
Hardware (CAN/OBD/GPS)
    ↓
Interface Layer (Protocol Abstraction)
    ↓
Data Stream Controller (Orchestration)
    ↓
    ├─→ Data Validator (Quality Check)
    ├─→ Predictive Fault Detector (Anomaly Detection)
    ├─→ Health Scoring Engine (Health Calculation)
    ├─→ Tuning Advisor (Recommendations)
    ├─→ Performance Tracker (Metrics)
    ├─→ Data Logger (CSV)
    ├─→ Database Manager (SQLite/PostgreSQL)
    ├─→ Cloud Sync (Optional)
    └─→ UI Components (Display)
```

## Database Architecture

### Local Database (SQLite)
- **Primary Storage**: Fast, always available
- **Tables**: telemetry, sessions, events, performance_metrics
- **Features**: WAL mode, indexed queries, transaction support

### Cloud Database (PostgreSQL)
- **Fallback/Sync**: When connectivity available
- **Automatic Sync**: Background thread syncs local → cloud
- **Features**: Connection pooling, SSL, conflict resolution

### Sync Strategy
1. Write to local first (fast, always available)
2. Queue for cloud sync
3. Background worker syncs when online
4. Automatic retry with backoff

## Communication Protocols

### Supported Protocols
- **CAN Bus**: ISO 15765, J1939, custom protocols
- **OBD-II**: ELM327, ISO 9141, ISO 14230, ISO 15765
- **RaceCapture**: Serial protocol
- **GPS**: NMEA 0183
- **Video**: USB UVC, RTSP, HTTP streams
- **Cloud**: MQTT, HTTPS REST

## Security Architecture

### Credential Management
- Encrypted storage (Fernet/AES)
- Secure key management
- Password hashing (PBKDF2)
- File permission protection

### Data Protection
- Optional encryption for sensitive logs
- Secure cloud connections (SSL/TLS)
- Access control for operations

## Performance Optimizations

### Resource Management
- Thread pool for concurrent operations
- Memory optimization (garbage collection)
- CPU/memory monitoring
- Automatic resource cleanup

### Real-time Processing
- Low-latency data pipelines
- Efficient data structures
- Minimal copying
- Optimized algorithms

## Extensibility Points

### Adding New Data Sources
1. Create interface in `interfaces/`
2. Implement `read_data()` method
3. Register in `data_stream_controller.py`
4. Add to auto-detection logic

### Adding New Vendors
1. Add signature to `can_vendor_detector.py`
2. Create/import DBC file
3. Add to vendor detection logic

### Adding New Features
1. Create service in `services/`
2. Integrate with controller
3. Add UI components if needed
4. Update configuration system

## Deployment Architecture

### Edge Device (reTerminal DM / Raspberry Pi)
- Runs full application
- Local database
- Real-time processing
- USB storage support

### Cloud Services (Optional)
- PostgreSQL database
- REST API
- MQTT broker
- Analytics backend

### Mobile Companion (Future)
- Remote monitoring
- Push notifications
- Mobile dashboard

## Scalability

### Horizontal Scaling
- Multiple edge devices
- Centralized cloud database
- Load balancing for API

### Vertical Scaling
- Optimized for single device
- Efficient resource usage
- Background processing

## Reliability

### Fault Tolerance
- Automatic error recovery
- Graceful degradation
- Fallback mechanisms
- Health monitoring

### Data Integrity
- Transaction support
- Validation checks
- Backup strategies
- Sync verification

## Technology Stack

### Core
- **Python 3.8+**: Main language
- **PySide6/Qt6**: UI framework
- **SQLite**: Local database
- **PostgreSQL**: Cloud database

### AI/ML
- **scikit-learn**: Machine learning
- **numpy/pandas**: Data processing
- **joblib**: Model persistence

### Hardware
- **python-can**: CAN bus
- **python-OBD**: OBD-II
- **pyserial**: Serial communication
- **opencv-python**: Video processing

### Communication
- **paho-mqtt**: MQTT client
- **requests**: HTTP client
- **psycopg2**: PostgreSQL driver

## Development Workflow

1. **Local Development**: Demo mode with simulated data
2. **Testing**: Unit tests, integration tests
3. **Hardware Testing**: Real device testing
4. **Deployment**: Edge device deployment
5. **Monitoring**: Health monitoring and logging

## Future Architecture Enhancements

1. **Microservices**: Split into smaller services
2. **Containerization**: Docker support
3. **Kubernetes**: Orchestration for cloud
4. **GraphQL API**: Flexible data queries
5. **WebSocket**: Real-time updates
6. **Edge AI**: On-device model inference

