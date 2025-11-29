"""
AI Advisor "Q" Service
Onboard AI agent that answers questions about the software, configuration, and provides help/tips
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .session_analysis_service import SessionAnalysisReport, SessionAnalysisService
from .driver_performance_summary import DriverPerformanceSummaryService
from .tuning_suggestion_service import TuningSuggestionService, TuningSuggestion

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


@dataclass
class ChatMessage:
    """Chat message."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class KnowledgeEntry:
    """Knowledge base entry."""
    topic: str
    keywords: List[str]
    content: str
    category: str  # "feature", "configuration", "troubleshooting", "tip"


class AIAdvisorQ:
    """
    AI Advisor "Q" - Onboard assistant for TelemetryIQ software.
    
    Features:
    - Answers questions about software features
    - Helps with configuration
    - Provides tips and tricks
    - Context-aware responses
    - Optional LLM enhancement
    """
    
    def __init__(
        self,
        use_llm: bool = False,
        llm_api_key: Optional[str] = None,
        config_monitor=None,
        session_analyzer: Optional[SessionAnalysisService] = None,
        driver_performance_service: Optional[DriverPerformanceSummaryService] = None,
        tuning_suggestion_service: Optional[TuningSuggestionService] = None,
    ):
        """
        Initialize AI Advisor Q.
        
        Args:
            use_llm: Use external LLM for enhanced responses
            llm_api_key: API key for LLM service
            config_monitor: Intelligent config monitor instance
        """
        self.use_llm = use_llm and OPENAI_AVAILABLE
        self.llm_api_key = llm_api_key
        self.config_monitor = config_monitor
        # Optional helpers for data‑driven answers
        self.session_analyzer = session_analyzer or SessionAnalysisService()
        self.driver_performance_service = (
            driver_performance_service or DriverPerformanceSummaryService()
        )
        self.tuning_suggestion_service = (
            tuning_suggestion_service or TuningSuggestionService()
        )
        self.conversation_history: List[ChatMessage] = []
        self.knowledge_base: List[KnowledgeEntry] = []
        
        # Initialize knowledge base
        self._build_knowledge_base()
        
        # Initialize LLM if requested
        if self.use_llm and llm_api_key:
            try:
                openai.api_key = llm_api_key
            except Exception as e:
                LOGGER.warning("Failed to initialize LLM: %s", e)
                self.use_llm = False
    
    def _build_knowledge_base(self) -> None:
        """Build comprehensive knowledge base about the software."""
        
        # Main Features
        self.knowledge_base.extend([
            KnowledgeEntry(
                topic="ECU Tuning",
                keywords=["ecu", "tuning", "fuel", "ignition", "ve table", "map"],
                content="""
ECU Tuning Features:
- Fuel VE Table: Main volumetric efficiency map for fuel calibration
- Ignition Timing: Spark advance control with knock protection
- Boost Control: Closed/open loop boost management
- Idle Control: E-throttle, stepper motor, or timing-based idle
- Flex Fuel: E85 blending with automatic map switching
- Individual Cylinder Correction: Per-cylinder fuel/ignition trim
- Injector Staging: Primary/secondary injector control
- Trailing Ignition: Secondary ignition event (for rotary engines)

Tips:
- Use Local Autotune (A key) for automatic fuel corrections
- Interpolate tables (Ctrl+H/V) to smooth transitions
- Always backup before making changes (Backup button)
- Use 2D/3D view toggle (V key) to visualize maps
                """,
                category="feature"
            ),
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
                category="feature"
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
                category="feature"
            ),
            KnowledgeEntry(
                topic="Transmission Control",
                keywords=["transmission", "tcu", "gearbox", "shift", "clutch"],
                content="""
Transmission Control:
- Supported Gearboxes: GM 4L80E/4L85E, 4L60E, Toyota A340E/A341E, BMW DCT, VAG DSG, 8HP, Sequential
- Clutch Slip Control: Torque converter/clutch pack pressure management
- Sequential Control: Strain gauge inputs and solenoid actuation
- CAN TCU Control: OEM protocol integration

Configuration:
- Select gearbox type from dropdown
- Configure clutch slip tables (Load vs Gear)
- Set sequential shift parameters
                """,
                category="feature"
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
                category="feature"
            ),
            KnowledgeEntry(
                topic="Hardware Interfaces",
                keywords=["gpio", "arduino", "i2c", "spi", "serial", "breakout"],
                content="""
Hardware Interface Support:
- GPIO Breakout Boards: Raspberry Pi, Jetson, Arduino, ESP32
- I2C Devices: ADC boards, sensors, multiple devices on one bus
- SPI Devices: High-speed sensors and interfaces
- Serial/UART: GPS, serial sensors, USB serial devices
- CAN Bus: Automotive CAN interfaces

Arduino Setup:
1. Upload firmware (hardware/arduino_gpio_breakout.ino)
2. Connect via USB
3. Auto-detected by system
4. Configure pins in GPIO Configuration tab

Tips:
- Use Arduino for additional GPIO pins
- I2C allows up to 127 devices on one bus
- Check Hardware Interfaces tab for detected devices
                """,
                category="feature"
            ),
            KnowledgeEntry(
                topic="USB Cameras",
                keywords=["camera", "usb", "webcam", "video", "preview"],
                content="""
USB Camera Support:
- Auto-detection of USB cameras
- Vendor-specific optimizations (Logitech, Microsoft, etc.)
- Resolution enumeration
- Live preview
- Multiple camera support

Supported Vendors:
- Logitech: C920, C922, C930e, BRIO, StreamCam, etc.
- Microsoft: LifeCam series
- Creative, Razer, Corsair
- Generic UVC cameras

Usage:
- Cameras auto-detected on startup
- Use USB Cameras tab to manage
- Click "Preview" to test camera
- Configure in Video/Overlay tab for recording
                """,
                category="feature"
            ),
            KnowledgeEntry(
                topic="Sensors",
                keywords=["sensor", "knock", "maf", "map", "o2", "temperature"],
                content="""
Sensor Support:
- Knock Sensor: Detonation detection
- MAF/MAP: Airflow measurement
- Oxygen Sensors: Wideband and narrowband
- Temperature Sensors: Coolant, air intake, EGT
- Pressure Sensors: Oil, fuel, boost
- Position Sensors: TPS, camshaft, crankshaft
- Speed Sensors: Vehicle speed, wheel speed

Configuration:
- Each sensor has dedicated settings in Sensors tab
- Configure calibration, scaling, and thresholds
- Set up alerts and warnings
                """,
                category="feature"
            ),
            KnowledgeEntry(
                topic="Keyboard Shortcuts",
                keywords=["shortcut", "key", "keyboard", "hotkey"],
                content="""
Keyboard Shortcuts:
- V: Toggle 2D/3D view
- Ctrl+H: Horizontal interpolation
- Ctrl+V: Vertical interpolation
- Ctrl+S: Table smoothing
- A: Local Autotune
- P: Live Logger toggle

Tips:
- Shortcuts work in active tab
- Some shortcuts are context-specific
- Check tooltips for available shortcuts
                """,
                category="tip"
            ),
            KnowledgeEntry(
                topic="Configuration Tips",
                keywords=["config", "setup", "configure", "settings"],
                content="""
Configuration Tips:
- Use Racing Mode selector for context-specific UI
- Configure backup settings before tuning
- Set up hardware interfaces before connecting sensors
- Test cameras before recording sessions
- Enable auto-backup for safety

Best Practices:
- Start with conservative settings
- Make small incremental changes
- Log data before and after changes
- Use predictive analytics for recommendations
- Monitor safety alerts closely
                """,
                category="tip"
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
                category="troubleshooting"
            ),
        ])
    
    def ask(self, question: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Ask Q a question.
        
        Args:
            question: User question
            context: Optional context (current tab, telemetry, change info, etc.)
            
        Returns:
            Q's response
        """
        # Add user message to history
        self.conversation_history.append(ChatMessage(role="user", content=question))
        
        # 1) Configuration change analysis
        if context and "change" in context:
            change = context["change"]
            # Provide proactive advice about the change
            response = self._analyze_config_change(change, context)
        else:
            # 2) Driver performance questions (0‑60, 1/4 mile, distance, etc.)
            driver_answer = self._maybe_answer_with_driver_performance(
                question, context or {}
            )
            if driver_answer:
                response = driver_answer
            else:
                # 3) Tuning‑oriented questions (what should I change in the tune?)
                tuning_answer = self._maybe_answer_with_tuning_suggestions(
                    question, context or {}
                )
                if tuning_answer:
                    response = tuning_answer
                else:
                    # 4) Session‑specific telemetry analysis (AFR, temps, boost, etc.)
                    telemetry_answer = self._maybe_answer_with_session_analysis(
                        question, context or {}
                    )
                    if telemetry_answer:
                        response = telemetry_answer
                    else:
                        # 5) Fallback to knowledge base / LLM
                        relevant_knowledge = self._find_relevant_knowledge(question)
                        if self.use_llm:
                            response = self._generate_llm_response(
                                question, relevant_knowledge, context
                            )
                        else:
                            response = self._generate_rule_based_response(
                                question, relevant_knowledge, context
                            )
        
        # Add response to history
        self.conversation_history.append(ChatMessage(role="assistant", content=response))
        
        # Keep history manageable (last 20 messages)
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        return response
    
    def _analyze_config_change(self, change, context: Optional[Dict[str, Any]] = None) -> str:
        """Analyze a configuration change and provide advice."""
        if not self.config_monitor:
            return "I can't analyze configuration changes right now. Please check the configuration monitor."
        
        # Get warnings and suggestions
        warnings = self.config_monitor.monitor_change(
            change.change_type,
            change.category,
            change.parameter,
            change.old_value,
            change.new_value,
            context.get("telemetry") if context else None,
        )
        
        if not warnings:
            return f"Configuration change looks reasonable. {change.parameter} changed from {change.old_value} to {change.new_value}. Monitor telemetry to verify results."
        
        # Build response from warnings
        response = "⚠️ I've analyzed your configuration change and here's what I found:\n\n"
        
        critical_warnings = [w for w in warnings if w.severity == "critical"]
        if critical_warnings:
            response += "🚨 CRITICAL WARNINGS:\n"
            for warning in critical_warnings:
                response += f"• {warning.message}\n"
                if warning.suggestion:
                    response += f"  💡 Suggestion: {warning.suggestion}\n"
                if warning.alternative_value is not None:
                    response += f"  ✅ Better option: Try {warning.alternative_value} instead\n"
            response += "\n"
        
        high_warnings = [w for w in warnings if w.severity == "high"]
        if high_warnings:
            response += "⚠️ WARNINGS:\n"
            for warning in high_warnings:
                response += f"• {warning.message}\n"
                if warning.suggestion:
                    response += f"  💡 {warning.suggestion}\n"
            response += "\n"
        
        info_warnings = [w for w in warnings if w.severity == "info"]
        if info_warnings:
            response += "💡 SUGGESTIONS:\n"
            for warning in info_warnings:
                response += f"• {warning.message}\n"
        
        return response

    # ------------------------------------------------------------------ #
    # Session / Telemetry‑aware answers
    # ------------------------------------------------------------------ #

    def _maybe_answer_with_tuning_suggestions(
        self,
        question: str,
        context: Dict[str, Any],
    ) -> Optional[str]:
        """
        Answer questions like:
        - "What tune changes do you recommend from the last session?"
        - "How can I make the car safer / richer / less knock‑prone?"
        """
        q = question.lower()
        tuning_keywords = [
            "tune",
            "tuning",
            "map",
            "fuel",
            "ignition",
            "spark",
            "boost",
            "safe",
            "safety",
            "recommend",
            "suggestion",
            "what should i change",
            "what should i adjust",
        ]
        if not any(k in q for k in tuning_keywords):
            return None

        # Re‑use the latest session analysis and tuning suggestions
        suggestions = self.get_latest_tuning_suggestions()
        if suggestions is None:
            # Analysis failed; fall back to normal knowledge path
            return None

        if not suggestions:
            # No samples or no actionable findings
            return (
                "I analyzed the latest session and didn't see any major issues that "
                "would force tune changes. You can keep your current calibration and "
                "continue gathering more data."
            )

        lines: List[str] = []
        lines.append(
            "Based on the latest session data, here are some high‑level tuning and "
            "setup suggestions. Treat these as guidance – always validate changes "
            "carefully on your specific engine and fuel:"
        )
        lines.append("")

        for s in suggestions:
            prefix = "•"
            if s.severity == "warning":
                prefix = "⚠️"
            elif s.severity == "critical":
                prefix = "🚨"
            lines.append(f"{prefix} [{s.category}] {s.message}")
            lines.append(f"    – {s.rationale}")

        lines.append(
            "\nIf you tell me more about your goals (e.g. 'maximum power on E85' vs "
            "'safe track day on pump fuel'), I can help you prioritize these changes."
        )

        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Public helper APIs for UI / tooling
    # ------------------------------------------------------------------ #

    def get_latest_tuning_suggestions(self) -> Optional[List[TuningSuggestion]]:
        """
        Return structured tuning suggestions from the most recent session log.

        This is used by the UI to render a live "Tuning Suggestions" panel next
        to the chat, and by _maybe_answer_with_tuning_suggestions() to avoid
        duplicating logic.

        Returns:
            - list[TuningSuggestion]: if analysis ran successfully (may be empty
              when there is no data or no anomalies)
            - None: if analysis failed (I/O error, parse error, etc.)
        """
        # Re‑use the latest session analysis
        try:
            report: SessionAnalysisReport = self.session_analyzer.analyze_latest_session()
        except Exception as e:
            LOGGER.debug("Tuning suggestions: session analysis failed: %s", e)
            return None

        if report.sample_count == 0:
            # Valid but no data yet
            return []

        try:
            suggestions: List[TuningSuggestion] = (
                self.tuning_suggestion_service.suggest_from_session(report)
            )
        except Exception as e:
            LOGGER.debug("Tuning suggestions generation failed: %s", e)
            return None

        return suggestions

    def _maybe_answer_with_driver_performance(
        self,
        question: str,
        context: Dict[str, Any],
    ) -> Optional[str]:
        """
        Answer questions about straight‑line performance using a PerformanceSnapshot
        provided in the context (key: 'performance_snapshot').
        """
        q = question.lower()
        if not any(k in q for k in ["0-60", "0 to 60", "60ft", "quarter", "1/4", "half mile", "1/2 mile", "distance", "drag", "acceleration"]):
            return None

        snapshot = context.get("performance_snapshot")
        if snapshot is None:
            return None

        try:
            # Accept either a PerformanceSnapshot or a dict with the same fields
            if not isinstance(snapshot, dict):
                # dataclass instance – use its __dict__ for safety
                snap_dict = {
                    "metrics": getattr(snapshot, "metrics", {}),
                    "best_metrics": getattr(snapshot, "best_metrics", {}),
                    "total_distance_m": getattr(snapshot, "total_distance_m", 0.0),
                }
            else:
                snap_dict = snapshot

            fake_snapshot = PerformanceSnapshot(
                metrics=snap_dict.get("metrics", {}),
                best_metrics=snap_dict.get("best_metrics", {}),
                total_distance_m=snap_dict.get("total_distance_m", 0.0),
                track_points=snap_dict.get("track_points", []),
                last_update=snap_dict.get("last_update", 0.0),
            )

            summary = self.driver_performance_service.summarize(fake_snapshot)
        except Exception as e:
            LOGGER.debug("Driver performance summary failed: %s", e)
            return None

        lines: List[str] = []
        lines.append("Here's a quick summary of your straight‑line performance this session:")
        if summary.best_0_60_s:
            lines.append(f"- Best 0–60 mph: {summary.best_0_60_s:.2f} s")
        else:
            lines.append("- 0–60 mph: no complete run detected yet.")

        if summary.best_quarter_mile_s:
            lines.append(f"- Best 1/4 mile ET: {summary.best_quarter_mile_s:.2f} s")
        if summary.best_half_mile_s:
            lines.append(f"- Best 1/2 mile ET: {summary.best_half_mile_s:.2f} s")

        lines.append(f"- Total distance covered: {summary.total_distance_km:.2f} km")
        lines.append(
            "\nYou can ask follow‑ups like:\n"
            "- \"How can I improve my 60‑foot time?\"\n"
            "- \"Is my 0–60 consistent between runs?\""
        )

        return "\n".join(lines)

    def _maybe_answer_with_session_analysis(
        self,
        question: str,
        context: Dict[str, Any],
    ) -> Optional[str]:
        """
        If the question is clearly about AFR, temps, boost, or session behaviour,
        try to answer using the latest session analysis report.
        """
        if not self.session_analyzer:
            return None

        q = question.lower()
        keywords = ["afr", "lambda", "lean", "rich", "knock", "egt", "coolant", "temp", "overheat", "boost", "lap"]
        if not any(k in q for k in keywords):
            # Not obviously telemetry‑related – let the normal knowledge path handle it
            return None

        try:
            report: SessionAnalysisReport = self.session_analyzer.analyze_latest_session()
        except Exception as e:
            LOGGER.warning("Session analysis failed: %s", e)
            return None

        if report.sample_count == 0:
            return (
                "I looked for recent session data but couldn't find any completed logs. "
                "Run a session with logging enabled, then ask me again about AFR, temps, or boost."
            )

        # Build a concise, human‑readable summary from anomalies
        lines: List[str] = []
        lines.append("Here's what I see from your most recent logged session:")
        if report.duration_s:
            lines.append(f"- Duration: ~{report.duration_s:.0f} seconds with {report.sample_count} samples.")
        else:
            lines.append(f"- Samples: {report.sample_count} (no explicit timestamp column found).")

        if not report.anomalies:
            lines.append("- I did not detect any obvious AFR, temperature, or boost issues in the summary.")
        else:
            critical = [a for a in report.anomalies if a.severity == "critical"]
            warnings = [a for a in report.anomalies if a.severity == "warning"]
            info = [a for a in report.anomalies if a.severity not in {"critical", "warning"}]

            if critical:
                lines.append("\n🚨 **Critical findings:**")
                for a in critical:
                    lines.append(f"- {a.message}")
            if warnings:
                lines.append("\n⚠️ **Warnings:**")
                for a in warnings:
                    lines.append(f"- {a.message}")
            if info:
                lines.append("\nℹ️ **Additional notes:**")
                for a in info:
                    lines.append(f"- {a.message}")

        lines.append(
            "\nYou can ask follow‑up questions like:\n"
            "- \"Where did AFR go lean in that session?\"\n"
            "- \"Did coolant get too hot?\"\n"
            "- \"Was boost higher than usual?\""
        )

        return "\n".join(lines)
    
    def _find_relevant_knowledge(self, question: str) -> List[KnowledgeEntry]:
        """Find relevant knowledge base entries."""
        question_lower = question.lower()
        scored_entries = []
        
        for entry in self.knowledge_base:
            score = 0
            
            # Check keyword matches
            for keyword in entry.keywords:
                if keyword in question_lower:
                    score += 2
            
            # Check topic match
            if entry.topic.lower() in question_lower:
                score += 3
            
            # Check content match
            content_words = set(entry.content.lower().split())
            question_words = set(question_lower.split())
            common_words = content_words.intersection(question_words)
            score += len(common_words) * 0.5
            
            if score > 0:
                scored_entries.append((score, entry))
        
        # Sort by score and return top matches
        scored_entries.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored_entries[:3]]
    
    def _generate_rule_based_response(self, question: str, knowledge: List[KnowledgeEntry], context: Optional[Dict[str, any]]) -> str:
        """Generate response using rule-based system."""
        question_lower = question.lower()
        
        # Greeting
        if any(word in question_lower for word in ["hello", "hi", "hey", "greetings"]):
            return "Hello! I'm Q, your TelemetryIQ AI advisor. How can I help you today? I can answer questions about features, configuration, troubleshooting, and provide tips."
        
        # Help request
        if any(word in question_lower for word in ["help", "what can you do", "capabilities"]):
            return """I'm Q, your TelemetryIQ AI advisor. I can help you with:

• Software features and how to use them
• Configuration and setup
• Troubleshooting issues
• Tips and best practices
• Keyboard shortcuts
• Hardware setup

Just ask me anything about the software!"""
        
        # If we have relevant knowledge, use it
        if knowledge:
            response = "Here's what I found:\n\n"
            for entry in knowledge:
                response += f"{entry.content}\n\n"
            return response.strip()
        
        # Default response
        return """I'm Q, your TelemetryIQ AI advisor. I can help you with software features, configuration, troubleshooting, and tips.

Try asking about:
• ECU tuning features
• How to configure backups
• Hardware setup
• Keyboard shortcuts
• Troubleshooting issues
• Tips and best practices

What would you like to know?"""
    
    def _generate_llm_response(self, question: str, knowledge: List[KnowledgeEntry], context: Optional[Dict[str, any]]) -> str:
        """Generate response using LLM (if available)."""
        if not OPENAI_AVAILABLE:
            return self._generate_rule_based_response(question, knowledge, context)
        
        try:
            # Build context from knowledge
            knowledge_context = "\n\n".join([entry.content for entry in knowledge])
            
            # Build system prompt
            system_prompt = """You are Q, the AI advisor for TelemetryIQ racing tuner software. 
You help users with software features, configuration, troubleshooting, and tips.
Be concise, helpful, and professional. Use the provided knowledge base to answer questions accurately."""
            
            # Build conversation context
            messages = [
                {"role": "system", "content": system_prompt},
            ]
            
            # Add knowledge context
            if knowledge_context:
                messages.append({
                    "role": "system",
                    "content": f"Relevant information:\n{knowledge_context}"
                })
            
            # Add conversation history (last 5 messages)
            for msg in self.conversation_history[-5:]:
                messages.append({"role": msg.role, "content": msg.content})
            
            # Add current question
            messages.append({"role": "user", "content": question})
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.7,
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            LOGGER.error("LLM response generation failed: %s", e)
            return self._generate_rule_based_response(question, knowledge, context)
    
    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []
    
    def get_suggestions(self, partial_question: str) -> List[str]:
        """Get suggested questions based on partial input."""
        suggestions = []
        partial_lower = partial_question.lower()
        
        common_questions = [
            "How do I configure ECU tuning?",
            "What are the keyboard shortcuts?",
            "How do I set up backups?",
            "How do I connect hardware?",
            "How do I use USB cameras?",
            "What sensors are supported?",
            "How do I troubleshoot connection issues?",
            "What are the best practices for tuning?",
            "How do I use launch control?",
            "How do I configure boost control?",
        ]
        
        for q in common_questions:
            if partial_lower in q.lower() or not partial_question:
                suggestions.append(q)
        
        return suggestions[:5]

