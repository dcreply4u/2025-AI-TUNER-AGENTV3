"""
Enhanced AI Advisor "Q" Service
Advanced AI advisor with intent classification, semantic matching, telemetry context,
and improved accuracy for tuning-related questions.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any

LOGGER = logging.getLogger(__name__)

# Try to import LLM libraries (optional)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None  # type: ignore

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    pipeline = None  # type: ignore

# Import conversational response manager
try:
    from services.conversational_responses import get_conversation_manager
    CONVERSATIONAL_RESPONSES_AVAILABLE = True
except ImportError:
    CONVERSATIONAL_RESPONSES_AVAILABLE = False
    get_conversation_manager = None  # type: ignore


class IntentType(Enum):
    """Intent classification types."""
    FEATURE_QUESTION = "feature_question"
    TROUBLESHOOTING = "troubleshooting"
    TUNING_ADVICE = "tuning_advice"
    TELEMETRY_QUERY = "telemetry_query"
    CONFIGURATION = "configuration"
    HOW_TO = "how_to"
    WHAT_IS = "what_is"
    COMPARISON = "comparison"
    SAFETY = "safety"
    PERFORMANCE = "performance"
    GREETING = "greeting"
    LOG_ANALYSIS = "log_analysis"  # Analyze data logs
    WHAT_IF = "what_if"  # Simulation scenarios
    TUNE_SUGGESTION = "tune_suggestion"  # Targeted tune recommendations
    STEP_BY_STEP = "step_by_step"  # Interactive guidance
    PROFESSIONAL_HANDOFF = "professional_handoff"  # Professional tuner referral
    UNKNOWN = "unknown"


@dataclass
class ChatMessage:
    """Chat message with metadata."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: float = field(default_factory=time.time)
    intent: Optional[IntentType] = None
    confidence: float = 1.0


@dataclass
class KnowledgeEntry:
    """Enhanced knowledge base entry."""
    topic: str
    keywords: List[str]
    content: str
    category: str  # "feature", "configuration", "troubleshooting", "tip", "tuning"
    related_topics: List[str] = field(default_factory=list)
    telemetry_relevant: bool = False  # If this topic relates to live telemetry
    tuning_related: bool = False  # If this is tuning-specific


@dataclass
class ResponseContext:
    """Context for generating accurate responses."""
    telemetry: Optional[Dict[str, float]] = None
    health_status: Optional[Dict[str, Any]] = None
    current_tab: Optional[str] = None
    recent_changes: List[Dict] = field(default_factory=list)
    vehicle_info: Optional[Dict[str, Any]] = None


@dataclass
class ResponseResult:
    """Structured response with metadata."""
    answer: str
    confidence: float
    intent: IntentType
    sources: List[str] = field(default_factory=list)  # Knowledge base topics used
    follow_up_questions: List[str] = field(default_factory=list)
    telemetry_integrated: bool = False
    warnings: List[str] = field(default_factory=list)  # Predictive warnings
    recommendations: List[str] = field(default_factory=list)  # Tune recommendations
    step_by_step_guide: Optional[List[str]] = None  # Interactive steps
    disclaimer_required: bool = False  # If legal disclaimer needed


class EnhancedAIAdvisorQ:
    """
    Enhanced AI Advisor "Q" - Advanced AI assistant with improved accuracy.
    
    Features:
    - Intent classification
    - Semantic matching (beyond keywords)
    - Telemetry context integration
    - Confidence scoring
    - Follow-up question suggestions
    - Context-aware responses
    - Tuning-specific knowledge
    """
    
    def __init__(
        self,
        use_llm: bool = False,
        llm_api_key: Optional[str] = None,
        config_monitor=None,
        telemetry_provider=None,
        enable_web_search: bool = True,
        vehicle_profile_provider=None,
        predictive_diagnostics=None,
        data_log_manager=None,
        tune_database=None,
    ) -> None:
        """
        Initialize Enhanced AI Advisor Q.
        
        Args:
            use_llm: Use external LLM for enhanced responses
            llm_api_key: API key for LLM service
            config_monitor: Intelligent config monitor instance
            telemetry_provider: Function to get current telemetry data
            enable_web_search: Enable internet research when available
            vehicle_profile_provider: Function to get vehicle profile
            predictive_diagnostics: PredictiveDiagnosticsEngine instance
            data_log_manager: DataLogManager instance
            tune_database: TuneMapDatabase instance
        """
        self.use_llm = use_llm and OPENAI_AVAILABLE
        self.llm_api_key = llm_api_key
        self.config_monitor = config_monitor
        self.telemetry_provider = telemetry_provider
        self.vehicle_profile_provider = vehicle_profile_provider
        self.predictive_diagnostics = predictive_diagnostics
        self.data_log_manager = data_log_manager
        self.tune_database = tune_database
        self.conversation_history: List[ChatMessage] = []
        self.knowledge_base: List[KnowledgeEntry] = []
        self.response_context = ResponseContext()
        
        # Initialize conversational response manager
        self.conversation_manager = None
        if CONVERSATIONAL_RESPONSES_AVAILABLE:
            try:
                self.conversation_manager = get_conversation_manager()
                LOGGER.info("Conversational response manager initialized")
            except Exception as e:
                LOGGER.warning("Failed to initialize conversation manager: %s", e)
                self.conversation_manager = None
        
        # Initialize web search service
        self.web_search = None
        if enable_web_search:
            try:
                from services.web_search_service import WebSearchService
                self.web_search = WebSearchService(enable_search=True)
                if self.web_search.is_available():
                    LOGGER.info("Web search enabled - AI advisor can research online")
                else:
                    LOGGER.info("Web search service initialized but internet not available")
            except Exception as e:
                LOGGER.warning("Failed to initialize web search: %s", e)
                self.web_search = None
        
        # Initialize knowledge base
        self._build_enhanced_knowledge_base()
        
        # Initialize LLM if requested
        if self.use_llm and llm_api_key:
            try:
                openai.api_key = llm_api_key
            except Exception as e:
                LOGGER.warning("Failed to initialize LLM: %s", e)
                self.use_llm = False
    
    def _build_enhanced_knowledge_base(self) -> None:
        """Build comprehensive knowledge base with tuning expertise."""
        
        # Tuning-specific knowledge
        self.knowledge_base.extend([
            KnowledgeEntry(
                topic="Fuel Tuning",
                keywords=["fuel", "afr", "lambda", "ve table", "fuel map", "rich", "lean", "stoichiometric"],
                content="""
Fuel Tuning Fundamentals:

VE Table (Volumetric Efficiency):
- Main fuel calibration map (Load vs RPM)
- Higher VE = more air = needs more fuel
- Typical range: 50-120% (turbo engines can exceed 100%)
- Use Local Autotune (A key) for automatic corrections
- Interpolate tables (Ctrl+H/V) to smooth transitions

AFR/Lambda Targets:
- Stoichiometric: 14.7:1 (Lambda 1.0) for gasoline
- WOT (Wide Open Throttle): 12.5-13.2:1 (Lambda 0.85-0.90) for power
- Idle/Cruise: 14.5-15.0:1 (Lambda 0.99-1.02) for efficiency
- E85: Stoichiometric is 9.8:1, adjust targets accordingly

Tuning Process:
1. Start with base map (from similar engines)
2. Use wideband O2 sensor for feedback
3. Make small adjustments (2-5% at a time)
4. Log data before and after changes
5. Test at various load/RPM points
6. Always backup before major changes

Common Issues:
- Too rich: Black smoke, poor fuel economy, fouled plugs
- Too lean: Engine knock, high EGT, potential damage
- Inconsistent: Check for boost leaks, MAF/MAP calibration
                """,
                category="tuning",
                related_topics=["ECU Tuning", "Sensors", "Auto Tuning"],
                telemetry_relevant=True,
                tuning_related=True,
            ),
            KnowledgeEntry(
                topic="Ignition Timing",
                keywords=["timing", "spark", "advance", "retard", "knock", "detonation", "mbt"],
                content="""
Ignition Timing Tuning:

MBT (Minimum Best Timing):
- Maximum Brake Torque timing for best power
- Typically 25-35° BTDC at WOT (varies by engine)
- Too advanced: Knock/detonation, engine damage
- Too retarded: Power loss, high EGT

Timing Map (Load vs RPM):
- Low load: More advance (efficiency)
- High load: Less advance (safety)
- Boost: Reduce timing (1-2° per psi boost)
- E85/Methanol: Can run more advance (higher octane)

Knock Detection:
- Knock sensor monitors detonation
- System can automatically retard timing
- If knock persists, reduce timing in that cell
- Check for other causes: too lean, too much boost, hot intake air

Tuning Tips:
- Start conservative (retard timing)
- Gradually advance until knock detected
- Back off 2-3° from knock threshold
- Monitor EGT (should be <900°C at WOT)
- Use knock sensor feedback for safety
                """,
                category="tuning",
                related_topics=["ECU Tuning", "Protections", "Knock Sensor"],
                telemetry_relevant=True,
                tuning_related=True,
            ),
            KnowledgeEntry(
                topic="Boost Control",
                keywords=["boost", "turbo", "wastegate", "psi", "bar", "overboost"],
                content="""
Boost Control Tuning:

Boost Targets:
- Street: 10-15 psi (0.7-1.0 bar)
- Track: 15-25 psi (1.0-1.7 bar)
- Race: 25+ psi (1.7+ bar) - requires built engine

Control Methods:
- Open Loop: Fixed duty cycle table
- Closed Loop: PID control with target table
- Gear-based: Different boost per gear
- RPM-based: Ramp boost with RPM

Wastegate Control:
- Solenoid duty cycle controls boost
- Higher duty = more boost (up to limit)
- Adjust duty cycle table (Load vs RPM)
- Use compensation tables for temperature/altitude

Safety:
- Set overboost protection (fuel cut or wastegate dump)
- Monitor boost spikes (can damage engine)
- Use boost ramp-in for smooth power delivery
- Check for boost leaks (inconsistent boost)

Tuning Process:
1. Start with low boost target
2. Gradually increase while monitoring AFR and timing
3. Adjust fuel and timing for higher boost
4. Test at various RPM points
5. Use boost compensation for conditions
                """,
                category="tuning",
                related_topics=["ECU Tuning", "Protections", "Turbo"],
                telemetry_relevant=True,
                tuning_related=True,
            ),
            KnowledgeEntry(
                topic="Nitrous Oxide Tuning",
                keywords=["nitrous", "n2o", "bottle", "solenoid", "progressive", "stage"],
                content="""
Nitrous Oxide System Tuning:

System Types:
- Dry: Nitrous only, ECU adds fuel
- Wet: Nitrous + fuel mixed, simpler setup
- Direct Port: Individual nozzles per cylinder
- Progressive: Gradual activation (smoother power)

Bottle Pressure:
- Optimal: 900-1100 psi
- Too low: Inconsistent flow, poor performance
- Too high: Risk of over-delivery
- Monitor pressure gauge

Progressive Control:
- Ramp-in: Gradual activation (prevents wheel spin)
- Time-based: Activate over X seconds
- RPM-based: Activate at specific RPM
- Speed-based: Activate at specific MPH

Fuel Enrichment:
- Nitrous requires additional fuel
- Typical: 50-100% fuel increase with nitrous
- Use separate fuel map or enrichment table
- Monitor AFR (should be 11.5-12.5:1 with nitrous)

Safety:
- RPM window: Only activate in safe RPM range
- Gear lockout: Disable in low gears
- Pressure monitoring: Shut off if pressure drops
- AFR monitoring: Shut off if too lean
- Max time limit: Prevent over-use

Tuning Tips:
- Start with small shot (50hp)
- Gradually increase while monitoring
- Use progressive activation for traction
- Always monitor AFR and EGT
- Test on dyno before track use
                """,
                category="tuning",
                related_topics=["ECU Tuning", "Racing Controls", "Safety"],
                telemetry_relevant=True,
                tuning_related=True,
            ),
            KnowledgeEntry(
                topic="Methanol Injection",
                keywords=["methanol", "meth", "water", "injection", "duty", "tank"],
                content="""
Methanol Injection Tuning:

System Purpose:
- Charge cooling (reduces intake air temperature)
- Octane boost (allows more timing/boost)
- Power increase (typically 50-150hp)

Injection Control:
- Duty cycle based on boost/RPM
- Typical: 10-30% duty at full boost
- Higher boost = more methanol needed
- Use duty cycle table (Load vs RPM)

Tank Level Monitoring:
- Monitor tank level (sensor required)
- Low level warning (system should shut off)
- Failsafe: Revert to safe map if empty

Timing/Boost Adjustment:
- Methanol allows more timing advance
- Can run higher boost safely
- Typical: +2-5° timing, +2-5 psi boost
- Use separate maps or compensation

Safety:
- Failsafe if flow stops (revert to safe map)
- Monitor flow rate (flow sensor)
- Low tank warning
- AFR monitoring (should stay safe)

Tuning Process:
1. Start with conservative injection rate
2. Gradually increase while monitoring IAT
3. Add timing/boost as IAT decreases
4. Test at various boost levels
5. Verify failsafe operation
                """,
                category="tuning",
                related_topics=["ECU Tuning", "Cooling", "Safety"],
                telemetry_relevant=True,
                tuning_related=True,
            ),
            KnowledgeEntry(
                topic="E85/Flex Fuel Tuning",
                keywords=["e85", "ethanol", "flex", "blend", "content", "sensor"],
                content="""
E85/Flex Fuel Tuning:

Ethanol Content:
- E85: 51-83% ethanol (varies by region/season)
- E10: 10% ethanol (standard pump gas)
- Pure Gasoline: 0% ethanol
- Sensor measures actual content (0-100%)

Fuel Requirements:
- E85 requires 30-40% more fuel (stoichiometric 9.8:1 vs 14.7:1)
- Use flex fuel sensor for automatic adjustment
- ECU can blend between gas and E85 maps
- Or use single map with ethanol compensation

Timing Benefits:
- E85 has higher octane (105-110 vs 87-93)
- Can run more timing advance
- Better knock resistance
- Typical: +3-8° timing with E85

Cooling Benefits:
- Ethanol has higher latent heat of vaporization
- Cools intake charge (similar to methanol)
- Reduces IAT (Intake Air Temperature)
- Allows more boost/timing

Tuning Process:
1. Install flex fuel sensor
2. Calibrate sensor (0% and 100% points)
3. Create separate fuel maps (gas and E85)
4. Or use single map with compensation
5. Add timing for E85 (use compensation table)
6. Test at various ethanol percentages
                """,
                category="tuning",
                related_topics=["ECU Tuning", "Fuel", "Sensors"],
                telemetry_relevant=True,
                tuning_related=True,
            ),
            KnowledgeEntry(
                topic="Advanced Tuning Strategies",
                keywords=["strategy", "approach", "method", "technique", "best practice", "optimization"],
                content="""
Advanced Tuning Strategies:

Systematic Approach:
1. Baseline: Log stock/current tune
2. Safety First: Set protections (rev limit, EGT, lean cut)
3. Fuel First: Get AFR correct before timing
4. Timing Second: Optimize after fuel is correct
5. Boost Last: Increase boost after fuel/timing optimized
6. Fine-tune: Small adjustments, test, repeat

Load-Based Tuning:
- Tune at various load points (not just RPM)
- Low load: Efficiency focus
- Medium load: Smooth power delivery
- High load: Maximum power
- WOT: Power and safety balance

RPM-Based Strategy:
- Idle (600-1000 RPM): Stability and smoothness
- Low RPM (1000-3000): Torque and response
- Mid RPM (3000-5000): Power building
- High RPM (5000-7000+): Maximum power

Environmental Adaptation:
- Temperature compensation (hot/cold)
- Altitude compensation (air density)
- Humidity effects (affects air density)
- Fuel quality variations

Data-Driven Tuning:
- Log every change
- Compare before/after
- Track trends over time
- Use wideband O2 for feedback
- Monitor knock sensor
- Track EGT for safety

Common Mistakes to Avoid:
- Changing too many things at once
- Not logging data
- Ignoring knock sensor
- Too aggressive too fast
- Not testing thoroughly
- Skipping safety checks
                """,
                category="tuning",
                related_topics=["ECU Tuning", "Best Practices"],
                tuning_related=True,
            ),
            KnowledgeEntry(
                topic="Knock Prevention and Management",
                keywords=["knock", "detonation", "pre-ignition", "ping", "prevent", "avoid"],
                content="""
Knock Prevention and Management:

What is Knock:
- Uncontrolled combustion (fuel ignites too early)
- Causes: Too much timing, too lean, too much boost, hot intake air
- Damage: Can destroy pistons, rings, head gaskets
- Sound: Metallic pinging/knocking

Prevention Strategies:
1. Conservative Timing: Start retarded, advance gradually
2. Proper AFR: Not too lean (12.5-13.2:1 at WOT)
3. Boost Management: Don't exceed safe levels
4. Intake Cooling: Intercooler, methanol, E85
5. Fuel Quality: Higher octane = more knock resistance
6. Engine Health: Clean injectors, good compression

Detection:
- Knock sensor: Detects vibration from knock
- EGT monitoring: High EGT can indicate knock risk
- Sound: Listen for pinging
- Power loss: Knock reduces power

Response to Knock:
- Immediate: Retard timing 2-3° in that cell
- Check AFR: May be too lean
- Check boost: May be too high
- Check IAT: May be too hot
- Check fuel quality: May need higher octane

Safe Tuning Process:
1. Start 5° retarded from estimated MBT
2. Advance 1° at a time
3. Test at each step
4. Stop when knock detected
5. Back off 2-3° from knock threshold
6. This is your safe timing for that condition

Monitoring:
- Always monitor knock sensor
- Log knock counts
- Track which cells have knock
- Adjust those cells specifically
- Don't ignore knock - it's engine damage waiting to happen
                """,
                category="tuning",
                related_topics=["Ignition Timing", "Safety", "Protections"],
                telemetry_relevant=True,
                tuning_related=True,
            ),
            KnowledgeEntry(
                topic="Turbo Tuning Fundamentals",
                keywords=["turbo", "turbocharger", "spool", "lag", "compressor", "turbine"],
                content="""
Turbo Tuning Fundamentals:

How Turbos Work:
- Exhaust spins turbine
- Turbine spins compressor
- Compressor forces air into engine
- More exhaust = more boost

Spool Characteristics:
- Small turbo: Fast spool, lower max boost
- Large turbo: Slow spool, higher max boost
- Twin turbo: Best of both (small + large)
- Variable geometry: Adjustable for spool and max boost

Boost Control:
- Wastegate: Bypasses exhaust to control boost
- Solenoid: Controls wastegate (duty cycle)
- Higher duty = more boost (up to turbo limit)
- Closed loop: Maintains target boost
- Open loop: Fixed duty cycle

Tuning for Spool:
- Exhaust tuning: Less backpressure = faster spool
- Ignition timing: More advance = more exhaust energy
- Fuel: Slightly rich helps spool (more exhaust)
- Anti-lag: Keeps turbo spooled off-throttle

Tuning for Power:
- More boost = more power (up to engine limit)
- Must add fuel for more boost
- Must reduce timing for more boost
- Monitor AFR and knock closely

Safety Considerations:
- Overboost protection: Fuel cut or wastegate dump
- Boost spikes: Can damage engine
- Surge: Compressor stall (bad for turbo)
- Overspeed: Turbo spinning too fast (damage)

Common Issues:
- Boost creep: Boost increases with RPM (wastegate too small)
- Boost lag: Slow spool (turbo too large)
- Inconsistent boost: Boost leaks or wastegate issues
- Boost spikes: Wastegate response too slow

Best Practices:
- Start with low boost target
- Gradually increase while monitoring
- Use boost ramp-in for smooth delivery
- Set overboost protection
- Check for boost leaks regularly
- Monitor turbo health (shaft play, oil)
                """,
                category="tuning",
                related_topics=["Boost Control", "Turbo"],
                telemetry_relevant=True,
                tuning_related=True,
            ),
            KnowledgeEntry(
                topic="Launch Control",
                keywords=["launch", "rpm", "limit", "staging", "transbrake", "two-step"],
                content="""
Launch Control Setup:

Purpose:
- Hold RPM at optimal launch RPM
- Prevent wheel spin on launch
- Consistent launches for drag racing

RPM Setting:
- Typical: 3000-5000 RPM (depends on vehicle)
- Too low: Bog off the line
- Too high: Wheel spin, broken parts
- Test to find optimal RPM

Control Methods:
- Fuel cut: Cuts fuel to limit RPM
- Spark cut: Cuts spark to limit RPM
- Blended: Combination of both (smoother)

Staging:
- Stage 1: Pre-stage beam (prepare)
- Stage 2: Stage beam (ready to launch)
- Launch: Green light (release transbrake)

Transbrake:
- Locks transmission in gear
- Allows full throttle while stationary
- Release on green light
- Requires transbrake solenoid/switch

Tuning Tips:
- Start with conservative RPM
- Gradually increase while testing
- Monitor wheel speed sensors
- Adjust for track conditions
- Use traction control if available
                """,
                category="tuning",
                related_topics=["Racing Controls", "Transmission"],
                telemetry_relevant=True,
                tuning_related=True,
            ),
            KnowledgeEntry(
                topic="Anti-Lag System",
                keywords=["anti-lag", "als", "wastegate", "turbo", "lag", "backfire"],
                content="""
Anti-Lag System Tuning:

Purpose:
- Keep turbo spooled when off throttle
- Eliminates turbo lag
- Used in rally/race applications

How It Works:
- Retards timing and adds fuel
- Unburned fuel ignites in exhaust
- Hot exhaust spins turbo
- Creates backfire/pop sound

Control Methods:
- Solenoid-based: Controls wastegate
- E-throttle: Uses throttle for control
- Ignition cut: Cuts spark in exhaust stroke

RPM Window:
- Only active in specific RPM range
- Typical: 2000-6000 RPM
- Disable at idle (too aggressive)
- Disable at high RPM (not needed)

Boost Target:
- Maintains boost pressure
- Typical: 5-15 psi
- Higher = more aggressive
- Monitor EGT (can get very hot)

Safety:
- High EGT (can damage turbo/exhaust)
- Increased wear on turbo
- Use only when needed (race mode)
- Monitor EGT closely

Tuning Tips:
- Start with low boost target
- Gradually increase while monitoring EGT
- Adjust timing retard amount
- Test on dyno first
- Use only in race conditions
                """,
                category="tuning",
                related_topics=["Racing Controls", "Turbo", "Safety"],
                telemetry_relevant=True,
                tuning_related=True,
            ),
            KnowledgeEntry(
                topic="ECU Tuning",
                keywords=["ecu", "tuning", "fuel", "ignition", "ve table", "map", "calibration"],
                content="""
ECU Tuning Overview:

Main Components:
- Fuel VE Table: Volumetric efficiency map (Load vs RPM)
- Ignition Timing Map: Spark advance map (Load vs RPM)
- Boost Control: Wastegate/solenoid control
- Idle Control: E-throttle, stepper motor, or timing
- Flex Fuel: E85 blending with automatic adjustment
- Individual Cylinder Correction: Per-cylinder trim
- Injector Staging: Primary/secondary injector control

Tuning Workflow:
1. Connect to ECU (CAN bus or direct)
2. Read current calibration
3. Backup original file
4. Make adjustments to maps
5. Test on dyno or track
6. Log data and analyze
7. Refine adjustments
8. Save and backup new calibration

Best Practices:
- Always backup before changes
- Make small incremental changes
- Test thoroughly before track use
- Log data for analysis
- Use predictive analytics
- Monitor safety systems
- Start conservative, tune up

Tools:
- Local Autotune (A key): Automatic fuel corrections
- Interpolation (Ctrl+H/V): Smooth table transitions
- 2D/3D View (V key): Visualize maps
- Live Logger (P key): Real-time data logging
- Backup System: Version control for calibrations
                """,
                category="feature",
                related_topics=["Fuel Tuning", "Ignition Timing", "Boost Control"],
                telemetry_relevant=True,
                tuning_related=True,
            ),
        ])
        
        # Add software feature knowledge (from original)
        self.knowledge_base.extend([
            KnowledgeEntry(
                topic="Protections",
                keywords=["protection", "rev limit", "egt", "lean", "safety"],
                content="""
Protection Features:
- Rev Limit: Fuel cut, spark cut, or blended with soft/hard cut
- EGT Protection: Exhaust gas temperature monitoring and power cut
- Lean Power Cut: Lambda-based fuel cut protection
- Signal Filters: TPS, RPM, MAP signal filtering
- Speed Limiters: Pit lane and road speed limiters

Configuration:
- Set soft cut percentage for gradual power reduction
- Configure EGT thresholds per cylinder
- Adjust filter aggressiveness (0-100%)
                """,
                category="feature",
                related_topics=["Safety", "ECU Tuning"],
            ),
            KnowledgeEntry(
                topic="Motorsport Features",
                keywords=["launch", "anti-lag", "traction", "boost", "shift"],
                content="""
Motorsport Features:
- Launch Control: 3-stage launch with RPM targets
- Anti-Lag: Solenoid or E-throttle based anti-lag
- Traction Control: Slip-based power management
- Boost Control: Advanced boost with compensation tables
- Shift Cut: Paddle shift support with duration/delay

Tips:
- Stage 1 launch for street, Stage 3 for drag racing
- Anti-lag requires wastegate control setup
- Traction control uses wheel speed sensors
                """,
                category="feature",
                related_topics=["Launch Control", "Anti-Lag System", "Racing Controls"],
            ),
            KnowledgeEntry(
                topic="Backup System",
                keywords=["backup", "revert", "version", "restore"],
                content="""
Backup & Version Control:
- Auto-backup on file save/change
- Backup before apply/burn operations
- Version history with timestamps
- Revert to previous versions
- Configurable retention policies

Usage:
- Click "Backup" button to create manual backup
- Click "Revert" to restore from backup
- Configure retention in Backup Manager tab
- Automatic cleanup of old backups

Tips:
- Always backup before major changes
- Use descriptive backup descriptions
- Check backup statistics regularly
                """,
                category="feature",
            ),
            KnowledgeEntry(
                topic="Troubleshooting",
                keywords=["error", "problem", "issue", "not working", "help"],
                content="""
Common Issues & Solutions:

Camera not detected:
- Check USB connection
- Try different USB port
- Verify camera works in other software
- Check USB Cameras tab for detection

GPIO not working:
- Verify hardware connection
- Check pin configuration
- Ensure proper permissions (Linux)
- Test with Hardware Interfaces tab

Backup failed:
- Check disk space
- Verify backup directory permissions
- Review Backup Manager settings

ECU not connecting:
- Check CAN bus connection
- Verify ECU is powered
- Check CAN bitrate settings
- Review auto-detection results

Tips:
- Check Status & Diagnostics tab
- Review error logs
- Use auto-detection features
                """,
                category="troubleshooting",
            ),
        ])
    
    def classify_intent(self, question: str) -> Tuple[IntentType, float]:
        """
        Classify user intent from question.
        
        Returns:
            (intent_type, confidence)
        """
        question_lower = question.lower()
        
        # Vehicle detection patterns (check first for vehicle-specific questions)
        vehicle_patterns = [
            r"\b(dodge|ford|chevrolet|chevy|gm|honda|toyota|nissan|bmw|mercedes|audi|porsche|subaru|mazda|lexus|acura|infiniti)\b",
            r"\b(hellcat|demon|redeye|viper|corvette|camaro|mustang|charger|challenger|supra|gtr|m3|m4|911|gt3|sti|type r)\b",
            r"\b(\d{4})\s+(dodge|ford|chevrolet|honda|toyota|nissan|bmw|mercedes)\b",  # Year + make
        ]
        has_vehicle = any(re.search(pattern, question_lower) for pattern in vehicle_patterns)
        
        # Intent patterns
        intent_patterns = {
            IntentType.GREETING: [
                r"\b(hi|hello|hey|greetings|good morning|good afternoon)\b",
            ],
            IntentType.TELEMETRY_QUERY: [
                r"\b(what is|what's|show|display|current|now|right now)\b.*\b(rpm|speed|temp|pressure|boost|afr|lambda)\b",
                r"\b(how (much|many|fast|hot|cold))\b",
                # Vehicle-specific queries
                r"\b(what (is|are|is the))\b.*\b(fuel pressure|oil pressure|boost|afr|timing|spec|specification)\b.*\b(for|on|in)\b",
            ],
            IntentType.TUNING_ADVICE: [
                r"\b(how (to|do|should|can))\b.*\b(tune|adjust|set|configure)\b",
                r"\b(what (should|is the best|is optimal))\b.*\b(timing|fuel|boost|afr)\b",
                r"\b(recommend|suggest|advice|tip)\b",
            ],
            IntentType.TROUBLESHOOTING: [
                r"\b(problem|issue|error|not working|broken|fault|fail)\b",
                r"\b(why (is|does|won't|can't))\b",
                r"\b(how (to fix|to solve|to repair))\b",
            ],
            IntentType.HOW_TO: [
                r"\b(how (to|do|can))\b",
                r"\b(step|steps|process|procedure)\b",
            ],
            IntentType.WHAT_IS: [
                r"\b(what (is|are|does|is a|is an))\b",
                r"\b(explain|tell me about|describe)\b",
                # Vehicle-specific "what is" questions
                r"\b(what (is|are|is the))\b.*\b(for|on|in)\b.*\b(dodge|ford|chevrolet|hellcat|corvette|camaro|mustang)\b",
            ],
            IntentType.CONFIGURATION: [
                r"\b(set|setup|configure|config|settings)\b",
                r"\b(where (is|are|do|can))\b.*\b(setting|config|option)\b",
            ],
            IntentType.SAFETY: [
                r"\b(safe|safety|dangerous|risk|damage|protect)\b",
                r"\b(too (much|many|high|low|hot|cold))\b",
            ],
            IntentType.PERFORMANCE: [
                r"\b(power|hp|horsepower|performance|speed|acceleration)\b",
                r"\b(how (fast|quick|much power))\b",
            ],
            IntentType.LOG_ANALYSIS: [
                r"\b(analyze|analysis|review|examine)\b.*\b(log|data log|datalog)\b",
                r"\b(upload|import|load)\b.*\b(log|datalog)\b",
                r"\b(what (is wrong|are the issues|problems))\b.*\b(log|data)\b",
            ],
            IntentType.WHAT_IF: [
                r"\b(what (if|would happen|will happen))\b",
                r"\b(simulate|simulation|predict)\b",
                r"\b(if i (increase|decrease|change|adjust))\b",
            ],
            IntentType.TUNE_SUGGESTION: [
                r"\b(suggest|recommend|recommendation)\b.*\b(tune|map|settings)\b",
                r"\b(what (tune|map|settings))\b.*\b(for|to)\b",
                r"\b(goal|target|want to)\b.*\b(power|efficiency|performance)\b",
            ],
            IntentType.STEP_BY_STEP: [
                r"\b(step by step|guide me|walk me through|how do i)\b",
                r"\b(instructions|tutorial|guide)\b",
            ],
            IntentType.PROFESSIONAL_HANDOFF: [
                r"\b(professional|tuner|expert|help me find)\b",
                r"\b(too (complex|difficult|hard))\b",
                r"\b(need (professional|expert|tuner))\b",
            ],
        }
        
        best_intent = IntentType.UNKNOWN
        best_score = 0.0
        
        for intent, patterns in intent_patterns.items():
            score = 0.0
            for pattern in patterns:
                matches = len(re.findall(pattern, question_lower))
                score += matches * 0.5
            
            # Keyword boost
            if intent == IntentType.TUNING_ADVICE:
                tuning_keywords = ["tune", "adjust", "timing", "fuel", "boost", "afr", "lambda", "ve table"]
                if any(kw in question_lower for kw in tuning_keywords):
                    score += 1.0
            
            if score > best_score:
                best_score = score
                best_intent = intent
        
        # Normalize confidence (0-1)
        confidence = min(1.0, best_score / 2.0) if best_score > 0 else 0.3
        
        return best_intent, confidence
    
    def _find_relevant_knowledge_enhanced(self, question: str, intent: IntentType) -> List[Tuple[KnowledgeEntry, float]]:
        """Enhanced knowledge matching with semantic scoring."""
        question_lower = question.lower()
        question_words = set(re.findall(r'\b\w+\b', question_lower))
        
        # Extract key terms from question (excluding common words)
        common_words = {'the', 'a', 'an', 'is', 'are', 'and', 'or', 'but', 'what', 'how', 'when', 'where', 
                       'why', 'for', 'with', 'from', 'to', 'on', 'in', 'at', 'by', 'of', 'this', 'that'}
        key_terms = {w for w in question_words if w not in common_words and len(w) > 2}
        
        # For "what is X" questions, extract the main subject
        main_subject = None
        if "what is" in question_lower or "what's" in question_lower or "what are" in question_lower:
            # Extract the main subject after "what is/are"
            parts = re.split(r"what (is|are|is the|are the|'s)", question_lower, 1)
            if len(parts) > 1:
                subject_part = parts[-1].strip()
                # Remove trailing common words
                subject_part = re.sub(r"\b(for|on|in|at|with|to|the)\b.*$", "", subject_part).strip()
                # Extract key words from subject
                subject_words = [w for w in re.findall(r'\b\w+\b', subject_part) if w not in common_words and len(w) > 2]
                if subject_words:
                    main_subject = " ".join(subject_words[:3])  # Take first 3 meaningful words
                    # Also add individual words to key_terms
                    key_terms.update(subject_words)
        
        scored_entries = []
        
        for entry in self.knowledge_base:
            score = 0.0
            
            # Exact topic match (highest priority) - must be exact phrase match
            topic_lower = entry.topic.lower()
            if topic_lower in question_lower:
                score += 15.0  # Increased from 10.0
            elif main_subject and main_subject in topic_lower:
                score += 12.0  # High score if main subject matches topic
            
            # For "what is" questions, require topic or keyword match
            is_what_is_question = "what is" in question_lower or "what's" in question_lower or "what are" in question_lower
            if is_what_is_question and main_subject:
                # Check if main subject is in topic or keywords
                topic_has_subject = any(word in topic_lower for word in main_subject.split())
                keywords_has_subject = any(word in [k.lower() for k in entry.keywords] for word in main_subject.split())
                
                if not topic_has_subject and not keywords_has_subject:
                    # This entry doesn't match the subject - skip it or heavily penalize
                    continue  # Skip entries that don't match the subject for "what is" questions
            
            # Keyword matching (weighted by importance)
            keyword_matches = []
            for kw in entry.keywords:
                kw_lower = kw.lower()
                if kw_lower in question_lower:
                    keyword_matches.append(kw)
                    # Exact keyword match gets higher score
                    if f" {kw_lower} " in f" {question_lower} ":
                        score += 6.0  # Increased from 5.0
                    else:
                        score += 2.5  # Increased from 2.0
                
                # For "what is" questions, check if keyword matches main subject
                if main_subject and kw_lower in main_subject:
                    score += 8.0  # High score for subject keyword match
            
            # Penalize if entry has keywords that don't match question
            entry_keywords_lower = {k.lower() for k in entry.keywords}
            question_keywords = {w for w in key_terms if len(w) > 3}  # Longer words are more specific
            
            # For "what is" questions, be stricter about keyword matching
            if is_what_is_question and main_subject:
                main_subject_words = set(main_subject.split())
                # Check if entry keywords match the main subject
                entry_matches_subject = any(kw in main_subject_words or any(sw in kw for sw in main_subject_words) 
                                           for kw in entry_keywords_lower)
                if not entry_matches_subject and len(keyword_matches) == 0:
                    # Entry doesn't match subject and has no keyword matches - skip
                    continue
            
            unmatched_entry_keywords = entry_keywords_lower - {w.lower() for w in question_keywords}
            if len(unmatched_entry_keywords) > len(keyword_matches) * 3:  # Stricter: was 2, now 3
                score *= 0.3  # Heavier penalty if too many unmatched keywords
            
            # Semantic matching (word overlap) - but only for relevant words
            entry_words = set(re.findall(r'\b\w+\b', entry.content.lower()))
            entry_words = {w for w in entry_words if w not in common_words and len(w) > 2}
            common_words_matched = question_words.intersection(entry_words)
            common_words_matched = {w for w in common_words_matched if w not in common_words}
            
            # Only count meaningful matches (technical terms, not generic words)
            technical_terms = {'pressure', 'rpm', 'boost', 'afr', 'timing', 'fuel', 'oil', 'temp', 
                              'temperature', 'sensor', 'ecu', 'tune', 'map', 'psi', 'bar', 'hp', 
                              'torque', 'knock', 'detonation', 'injector', 'turbo', 'supercharger'}
            meaningful_matches = {w for w in common_words_matched if w in technical_terms or len(w) > 4}
            
            # For "what is" questions, only count matches that are in the main subject
            if is_what_is_question and main_subject:
                main_subject_words = set(main_subject.split())
                # Only count matches that are part of the subject
                meaningful_matches = {w for w in meaningful_matches if w in main_subject_words}
            
            score += len(meaningful_matches) * 1.5  # Increased from 1.0
            
            # Intent-based boost
            if intent == IntentType.TUNING_ADVICE and entry.tuning_related:
                score += 3.0
            if intent == IntentType.TELEMETRY_QUERY and entry.telemetry_relevant:
                score += 2.0
            
            # Category matching
            if intent == IntentType.TROUBLESHOOTING and entry.category == "troubleshooting":
                score += 2.0
            if intent == IntentType.HOW_TO and entry.category == "tip":
                score += 1.5
            
            # Penalize if entry topic doesn't match question focus
            # If question asks about "fuel pressure" but entry is about "knock sensor", penalize heavily
            if len(key_terms) > 0:
                topic_words = set(re.findall(r'\b\w+\b', entry.topic.lower()))
                topic_overlap = key_terms.intersection(topic_words)
                if len(topic_overlap) == 0 and score > 0:
                    score *= 0.2  # Heavier penalty: was 0.3, now 0.2
            
            # For "what is" questions, if no topic/keyword match, don't include
            if is_what_is_question and main_subject:
                topic_has_subject = any(word in topic_lower for word in main_subject.split())
                keywords_has_subject = any(word in [k.lower() for k in entry.keywords] for word in main_subject.split())
                if not topic_has_subject and not keywords_has_subject and score < 5.0:
                    # Low score and no subject match - skip
                    continue
            
            if score > 0:
                scored_entries.append((entry, score))
        
        # Sort by score and return top matches
        scored_entries.sort(key=lambda x: x[1], reverse=True)
        
        # Filter out low-scoring matches (higher threshold for "what is" questions)
        threshold = 5.0 if is_what_is_question else 3.0  # Stricter threshold for "what is" questions
        filtered_entries = [(entry, score) for entry, score in scored_entries if score >= threshold]
        
        return filtered_entries[:5] if filtered_entries else (scored_entries[:2] if scored_entries else [])  # Top matches, or top 2 if all below threshold
    
    def _integrate_telemetry_context(self, response: str, knowledge: List[KnowledgeEntry], question: str = "") -> Tuple[str, bool]:
        """Integrate live telemetry data into response if relevant."""
        if not self.response_context.telemetry:
            return response, False
        
        telemetry = self.response_context.telemetry
        integrated = False
        question_lower = question.lower()
        
        # Check if any knowledge entry is telemetry-relevant
        if any(entry.telemetry_relevant for entry in knowledge):
            # Add telemetry context to response
            telemetry_info = []
            
            # Common telemetry values
            if "rpm" in question_lower or "engine" in question_lower:
                rpm = telemetry.get("RPM") or telemetry.get("Engine_RPM", 0)
                if rpm > 0:
                    telemetry_info.append(f"Current RPM: {rpm:.0f}")
                    integrated = True
            
            if "boost" in question_lower:
                boost = telemetry.get("Boost_Pressure") or telemetry.get("boost_psi", 0)
                if boost != 0:
                    telemetry_info.append(f"Current Boost: {boost:.1f} psi")
                    integrated = True
            
            if "afr" in question_lower or "lambda" in question_lower or "fuel" in question_lower:
                afr = telemetry.get("AFR") or telemetry.get("Lambda", 0)
                if afr > 0:
                    if afr > 2:  # Likely lambda
                        lambda_val = afr
                        afr_val = lambda_val * 14.7
                    else:  # Likely AFR
                        afr_val = afr
                        lambda_val = afr / 14.7
                    telemetry_info.append(f"Current AFR: {afr_val:.2f}:1 (Lambda: {lambda_val:.2f})")
                    integrated = True
            
            if "temp" in question_lower or "temperature" in question_lower:
                coolant = telemetry.get("Coolant_Temp") or telemetry.get("CoolantTemp", 0)
                if coolant > 0:
                    telemetry_info.append(f"Coolant Temp: {coolant:.1f}°C")
                    integrated = True
            
            if telemetry_info:
                response = f"{response}\n\n📊 Current Vehicle Status:\n" + "\n".join(f"• {info}" for info in telemetry_info)
        
        return response, integrated
    
    def ask(self, question: str, context: Optional[Dict[str, Any]] = None) -> ResponseResult:
        """
        Ask Q a question with enhanced accuracy.
        
        Args:
            question: User question
            context: Optional context (current tab, telemetry, etc.)
            
        Returns:
            ResponseResult with answer, confidence, and metadata
        """
        # Update context
        if context:
            if "telemetry" in context:
                self.response_context.telemetry = context["telemetry"]
            if "current_tab" in context:
                self.response_context.current_tab = context["current_tab"]
        
        # Get telemetry if provider available
        if self.telemetry_provider:
            try:
                self.response_context.telemetry = self.telemetry_provider()
            except (AttributeError, TypeError, ValueError) as e:
                LOGGER.debug("Telemetry provider unavailable: %s", e)
        
        # Add user message to history
        intent, intent_confidence = self.classify_intent(question)
        self.conversation_history.append(
            ChatMessage(role="user", content=question, intent=intent, confidence=intent_confidence)
        )
        
        # Update conversation context
        if self.conversation_manager:
            # Extract topic from question (simplified)
            topic_words = [w for w in question.lower().split() if len(w) > 3][:3]
            topic = " ".join(topic_words) if topic_words else None
            self.conversation_manager.update_context(topic=topic, interaction_type="question")
        
        # Find relevant knowledge
        knowledge_matches = self._find_relevant_knowledge_enhanced(question, intent)
        knowledge = [entry for entry, _ in knowledge_matches]
        
        # Check if we need web search (low confidence or no knowledge found)
        web_search_results = None
        if self.web_search and self.web_search.is_available():
            question_lower = question.lower()
            
            # Detect vehicle-specific questions
            vehicle_keywords = ["dodge", "ford", "chevrolet", "chevy", "honda", "toyota", "nissan", 
                              "hellcat", "demon", "corvette", "camaro", "mustang", "charger", "challenger",
                              "supra", "gtr", "m3", "m4", "911", "gt3", "sti", "type r"]
            has_vehicle = any(vk in question_lower for vk in vehicle_keywords)
            
            # Detect spec/technical questions
            spec_keywords = ["spec", "specification", "pressure", "psi", "bar", "rpm", "hp", "horsepower",
                           "torque", "boost", "afr", "timing", "fuel pressure", "oil pressure"]
            has_spec = any(sk in question_lower for sk in spec_keywords)
            
            # Use web search if:
            # 1. Vehicle-specific question (ALWAYS search for vehicle specs)
            # 2. No good knowledge matches (confidence < 5.0)
            # 3. Question asks about specific products/components/vehicles
            # 4. Troubleshooting questions
            # 5. "What is" questions about technical specs
            # 6. Spec/technical questions
            should_search = (
                has_vehicle or  # ALWAYS search for vehicle-specific questions
                has_spec or  # Search for technical specs
                not knowledge_matches or knowledge_matches[0][1] < 5.0 or
                intent in [IntentType.TROUBLESHOOTING, IntentType.WHAT_IS, IntentType.TELEMETRY_QUERY] or
                any(word in question_lower for word in ["spec", "specification", "details", "information about", "look up", "research", "what is", "what are"])
            )
            
            if should_search:
                try:
                    web_search_results = self._perform_web_search(question, intent)
                    if web_search_results:
                        LOGGER.info("Web search found %d results for: %s", 
                                  len(web_search_results.results), question)
                except (requests.RequestException, ValueError, KeyError) as e:
                    LOGGER.warning("Web search failed: %s", e)
        
        # Initialize default values
        warnings = []
        recommendations = []
        step_by_step = None
        predictive_warnings = []
        
        # Handle special intents that need dedicated processing
        if intent == IntentType.LOG_ANALYSIS:
            answer, log_warnings, log_recommendations = self._handle_log_analysis(question, knowledge)
            warnings.extend(log_warnings)
            recommendations.extend(log_recommendations)
        elif intent == IntentType.WHAT_IF:
            answer, whatif_warnings = self._handle_what_if_scenario(question, knowledge)
            warnings.extend(whatif_warnings)
        elif intent == IntentType.TUNE_SUGGESTION:
            answer, tune_recommendations, tune_steps = self._handle_tune_suggestion(question, knowledge)
            recommendations.extend(tune_recommendations)
            step_by_step = tune_steps
        elif intent == IntentType.STEP_BY_STEP:
            answer, step_guide = self._handle_step_by_step_guidance(question, knowledge)
            step_by_step = step_guide
        elif intent == IntentType.PROFESSIONAL_HANDOFF:
            answer, handoff_warnings = self._handle_professional_handoff(question, knowledge)
            warnings.extend(handoff_warnings)
        else:
            # Standard response generation
            if self.use_llm:
                answer = self._generate_llm_response(question, knowledge, intent, web_search_results)
            else:
                answer = self._generate_enhanced_response(question, knowledge, intent, web_search_results)
        
        # Enhance with conversational formatting if manager available
        if self.conversation_manager and intent != IntentType.GREETING:
            answer = self.conversation_manager.get_contextual_response(
                question=question,
                base_response=answer,
                intent=intent.value if hasattr(intent, 'value') else str(intent),
            )
        
        # Integrate telemetry context
        answer, telemetry_integrated = self._integrate_telemetry_context(answer, knowledge, question)
        
        # Get predictive warnings if available
        if self.predictive_diagnostics and self.response_context.telemetry:
            try:
                predictive_warnings = self.predictive_diagnostics.analyze_telemetry(
                    self.response_context.telemetry
                )
                if predictive_warnings:
                    warnings.extend([w.message for w in predictive_warnings if hasattr(w, 'message')])
            except Exception as e:
                LOGGER.debug("Predictive diagnostics unavailable: %s", e)
        
        # Calculate confidence
        confidence = self._calculate_confidence(intent_confidence, knowledge_matches, telemetry_integrated)
        
        # Generate follow-up questions
        follow_ups = self._generate_follow_ups(intent, knowledge, question)
        
        # Build sources list (knowledge + web search)
        sources = [entry.topic for entry in knowledge]
        if web_search_results:
            sources.extend([f"Web: {r.title}" for r in web_search_results.results[:3]])
        
        # Determine if disclaimer is needed (tuning advice, what-if, tune suggestions)
        disclaimer_required = intent in [
            IntentType.TUNING_ADVICE,
            IntentType.WHAT_IF,
            IntentType.TUNE_SUGGESTION,
            IntentType.STEP_BY_STEP,
        ]
        
        # Add disclaimer to answer if needed
        if disclaimer_required:
            answer = self._add_disclaimer(answer)
        
        # Create response result
        result = ResponseResult(
            answer=answer,
            confidence=confidence,
            intent=intent,
            sources=sources,
            follow_up_questions=follow_ups,
            telemetry_integrated=telemetry_integrated,
            warnings=warnings,
            recommendations=recommendations,
            step_by_step_guide=step_by_step,
            disclaimer_required=disclaimer_required,
        )
        
        # Add to history
        self.conversation_history.append(
            ChatMessage(role="assistant", content=answer, intent=intent, confidence=confidence)
        )
        
        # Keep history manageable
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        return result
    
    def _perform_web_search(self, question: str, intent: IntentType):
        """Perform web search based on question and intent."""
        if not self.web_search or not self.web_search.is_available():
            return None
        
        try:
            question_lower = question.lower()
            
            # Detect vehicle-specific questions
            vehicle_keywords = ["dodge", "ford", "chevrolet", "chevy", "honda", "toyota", "nissan", 
                              "hellcat", "demon", "corvette", "camaro", "mustang", "charger", "challenger",
                              "supra", "gtr", "m3", "m4", "911", "gt3", "sti", "type r"]
            has_vehicle = any(vk in question_lower for vk in vehicle_keywords)
            
            # Detect spec/technical questions
            spec_keywords = ["pressure", "psi", "bar", "rpm", "hp", "horsepower", "torque", 
                           "boost", "afr", "timing", "fuel pressure", "oil pressure", "spec", "specification"]
            has_spec = any(sk in question_lower for sk in spec_keywords)
            
            # For vehicle-specific spec questions, use optimized search query
            if has_vehicle and has_spec:
                # Extract vehicle name and spec type
                vehicle = None
                spec_type = None
                
                for vk in vehicle_keywords:
                    if vk in question_lower:
                        vehicle = vk
                        break
                
                for sk in spec_keywords:
                    if sk in question_lower:
                        spec_type = sk
                        break
                
                if vehicle and spec_type:
                    # Create optimized search query
                    search_query = f"{vehicle} {spec_type} specification"
                    LOGGER.info(f"Vehicle spec search: {search_query}")
                    return self.web_search.search(search_query, max_results=5)
            
            # Adjust search query based on intent
            if intent == IntentType.TROUBLESHOOTING:
                return self.web_search.find_troubleshooting_info(question)
            elif intent == IntentType.WHAT_IS or intent == IntentType.TELEMETRY_QUERY:
                # Extract the subject of "what is" question
                if "what is" in question_lower or "what's" in question_lower or "what are" in question_lower:
                    # Extract the main subject
                    parts = re.split(r"what (is|are|is the|are the|'s)", question_lower, 1)
                    if len(parts) > 1:
                        subject = parts[-1].strip()
                        # Clean up common trailing words
                        subject = re.sub(r"\b(for|on|in|at|with|to|the)\b.*$", "", subject).strip()
                        if subject:
                            return self.web_search.lookup_specification(subject)
                # Fallback to direct search
                return self.web_search.search(question, max_results=5)
            elif intent == IntentType.PERFORMANCE:
                return self.web_search.research_topic(question, "performance tuning")
            else:
                # General search
                return self.web_search.search(question, max_results=5)
        except Exception as e:
            LOGGER.warning("Web search error: %s", e)
            return None
    
    def _generate_enhanced_response(
        self,
        question: str,
        knowledge: List[KnowledgeEntry],
        intent: IntentType,
        web_search_results=None,
    ) -> str:
        """Generate response using enhanced rule-based system."""
        question_lower = question.lower()
        
        # Greeting - use conversational manager if available
        if intent == IntentType.GREETING:
            if self.conversation_manager:
                # Update context for greeting
                self.conversation_manager.update_context(topic="greeting", interaction_type="greeting")
                return self.conversation_manager.get_greeting(
                    is_returning=len(self.conversation_history) > 0,
                    user_input=question
                )
            # Fallback to original greeting
            return """Hello! I'm Q, your TelemetryIQ AI advisor. I can help you with:

• Tuning advice and best practices
• ECU configuration and setup
• Troubleshooting issues
• Software features and usage
• Real-time telemetry analysis
• Safety recommendations

What would you like to know?"""
        
        # Check if this is a vehicle-specific question
        vehicle_keywords = ["dodge", "ford", "chevrolet", "chevy", "honda", "toyota", "nissan", 
                          "hellcat", "demon", "corvette", "camaro", "mustang", "charger", "challenger",
                          "supra", "gtr", "m3", "m4", "911", "gt3", "sti", "type r"]
        has_vehicle = any(vk in question_lower for vk in vehicle_keywords)
        
        # For vehicle-specific questions, prioritize web search results
        if has_vehicle and web_search_results and web_search_results.results:
            response_parts = ["🌐 I researched this for you:\n"]
            
            # Extract key information from web results
            for result in web_search_results.results[:3]:
                response_parts.append(f"📋 {result.title}")
                if result.snippet:
                    # Try to extract specific numbers/values from snippet
                    snippet = result.snippet
                    # Look for pressure values (PSI, bar)
                    pressure_match = re.search(r'(\d+(?:\.\d+)?)\s*(psi|bar|PSI|BAR)', snippet, re.IGNORECASE)
                    if pressure_match:
                        response_parts.append(f"  ⚡ {pressure_match.group(0)}")
                    response_parts.append(f"  {snippet[:200]}")
                response_parts.append(f"  🔗 Source: {result.url}\n")
            
            response_parts.append("💡 Note: These are general specifications. Actual values may vary by year, model, and modifications.")
            return "\n".join(response_parts)
        
        # If we have relevant knowledge, use it
        if knowledge:
            response_parts = []
            
            # Check knowledge relevance - if score is low and we have web search, prioritize web
            knowledge_score = knowledge[0].__dict__.get('_score', 0) if hasattr(knowledge[0], '__dict__') else 5.0
            if knowledge_score < 3.0 and web_search_results and web_search_results.results:
                # Low relevance knowledge - prioritize web search
                response_parts = ["🌐 I found this information:\n"]
                for result in web_search_results.results[:3]:
                    response_parts.append(f"📋 {result.title}")
                    if result.snippet:
                        response_parts.append(f"  {result.snippet[:200]}")
                    response_parts.append(f"  🔗 {result.url}\n")
                return "\n".join(response_parts)
            
            # Primary knowledge (high relevance)
            primary = knowledge[0]
            response_parts.append(primary.content.strip())
            
            # Add related topics if available
            if len(knowledge) > 1:
                response_parts.append("\n\nRelated Information:")
                for entry in knowledge[1:3]:  # Up to 2 additional entries
                    response_parts.append(f"\n{entry.topic}:\n{entry.content[:200]}...")
            
            # Add community insights if available
            community_insights = self._get_community_insights(question, knowledge)
            if community_insights:
                response_parts.append("\n\n👥 Community Insights:")
                for insight in community_insights[:2]:  # Top 2 insights
                    response_parts.append(f"\n• {insight.get('title', 'Community Solution')}")
                    response_parts.append(f"  {insight.get('description', '')[:150]}...")
                    if insight.get('verified'):
                        response_parts.append("  ✓ Verified by community")
            
            # Add web search results if available (as supplementary)
            if web_search_results and web_search_results.results:
                response_parts.append("\n\n🌐 Additional Information (from web research):")
                for result in web_search_results.results[:2]:  # Limit to 2 for supplementary
                    response_parts.append(f"\n• {result.title}")
                    if result.snippet:
                        response_parts.append(f"  {result.snippet[:150]}...")
                    response_parts.append(f"  Source: {result.url}")
            
            return "\n".join(response_parts)
        
        # If no knowledge but we have web search results
        if web_search_results and web_search_results.results:
            response_parts = ["🌐 I found some information online:\n"]
            for result in web_search_results.results[:3]:
                response_parts.append(f"📋 {result.title}")
                if result.snippet:
                    response_parts.append(f"  {result.snippet}")
                response_parts.append(f"  🔗 {result.url}\n")
            response_parts.append("\n💡 Note: This information is from web research. Please verify for your specific application.")
            return "\n".join(response_parts)
        
        # Default response based on intent
        if intent == IntentType.TUNING_ADVICE:
            return """I can help with tuning advice! Try asking about:
• Fuel tuning and AFR targets
• Ignition timing optimization
• Boost control setup
• Nitrous/methanol/E85 tuning
• Launch control and anti-lag

What specific tuning topic would you like help with?"""
        
        if intent == IntentType.TELEMETRY_QUERY:
            return """I can provide real-time telemetry information. Try asking:
• "What is the current RPM?"
• "Show me boost pressure"
• "What's the AFR right now?"
• "How hot is the coolant?"

Make sure telemetry is connected for live data."""
        
        # Generic fallback
        return """I'm Q, your TelemetryIQ AI advisor. I can help with tuning, configuration, troubleshooting, and more.

Try asking about:
• How to tune fuel or timing
• ECU configuration
• Troubleshooting issues
• Software features
• Current telemetry values

What would you like to know?"""
    
    def _calculate_confidence(
        self,
        intent_confidence: float,
        knowledge_matches: List[Tuple[KnowledgeEntry, float]],
        telemetry_integrated: bool,
    ) -> float:
        """Calculate overall response confidence."""
        if not knowledge_matches:
            return 0.3  # Low confidence if no knowledge found
        
        # Base confidence from knowledge match quality
        best_match_score = knowledge_matches[0][1] if knowledge_matches else 0
        knowledge_confidence = min(1.0, best_match_score / 10.0)
        
        # Combine with intent confidence
        combined = (intent_confidence * 0.3 + knowledge_confidence * 0.7)
        
        # Boost if telemetry integrated
        if telemetry_integrated:
            combined = min(1.0, combined + 0.1)
        
        return combined
    
    def _generate_follow_ups(self, intent: IntentType, knowledge: List[KnowledgeEntry], question: str = "") -> List[str]:
        """Generate relevant follow-up questions based on actual knowledge matches."""
        follow_ups = []
        
        # Only generate follow-ups if we have relevant knowledge
        if not knowledge:
            return follow_ups
        
        question_lower = question.lower()
        
        # Extract main topic from question
        main_topic = None
        if "what is" in question_lower or "what's" in question_lower:
            parts = re.split(r"what (is|are|is the|are the|'s)", question_lower, 1)
            if len(parts) > 1:
                topic_part = parts[-1].strip()
                topic_part = re.sub(r"\b(for|on|in|at|with|to|the)\b.*$", "", topic_part).strip()
                main_topic = topic_part.split()[0] if topic_part.split() else None
        
        # Check if knowledge actually matches the question topic
        knowledge_matches_question = True
        if main_topic:
            # Check if any knowledge entry topic or keywords contain the main topic
            knowledge_matches_question = any(
                main_topic in entry.topic.lower() or 
                any(main_topic in kw.lower() for kw in entry.keywords)
                for entry in knowledge
            )
        
        # Only generate follow-ups if knowledge matches the question
        if not knowledge_matches_question:
            return follow_ups  # Don't suggest irrelevant follow-ups
        
        if intent == IntentType.TUNING_ADVICE:
            if any("fuel" in entry.topic.lower() for entry in knowledge):
                follow_ups.extend([
                    "How do I tune ignition timing?",
                    "What AFR should I target?",
                    "How do I use Local Autotune?",
                ])
            elif any("timing" in entry.topic.lower() for entry in knowledge):
                follow_ups.extend([
                    "How do I tune fuel?",
                    "What is MBT timing?",
                    "How do I prevent knock?",
                ])
            else:
                follow_ups.extend([
                    "How do I tune fuel?",
                    "How do I tune ignition timing?",
                    "What are safe tuning practices?",
                ])
        
        elif intent == IntentType.TELEMETRY_QUERY:
            follow_ups.extend([
                "What should normal values be?",
                "How do I interpret this data?",
                "Is this value safe?",
            ])
        
        return follow_ups[:3]  # Max 3 follow-ups
    
    def _generate_llm_response(
        self,
        question: str,
        knowledge: List[KnowledgeEntry],
        intent: IntentType,
        web_search_results=None,
    ) -> str:
        """Generate response using LLM (if available)."""
        if not OPENAI_AVAILABLE:
            return self._generate_enhanced_response(question, knowledge, intent)
        
        try:
            # Build knowledge context
            knowledge_context = "\n\n".join([entry.content for entry in knowledge])
            
            # Add web search results to context if available
            web_context = ""
            if web_search_results and web_search_results.results:
                web_context = "\n\nAdditional web research results:\n"
                for result in web_search_results.results:
                    web_context += f"\n{result.title}:\n{result.snippet}\nSource: {result.url}\n"
            
            # Build system prompt
            system_prompt = """You are Q, the AI advisor for TelemetryIQ racing tuner software.
You are an expert in engine tuning, ECU calibration, and racing performance.
Be concise, accurate, and helpful. Use the provided knowledge base to answer questions accurately.
If web research results are provided, incorporate them into your response and cite sources.
If telemetry data is available, integrate it into your response."""
            
            # Build messages with web search context
            messages = [
                {"role": "system", "content": system_prompt},
            ]
            
            # Add knowledge and web search context
            user_message = f"Question: {question}\n\n"
            if knowledge_context:
                user_message += f"Knowledge Base:\n{knowledge_context}\n\n"
            if web_context:
                user_message += f"Web Research:\n{web_context}\n\n"
            user_message += "Please provide a helpful, accurate answer based on the information above."
            
            messages.append({"role": "user", "content": user_message})
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.7,
            )
            
            return response.choices[0].message.content.strip()
            
        except (ValueError, KeyError, AttributeError, ImportError) as e:
            LOGGER.error("LLM response generation failed: %s", e, exc_info=True)
            return self._generate_enhanced_response(question, knowledge, intent)
    
    def _handle_log_analysis(self, question: str, knowledge: List[KnowledgeEntry]) -> Tuple[str, List[str], List[str]]:
        """Handle data log analysis requests."""
        warnings = []
        recommendations = []
        
        if not self.data_log_manager:
            return (
                "Data log analysis requires the data log manager to be configured. "
                "Please ensure data logging is enabled.",
                warnings,
                recommendations,
            )
        
        answer_parts = ["📊 Data Log Analysis\n"]
        answer_parts.append("To analyze a data log:\n")
        answer_parts.append("1. Upload your data log file (CSV, JSON, or vendor-specific format)")
        answer_parts.append("2. The system will automatically detect the format")
        answer_parts.append("3. Analysis will identify:\n")
        answer_parts.append("   • Inconsistencies in AFR, timing, or boost")
        answer_parts.append("   • Safety issues (knock, overboost, high temps)")
        answer_parts.append("   • Performance inefficiencies")
        answer_parts.append("   • Trends and patterns")
        answer_parts.append("\n4. You'll receive specific recommendations for improvements")
        
        # If predictive diagnostics available, add analysis capabilities
        if self.predictive_diagnostics:
            answer_parts.append("\n\n🔍 Advanced Analysis Available:")
            answer_parts.append("• Predictive failure detection")
            answer_parts.append("• Trend analysis across multiple logs")
            answer_parts.append("• Pattern recognition")
            answer_parts.append("• Component health scoring")
        
        return "\n".join(answer_parts), warnings, recommendations
    
    def _handle_what_if_scenario(self, question: str, knowledge: List[KnowledgeEntry]) -> Tuple[str, List[str]]:
        """Handle what-if scenario simulation requests."""
        warnings = []
        question_lower = question.lower()
        
        answer_parts = ["🔮 What-If Scenario Analysis\n"]
        
        # Extract parameters from question
        boost_change = None
        timing_change = None
        fuel_change = None
        
        # Parse boost changes
        if "boost" in question_lower:
            import re
            boost_match = re.search(r'boost.*?(\d+)\s*psi', question_lower)
            if boost_match:
                boost_change = float(boost_match.group(1))
        
        # Parse timing changes
        if "timing" in question_lower or "advance" in question_lower:
            import re
            timing_match = re.search(r'(\d+)\s*degrees?', question_lower)
            if timing_match:
                timing_change = float(timing_match.group(1))
        
        if boost_change or timing_change or fuel_change:
            answer_parts.append("Simulation Results:\n")
            
            # Simple simulation (would be enhanced with actual models)
            if boost_change:
                # Rough estimate: +1 PSI ≈ +7-10% power (varies by engine)
                power_gain = (boost_change - 15) * 7  # Assuming 15 PSI baseline
                answer_parts.append(f"• Boost: {boost_change} PSI")
                answer_parts.append(f"  Estimated power change: ~{power_gain:+.0f} HP")
                answer_parts.append(f"  ⚠️ Requires fuel enrichment (+{abs(power_gain)*0.1:.1f}% fuel)")
                answer_parts.append(f"  ⚠️ May require timing retard (-1 to -2 degrees)")
                warnings.append(f"Increasing boost to {boost_change} PSI requires careful fuel and timing adjustments")
            
            if timing_change:
                # Rough estimate: +1 degree ≈ +1-2% power (up to MBT)
                power_gain = timing_change * 1.5
                answer_parts.append(f"• Timing: {timing_change:+} degrees")
                answer_parts.append(f"  Estimated power change: ~{power_gain:+.0f} HP")
                if timing_change > 0:
                    warnings.append("Advancing timing increases knock risk - monitor knock sensor closely")
                else:
                    answer_parts.append(f"  ✓ Safer, but may reduce power")
            
            answer_parts.append("\n⚠️ These are estimates. Actual results depend on:")
            answer_parts.append("• Engine build and modifications")
            answer_parts.append("• Fuel quality and octane rating")
            answer_parts.append("• Ambient conditions")
            answer_parts.append("• Current tune state")
            answer_parts.append("\n💡 Always test incrementally and monitor all parameters!")
        else:
            answer_parts.append("I can simulate the effects of tuning changes.")
            answer_parts.append("\nTry asking:")
            answer_parts.append("• \"What if I increase boost from 15 to 20 PSI?\"")
            answer_parts.append("• \"What happens if I advance timing by 2 degrees?\"")
            answer_parts.append("• \"Simulate increasing fuel by 5%\"")
        
        return "\n".join(answer_parts), warnings
    
    def _handle_tune_suggestion(self, question: str, knowledge: List[KnowledgeEntry]) -> Tuple[str, List[str], Optional[List[str]]]:
        """Handle targeted tune suggestions based on user goals."""
        recommendations = []
        step_by_step = None
        question_lower = question.lower()
        
        answer_parts = ["🎯 Targeted Tune Suggestions\n"]
        
        # Determine goal
        goal = None
        if any(word in question_lower for word in ["power", "hp", "horsepower", "performance"]):
            goal = "max_power"
        elif any(word in question_lower for word in ["efficiency", "economy", "mpg", "fuel"]):
            goal = "efficiency"
        elif any(word in question_lower for word in ["safe", "reliable", "conservative"]):
            goal = "safety"
        elif any(word in question_lower for word in ["race", "track", "competition"]):
            goal = "race"
        
        # Get vehicle info for tune suggestions
        vehicle_info = self.response_context.vehicle_info or {}
        ecu_type = vehicle_info.get("ecu_vendor", "generic")
        
        # Search tune database if available
        tune_suggestions = []
        if self.tune_database:
            try:
                from services.tune_map_database import VehicleIdentifier, TuneType
                
                # Create vehicle identifier (would use actual profile data)
                vehicle = VehicleIdentifier(
                    make=vehicle_info.get("make", "Unknown"),
                    model=vehicle_info.get("model", "Unknown"),
                    year=vehicle_info.get("year", 2020),
                )
                
                # Search for relevant tunes
                if goal == "max_power":
                    tunes = self.tune_database.search_tunes(
                        ecu_type=ecu_type,
                        tune_type=TuneType.PERFORMANCE,
                    )
                elif goal == "efficiency":
                    tunes = self.tune_database.search_tunes(
                        ecu_type=ecu_type,
                        tune_type=TuneType.ECONOMY,
                    )
                elif goal == "race":
                    tunes = self.tune_database.search_tunes(
                        ecu_type=ecu_type,
                        tune_type=TuneType.RACE,
                    )
                else:
                    tunes = self.tune_database.get_base_maps(vehicle, ecu_type)
                
                if tunes:
                    tune_suggestions = tunes[:3]  # Top 3 matches
            except Exception as e:
                LOGGER.debug("Failed to search tune database: %s", e)
        
        if tune_suggestions:
            answer_parts.append("📋 Recommended Tunes from Database:\n")
            for tune in tune_suggestions:
                answer_parts.append(f"• {tune.name}")
                if tune.performance_gains:
                    if tune.performance_gains.hp_gain:
                        answer_parts.append(f"  Power gain: +{tune.performance_gains.hp_gain} HP")
                    if tune.performance_gains.torque_gain:
                        answer_parts.append(f"  Torque gain: +{tune.performance_gains.torque_gain} lb-ft")
                if tune.hardware_requirements:
                    answer_parts.append(f"  Required: {', '.join([h.component for h in tune.hardware_requirements[:2]])}")
                recommendations.append(f"Load tune: {tune.name}")
        else:
            # Provide general recommendations based on goal
            if goal == "max_power":
                answer_parts.append("Goal: Maximum Power\n")
                answer_parts.append("Recommended adjustments:")
                recommendations.extend([
                    "Enrich AFR to 12.5-12.8:1 at WOT",
                    "Advance timing to MBT (monitor knock)",
                    "Increase boost gradually (with fuel/timing adjustments)",
                    "Optimize VE table for your modifications",
                ])
                step_by_step = [
                    "1. Start with base map or current tune",
                    "2. Enrich fuel map at WOT (target 12.5-12.8:1 AFR)",
                    "3. Gradually advance timing (2° at a time, monitor knock)",
                    "4. Increase boost in 2 PSI increments",
                    "5. Test and log each change",
                    "6. Stop if knock detected or AFR goes lean",
                ]
            elif goal == "efficiency":
                answer_parts.append("Goal: Fuel Efficiency\n")
                recommendations.extend([
                    "Lean out cruise AFR to 15.0-15.5:1",
                    "Optimize timing for efficiency (not power)",
                    "Reduce boost at part throttle",
                    "Improve VE table accuracy",
                ])
            elif goal == "safety":
                answer_parts.append("Goal: Safe & Reliable\n")
                recommendations.extend([
                    "Use conservative AFR targets (12.8-13.2:1 at WOT)",
                    "Retard timing 2-3° from aggressive tunes",
                    "Set conservative boost limits",
                    "Enable all safety protections",
                ])
            else:
                answer_parts.append("I can suggest tunes based on your goals.")
                answer_parts.append("\nTell me:")
                answer_parts.append("• \"I want maximum power\"")
                answer_parts.append("• \"I want better fuel economy\"")
                answer_parts.append("• \"I want a safe, reliable tune\"")
        
        return "\n".join(answer_parts), recommendations, step_by_step
    
    def _handle_step_by_step_guidance(self, question: str, knowledge: List[KnowledgeEntry]) -> Tuple[str, Optional[List[str]]]:
        """Handle interactive step-by-step tuning guidance."""
        question_lower = question.lower()
        step_by_step = None
        
        # Determine what they want guidance on
        if "fuel" in question_lower or "afr" in question_lower or "ve table" in question_lower:
            answer = "📖 Step-by-Step Fuel Tuning Guide\n"
            step_by_step = [
                "1. Load a base map for your engine/ECU combination",
                "2. Connect wideband O2 sensor (essential for accurate tuning)",
                "3. Start data logging (P key or Live Logger button)",
                "4. Make a WOT pull and review the log",
                "5. Identify cells where AFR is off-target",
                "6. Use Local Autotune (A key) for automatic corrections, or",
                "7. Manually adjust VE table cells (increase VE if too lean, decrease if too rich)",
                "8. Make small changes (2-5% at a time)",
                "9. Test again and compare logs",
                "10. Repeat until AFR is consistent across all load/RPM points",
                "11. Always backup your tune before major changes!",
            ]
        elif "timing" in question_lower or "ignition" in question_lower:
            answer = "📖 Step-by-Step Ignition Timing Guide\n"
            step_by_step = [
                "1. Start with conservative timing (retard from aggressive tunes)",
                "2. Ensure fuel map is properly calibrated first",
                "3. Enable knock sensor monitoring",
                "4. Make a WOT pull and log data",
                "5. Gradually advance timing (1-2° at a time)",
                "6. Monitor for knock - if detected, retard immediately",
                "7. Target MBT (Maximum Brake Torque) timing",
                "8. Back off 2-3° from knock threshold for safety margin",
                "9. Test at various RPM and load points",
                "10. Use timing compensation tables for conditions (temp, altitude)",
            ]
        elif "boost" in question_lower:
            answer = "📖 Step-by-Step Boost Control Setup\n"
            step_by_step = [
                "1. Verify wastegate and boost control solenoid are properly installed",
                "2. Set conservative boost target initially (10-12 PSI)",
                "3. Configure boost control table (duty cycle vs RPM/Load)",
                "4. Start with low duty cycle (30-40%)",
                "5. Make a pull and log boost pressure",
                "6. Gradually increase duty cycle until target boost is reached",
                "7. Adjust fuel and timing for increased boost",
                "8. Set overboost protection (fuel cut or wastegate dump)",
                "9. Test boost ramp-in for smooth power delivery",
                "10. Monitor for boost spikes and leaks",
            ]
        else:
            answer = "📖 Step-by-Step Tuning Guidance\n"
            answer += "\nI can guide you through:\n"
            answer += "• Fuel tuning (VE table, AFR targets)\n"
            answer += "• Ignition timing setup\n"
            answer += "• Boost control configuration\n"
            answer += "• Nitrous system tuning\n"
            answer += "• Launch control setup\n"
            answer += "\nWhat would you like step-by-step guidance on?"
            step_by_step = None
        
        return answer, step_by_step
    
    def _handle_professional_handoff(self, question: str, knowledge: List[KnowledgeEntry]) -> Tuple[str, List[str]]:
        """Handle professional tuner handoff requests."""
        warnings = []
        
        answer_parts = ["👨‍🔧 Professional Tuner Handoff\n"]
        answer_parts.append("For complex tuning issues, I can help you connect with a professional tuner.\n")
        answer_parts.append("Services available:")
        answer_parts.append("• Remote tuning consultation")
        answer_parts.append("• Data log review and analysis")
        answer_parts.append("• Custom tune development")
        answer_parts.append("• Troubleshooting complex issues")
        answer_parts.append("\nTo request professional help:")
        answer_parts.append("1. Export your current tune file")
        answer_parts.append("2. Export recent data logs")
        answer_parts.append("3. Document your vehicle setup and modifications")
        answer_parts.append("4. Describe the issue or goal")
        answer_parts.append("5. Use the Professional Tuner tab to submit a request")
        answer_parts.append("\nYour data will be securely transmitted and reviewed by certified tuners.")
        answer_parts.append("You'll receive a quote before any work begins.")
        
        warnings.append("Professional tuning services are paid consultations. Review pricing before submitting.")
        
        return "\n".join(answer_parts), warnings
    
    def _get_community_insights(self, question: str, knowledge: List[KnowledgeEntry]) -> List[Dict[str, Any]]:
        """Get community insights for similar questions."""
        insights = []
        
        try:
            from services.community_knowledge_sharing import CommunityKnowledgeSharing
            
            # Search community knowledge for similar issues/solutions
            question_lower = question.lower()
            
            # Extract key terms for searching
            key_terms = []
            if "knock" in question_lower or "detonation" in question_lower:
                key_terms.append("knock")
            if "afr" in question_lower or "fuel" in question_lower or "lean" in question_lower or "rich" in question_lower:
                key_terms.append("fuel")
            if "timing" in question_lower or "ignition" in question_lower:
                key_terms.append("timing")
            if "boost" in question_lower:
                key_terms.append("boost")
            
            # Search community tips for relevant solutions
            # This would use the CommunityKnowledgeSharing service to search
            # For now, return empty (would be implemented with actual service instance)
            # Example:
            # community_service = CommunityKnowledgeSharing()
            # tips = community_service.search_tips(key_terms)
            # for tip in tips[:2]:
            #     insights.append({
            #         "title": tip.title,
            #         "description": tip.content,
            #         "verified": tip.verified,
            #     })
        except Exception as e:
            LOGGER.debug("Failed to get community insights: %s", e)
        
        return insights
    
    def _add_disclaimer(self, answer: str) -> str:
        """Add legal disclaimer to tuning advice."""
        disclaimer = "\n\n" + "="*60 + "\n"
        disclaimer += "⚠️ IMPORTANT LEGAL DISCLAIMER\n"
        disclaimer += "="*60 + "\n"
        disclaimer += "The AI advisor provides recommendations and suggestions based on general tuning principles.\n"
        disclaimer += "These are NOT guaranteed results and may not be suitable for your specific vehicle.\n\n"
        disclaimer += "• You are solely responsible for any changes made to your vehicle\n"
        disclaimer += "• Incorrect tuning can cause engine damage, void warranties, or create safety hazards\n"
        disclaimer += "• Always test changes incrementally and monitor all parameters\n"
        disclaimer += "• Consult a professional tuner for complex modifications\n"
        disclaimer += "• This software and its AI advisor are provided 'as-is' without warranties\n"
        disclaimer += "="*60
        
        return answer + disclaimer
    
    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []
    
    def get_suggestions(self, partial_question: str) -> List[str]:
        """Get suggested questions based on partial input."""
        suggestions = []
        partial_lower = partial_question.lower()
        
        common_questions = [
            "How do I tune fuel?",
            "What is the optimal AFR?",
            "How do I set ignition timing?",
            "What boost pressure should I run?",
            "How do I configure launch control?",
            "How do I tune nitrous?",
            "How do I set up methanol injection?",
            "What is the current RPM?",
            "How do I prevent knock?",
            "What are safe tuning practices?",
        ]
        
        for q in common_questions:
            if partial_lower in q.lower() or not partial_question:
                suggestions.append(q)
        
        return suggestions[:5]
    
    def update_telemetry(self, telemetry: Dict[str, float]) -> None:
        """Update telemetry context."""
        self.response_context.telemetry = telemetry


__all__ = ["EnhancedAIAdvisorQ", "ResponseResult", "IntentType"]

