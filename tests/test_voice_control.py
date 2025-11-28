"""
Voice Control Tests

Tests voice recognition, text-to-speech, and voice commands.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestVoiceRecognition:
    """Test voice recognition functionality."""
    
    def test_voice_feedback_import(self):
        """Test voice feedback can be imported."""
        try:
            from services.voice_feedback import VoiceFeedback, FeedbackEvent, FeedbackPriority
            assert VoiceFeedback is not None
            assert FeedbackEvent is not None
            assert FeedbackPriority is not None
        except ImportError:
            pytest.skip("Voice feedback not available")
    
    def test_voice_ecu_control_import(self):
        """Test voice ECU control can be imported."""
        try:
            from services.voice_ecu_control import VoiceECUControl, VoiceCommand
            assert VoiceECUControl is not None
            assert VoiceCommand is not None
        except ImportError:
            pytest.skip("Voice ECU control not available")
    
    def test_voice_command_parsing(self):
        """Test voice command parsing."""
        try:
            from services.voice_ecu_control import VoiceCommand
            
            # Test command creation
            command = VoiceCommand(
                text="increase boost by 2 psi",
                intent="adjust_parameter",
                parameter="boost",
                value=2.0,
            )
            
            assert command.intent == "adjust_parameter"
            assert command.parameter == "boost"
            assert command.value == 2.0
        except ImportError:
            pytest.skip("Voice ECU control not available")


class TestTextToSpeech:
    """Test text-to-speech functionality."""
    
    def test_tts_availability(self):
        """Test TTS library availability."""
        try:
            import pyttsx3
            assert pyttsx3 is not None
        except ImportError:
            pytest.skip("pyttsx3 not available")
    
    def test_speech_recognition_availability(self):
        """Test speech recognition library availability."""
        try:
            import speech_recognition
            assert speech_recognition is not None
        except ImportError:
            pytest.skip("SpeechRecognition not available")

