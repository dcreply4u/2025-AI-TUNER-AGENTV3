"""
Voice Interaction (Hands-Free)
Enables voice commands and verbal feedback for hands-free operation.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from typing import Callable, Optional

LOGGER = logging.getLogger(__name__)

# Try to import speech libraries
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    sr = None  # type: ignore

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    pyttsx3 = None  # type: ignore


class VoiceInteraction:
    """
    Voice interaction system for hands-free operation.
    
    Features:
    - Wake word detection
    - Voice command recognition
    - Text-to-speech responses
    - Continuous listening mode
    """
    
    def __init__(
        self,
        wake_words: list = None,
        language: str = "en-US",
        response_callback: Optional[Callable[[str], str]] = None
    ):
        """
        Initialize voice interaction.
        
        Args:
            wake_words: List of wake words (e.g., ["PitGirl", "Q", "assistant"])
            language: Language for speech recognition
            response_callback: Function to process commands and return responses
        """
        self.wake_words = wake_words or ["PitGirl", "Q", "assistant"]
        self.language = language
        self.response_callback = response_callback
        
        self.is_listening = False
        self.is_speaking = False
        self.command_queue = queue.Queue()
        
        # Initialize speech recognition
        self.recognizer = None
        self.microphone = None
        if SPEECH_RECOGNITION_AVAILABLE:
            try:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
                # Adjust for ambient noise
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
            except Exception as e:
                LOGGER.warning("Failed to initialize speech recognition: %s", e)
        
        # Initialize text-to-speech
        self.tts_engine = None
        if TTS_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                # Configure voice properties
                voices = self.tts_engine.getProperty('voices')
                if voices:
                    self.tts_engine.setProperty('voice', voices[0].id)
                self.tts_engine.setProperty('rate', 150)  # Speech rate
                self.tts_engine.setProperty('volume', 0.8)  # Volume
            except Exception as e:
                LOGGER.warning("Failed to initialize TTS: %s", e)
    
    def start_listening(self) -> None:
        """Start continuous listening for wake words and commands."""
        if not SPEECH_RECOGNITION_AVAILABLE or not self.recognizer or not self.microphone:
            LOGGER.error("Speech recognition not available")
            return
        
        self.is_listening = True
        listening_thread = threading.Thread(target=self._listen_loop, daemon=True)
        listening_thread.start()
        LOGGER.info("Voice interaction started")
    
    def stop_listening(self) -> None:
        """Stop listening."""
        self.is_listening = False
    
    def _listen_loop(self) -> None:
        """Main listening loop."""
        wake_word_detected = False
        
        if not self.recognizer or not self.microphone:
            LOGGER.error("Speech recognition not initialized, cannot start listening")
            return
        
        while self.is_listening:
            try:
                with self.microphone as source:
                    # Listen for audio with error handling
                    try:
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                    except Exception as e:
                        LOGGER.debug("Error listening for audio: %s", e)
                        time.sleep(0.5)
                        continue
                
                try:
                    # Recognize speech
                    text = self.recognizer.recognize_google(audio, language=self.language)
                    text_lower = text.lower()
                    
                    # Check for wake word
                    if not wake_word_detected:
                        for wake_word in self.wake_words:
                            if wake_word.lower() in text_lower:
                                wake_word_detected = True
                                self.speak(f"Listening, {wake_word}")
                                LOGGER.info(f"Wake word detected: {wake_word}")
                                break
                    else:
                        # Process command
                        if self.response_callback:
                            response = self.response_callback(text)
                            self.speak(response)
                        wake_word_detected = False
                
                except sr.UnknownValueError:
                    # Could not understand audio
                    if wake_word_detected:
                        self.speak("I didn't catch that. Please repeat.")
                        wake_word_detected = False
                except sr.RequestError as e:
                    LOGGER.error("Speech recognition error: %s", e)
                    wake_word_detected = False
            
            except sr.WaitTimeoutError:
                # Timeout - continue listening
                continue
            except Exception as e:
                LOGGER.error("Error in listen loop: %s", e)
                time.sleep(1)
    
    def speak(self, text: str) -> None:
        """
        Speak text using text-to-speech.
        
        Args:
            text: Text to speak
        """
        if not TTS_AVAILABLE or not self.tts_engine:
            LOGGER.warning("TTS not available, cannot speak: %s", text)
            return
        
        if self.is_speaking:
            # Wait for current speech to finish
            while self.is_speaking:
                time.sleep(0.1)
        
        self.is_speaking = True
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            LOGGER.error("TTS error: %s", e)
        finally:
            self.is_speaking = False
    
    def process_command(self, command: str) -> str:
        """
        Process a voice command.
        
        Args:
            command: Voice command text
            
        Returns:
            Response text
        """
        if self.response_callback:
            return self.response_callback(command)
        return "Command received"


__all__ = ["VoiceInteraction"]

