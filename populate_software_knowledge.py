#!/usr/bin/env python3
"""
Populate Software Knowledge Base
Adds comprehensive information about TelemetryIQ/AITUNER to the knowledge base.
"""

from services.vector_knowledge_store import VectorKnowledgeStore
from services.ai_advisor_rag import RAGAIAdvisor

def populate_software_knowledge():
    """Populate knowledge base with software information."""
    print("=" * 70)
    print("Populating Software Knowledge Base")
    print("=" * 70)
    
    vector_store = VectorKnowledgeStore()
    initial_count = vector_store.count()
    print(f"\nInitial knowledge base entries: {initial_count}")
    
    # Comprehensive TelemetryIQ knowledge
    software_knowledge = [
        {
            "topic": "TelemetryIQ Overview",
            "text": """Topic: TelemetryIQ Overview

What is TelemetryIQ?

TelemetryIQ is an AI-powered racing telemetry and tuning system. TelemetryIQ (also known as AI Tuner Agent or AITUNER) is a comprehensive edge computing platform for real-time vehicle telemetry, AI-driven tuning advice, performance tracking, and advanced racing analytics.

TelemetryIQ is the software you are using right now. TelemetryIQ provides real-time telemetry monitoring, AI-powered insights, performance tracking, video recording, and ECU tuning capabilities.

TelemetryIQ Key Features:
- Real-time telemetry from OBD-II, RaceCapture, and CAN bus
- AI-powered predictive fault detection and health scoring
- Performance tracking with Dragy-style 0-60, quarter-mile, and GPS lap timing
- Multi-camera support with telemetry overlays
- Voice control and hands-free operation
- Live streaming to YouTube and RTMP services
- Auto USB detection and configuration
- Multi-ECU support for 10+ vendors (Holley, HP Tuners, DiabloSport, SCT, COBB, etc.)

TelemetryIQ combines advanced telemetry collection with cutting-edge artificial intelligence to deliver insights that optimize performance, predict failures, and accelerate tuning decisions—all in real-time.

TelemetryIQ is designed for the reTerminal DM and Raspberry Pi 5 platforms.""",
            "keywords": ["telemetryiq", "aituner", "ai tuner", "software", "platform", "overview", "what is", "what is telemetryiq"]
        },
        {
            "topic": "TelemetryIQ AI Features",
            "text": """Topic: TelemetryIQ AI Features

TelemetryIQ includes advanced AI-powered features:

1. AI-Powered Analytics:
   - Predictive fault detection using machine learning
   - Real-time health scoring (0-100 scale)
   - Automated tuning recommendations
   - Trend analysis and pattern recognition

2. AI Chat Advisor (Q):
   - Conversational AI assistant
   - Answers questions about tuning, telemetry, and software features
   - Provides contextual advice based on current telemetry
   - Continuous learning from user feedback
   - RAG-based knowledge retrieval

3. Auto-Tuning Engine:
   - AI-driven automatic ECU parameter optimization
   - Adapts to conditions (weather, altitude, fuel)
   - Safety-first approach with validation

4. AI Racing Coach:
   - Real-time coaching with optimal driving line suggestions
   - Performance analysis and improvement recommendations""",
            "keywords": ["ai", "artificial intelligence", "machine learning", "predictive", "health score", "auto-tuning"]
        },
        {
            "topic": "TelemetryIQ Hardware Support",
            "text": """Topic: TelemetryIQ Hardware Support

TelemetryIQ supports multiple hardware platforms and data sources:

Primary Platform:
- reTerminal DM (recommended)
- Raspberry Pi 5 (compatible)

Data Sources:
- OBD-II (ELM327, STN1110, etc.)
- CAN bus (100+ CAN IDs supported)
- RaceCapture devices
- GPS for lap timing and performance tracking
- Analog sensors (ADC boards)
- Digital sensors (GPIO)

ECU Support:
- Holley EFI
- HP Tuners
- DiabloSport
- SCT
- COBB
- And 5+ more vendors

Camera Support:
- USB cameras (multiple simultaneous)
- Front/rear camera recording
- Telemetry overlay on video
- Live streaming capabilities""",
            "keywords": ["hardware", "obd", "can", "ecu", "camera", "gps", "sensors", "reterminal", "raspberry pi"]
        },
        {
            "topic": "TelemetryIQ Performance Tracking",
            "text": """Topic: TelemetryIQ Performance Tracking

TelemetryIQ includes comprehensive performance tracking features:

1. Dragy-Style Metrics:
   - 0-60 mph acceleration times
   - Quarter-mile times and trap speed
   - 60-130 mph times
   - Calculated using GPS data

2. GPS Lap Timing:
   - Automatic lap detection
   - Sector timing
   - Best lap tracking
   - Lap comparison (side-by-side and overlay)

3. Virtual Dyno:
   - Calculate horsepower from real-world driving
   - No expensive dyno runs needed
   - Uses acceleration data and vehicle weight

4. Performance Analytics:
   - Trend analysis over time
   - Compare different tuning configurations
   - Identify performance improvements
   - Track consistency""",
            "keywords": ["performance", "tracking", "draqy", "0-60", "quarter mile", "lap timing", "gps", "virtual dyno", "horsepower"]
        },
        {
            "topic": "TelemetryIQ Video Features",
            "text": """Topic: TelemetryIQ Video Features

TelemetryIQ includes professional video recording and streaming:

1. Multi-Camera Support:
   - Front and rear camera recording
   - Multiple USB cameras simultaneously
   - Automatic camera detection

2. Telemetry Overlays:
   - Customizable telemetry overlays on video
   - Real-time data display
   - RPM, speed, boost, AFR, and more
   - Customizable layout and styling

3. Live Streaming:
   - Direct streaming to YouTube
   - RTMP streaming support
   - Real-time telemetry overlay during stream
   - High-quality video encoding

4. Video Management:
   - Automatic file organization
   - USB storage detection
   - Cloud sync capabilities""",
            "keywords": ["video", "camera", "recording", "streaming", "youtube", "overlay", "telemetry overlay"]
        },
        {
            "topic": "TelemetryIQ Voice Control",
            "text": """Topic: TelemetryIQ Voice Control

TelemetryIQ includes hands-free voice control:

1. Voice Commands:
   - Start/stop recording
   - Take screenshot
   - Ask questions to AI advisor
   - Navigate interface
   - Control tuning parameters

2. Voice Feedback:
   - Verbal responses from AI advisor
   - Performance alerts
   - Safety warnings
   - Status updates

3. Hands-Free Operation:
   - No need to touch screen while driving
   - Critical for track use
   - Reduces distraction
   - Improves safety""",
            "keywords": ["voice", "speech", "hands-free", "voice control", "voice commands", "verbal"]
        },
        {
            "topic": "TelemetryIQ ECU Tuning",
            "text": """Topic: TelemetryIQ ECU Tuning

TelemetryIQ provides comprehensive ECU tuning capabilities:

1. Multi-ECU Support:
   - Holley EFI
   - HP Tuners
   - DiabloSport
   - SCT
   - COBB
   - And more (10+ vendors total)

2. Tuning Features:
   - Read ECU files
   - Write parameters (with safety validation)
   - Backup and restore configurations
   - Change tracking and version control
   - Safety classification system

3. AI Tuning Advisor:
   - Contextual tuning suggestions
   - Real-time recommendations based on telemetry
   - Safety warnings
   - Performance optimization advice

4. Auto-Tuning:
   - AI-driven automatic parameter optimization
   - Adapts to conditions
   - Safety-first approach""",
            "keywords": ["ecu", "tuning", "holley", "hp tuners", "diablosport", "sct", "cobb", "flash", "calibration"]
        },
        {
            "topic": "TelemetryIQ Safety Features",
            "text": """Topic: TelemetryIQ Safety Features

TelemetryIQ includes comprehensive safety features:

1. Safety Classification System:
   - Parameters classified by safety level
   - Warnings for dangerous changes
   - Validation before writing to ECU

2. Backup and Restore:
   - Automatic backups before changes
   - Easy restore to previous configuration
   - Version control for all changes

3. Panic Button:
   - Emergency safe stock map flash
   - Quick restore to safe configuration
   - Critical safety feature

4. Health Monitoring:
   - Real-time health scoring
   - Predictive fault detection
   - Safety warnings and alerts
   - Proactive issue detection""",
            "keywords": ["safety", "backup", "restore", "panic button", "health", "validation", "warning"]
        },
        {
            "topic": "TelemetryIQ Cloud and Mobile",
            "text": """Topic: TelemetryIQ Cloud and Mobile

TelemetryIQ includes cloud sync and mobile access:

1. Cloud Sync:
   - Automatic cloud backup
   - Sync across devices
   - Offline-first architecture
   - Secure encrypted storage

2. Mobile API:
   - RESTful API for mobile apps
   - Real-time telemetry access
   - Remote control capabilities
   - WebSocket support for live data

3. Remote Access:
   - Access from anywhere
   - View telemetry remotely
   - Control features remotely
   - Secure authentication

4. Fleet Management:
   - Manage multiple vehicles
   - Compare performance across fleet
   - Centralized monitoring""",
            "keywords": ["cloud", "mobile", "api", "remote", "sync", "fleet", "websocket"]
        },
        {
            "topic": "TelemetryIQ Installation and Setup",
            "text": """Topic: TelemetryIQ Installation and Setup

TelemetryIQ Setup:

1. Hardware Requirements:
   - reTerminal DM or Raspberry Pi 5
   - USB OBD-II adapter or CAN interface
   - USB cameras (optional)
   - USB storage (optional)

2. Software Installation:
   - Python 3.8+ required
   - Install dependencies: pip install -r requirements.txt
   - Run demo: python3 demo_safe.py

3. Initial Configuration:
   - Auto USB detection
   - ECU vendor detection
   - Camera detection
   - Network configuration

4. First Use:
   - Connect to vehicle
   - Select ECU vendor
   - Start telemetry collection
   - Ask AI advisor questions""",
            "keywords": ["installation", "setup", "install", "configuration", "requirements", "getting started"]
        },
        {
            "topic": "TelemetryIQ AI Chat Advisor",
            "text": """Topic: TelemetryIQ AI Chat Advisor (Q)

The AI Chat Advisor (called "Q") is an intelligent assistant built into TelemetryIQ:

1. Capabilities:
   - Answers questions about tuning, telemetry, and software features
   - Provides contextual advice based on current telemetry data
   - Explains technical concepts
   - Troubleshooting assistance
   - Step-by-step guidance

2. Knowledge Sources:
   - Built-in knowledge base about tuning and telemetry
   - Software documentation and features
   - Forum knowledge from tuning communities
   - Web search for current information
   - Continuous learning from user feedback

3. Features:
   - RAG-based (Retrieval Augmented Generation) for accurate answers
   - Semantic search for finding relevant information
   - Context-aware responses
   - Follow-up question suggestions
   - Safety warnings when appropriate

4. Usage:
   - Type questions in the chat interface
   - Ask about software features: "What is TelemetryIQ?"
   - Ask tuning questions: "How do I tune fuel pressure?"
   - Ask about telemetry: "What does this AFR reading mean?" """,
            "keywords": ["q", "ai advisor", "chat", "assistant", "help", "questions", "rag", "semantic search"]
        }
    ]
    
    print(f"\nAdding {len(software_knowledge)} software knowledge entries...")
    
    chunks_added = 0
    for entry in software_knowledge:
        try:
            vector_store.add_knowledge(
                text=entry["text"],
                metadata={
                    "topic": entry["topic"],
                    "category": "software",
                    "source": "software_documentation",
                    "keywords": ", ".join(entry["keywords"]),
                    "tuning_related": False,
                    "telemetry_relevant": True
                }
            )
            chunks_added += 1
            print(f"  ✓ Added: {entry['topic']}")
        except Exception as e:
            print(f"  ✗ Failed to add {entry['topic']}: {e}")
    
    final_count = vector_store.count()
    print(f"\n{'='*70}")
    print(f"Knowledge Base Update Complete")
    print(f"{'='*70}")
    print(f"Initial entries: {initial_count}")
    print(f"Added: {chunks_added}")
    print(f"Final entries: {final_count}")
    print(f"New entries: {final_count - initial_count}")
    
    # Test search
    print(f"\n{'='*70}")
    print("Testing Search")
    print(f"{'='*70}")
    
    test_queries = [
        "what is telemetryiq",
        "what features does telemetryiq have",
        "how do I use the AI advisor",
        "what ECUs does telemetryiq support"
    ]
    
    for query in test_queries:
        results = vector_store.search(query, n_results=2, min_similarity=0.3)
        print(f"\nQuery: '{query}'")
        if results:
            print(f"  Found {len(results)} results")
            for i, result in enumerate(results, 1):
                topic = result.get("metadata", {}).get("topic", "Unknown")
                similarity = result.get("similarity", 0)
                print(f"  {i}. {topic} (similarity: {similarity:.2f})")
        else:
            print("  No results found")
    
    print(f"\n{'='*70}")
    print("✅ Software knowledge populated!")
    print(f"{'='*70}")

if __name__ == "__main__":
    populate_software_knowledge()

