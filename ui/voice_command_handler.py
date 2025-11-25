"""
Voice Command Handler
Handles voice input for AI advisor and commands.
"""

from __future__ import annotations

import logging
from typing import Optional, Callable, List

from PySide6.QtCore import QObject, Signal, QThread

LOGGER = logging.getLogger(__name__)

# Try to import speech recognition libraries
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    sr = None  # type: ignore


class VoiceCommandHandler(QObject):
    """Handles voice commands for the application."""
    
    command_received = Signal(str)  # Emitted when a command is recognized
    error_occurred = Signal(str)  # Emitted on error
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.recognizer = None
        self.is_listening = False
        self.callbacks: List[Callable[[str], None]] = []
        self._active_threads: List[QThread] = []  # Track active threads for cleanup
        
        if SPEECH_RECOGNITION_AVAILABLE:
            try:
                self.recognizer = sr.Recognizer()
                self.recognizer.energy_threshold = 4000
                self.recognizer.dynamic_energy_threshold = True
            except Exception as e:
                LOGGER.warning("Failed to initialize speech recognition: %s", e)
                self.recognizer = None
    
    def is_available(self) -> bool:
        """Check if voice recognition is available."""
        return self.recognizer is not None
    
    def start_listening(self, callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Start listening for voice commands.
        
        Args:
            callback: Optional callback function for recognized text
            
        Returns:
            True if listening started successfully
        """
        if not self.is_available():
            self.error_occurred.emit("Speech recognition not available")
            return False
        
        if self.is_listening:
            return True
        
        if callback:
            self.callbacks.append(callback)
        
        self.is_listening = True
        
        # Start listening in a separate thread to avoid blocking
        thread = QThread()
        worker = VoiceListenerWorker(self.recognizer)
        worker.command_received.connect(self._on_command_received)
        worker.error_occurred.connect(self._on_error)
        worker.moveToThread(thread)
        thread.started.connect(worker.listen)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self._active_threads.remove(thread) if thread in self._active_threads else None)
        self._active_threads.append(thread)
        thread.start()
        
        return True
    
    def stop_listening(self) -> None:
        """Stop listening for voice commands."""
        self.is_listening = False
        self.callbacks.clear()
    
    def cleanup(self) -> None:
        """Clean up all threads and resources."""
        self.stop_listening()
        # Wait for all threads to finish (with timeout)
        import time
        for thread in self._active_threads[:]:  # Copy list to avoid modification during iteration
            if thread.isRunning():
                thread.quit()
                if not thread.wait(2000):  # Wait up to 2 seconds
                    LOGGER.warning("Thread did not finish in time, terminating")
                    thread.terminate()
                    thread.wait(1000)  # Wait for termination
        self._active_threads.clear()
    
    def _on_command_received(self, text: str) -> None:
        """Handle recognized command."""
        self.command_received.emit(text)
        for callback in self.callbacks:
            try:
                callback(text)
            except Exception as e:
                LOGGER.error("Error in voice command callback: %s", e)
        self.is_listening = False
    
    def _on_error(self, error: str) -> None:
        """Handle error."""
        self.error_occurred.emit(error)
        self.is_listening = False


class VoiceListenerWorker(QObject):
    """Worker thread for listening to voice input."""
    
    command_received = Signal(str)
    error_occurred = Signal(str)
    finished = Signal()
    
    def __init__(self, recognizer, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.recognizer = recognizer
    
    def listen(self) -> None:
        """
        Listen for voice input.
        
        Note: This sends audio data to Google's speech recognition service.
        Users should be aware of privacy implications.
        """
        try:
            with sr.Microphone() as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Listen for audio
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            # Recognize speech
            try:
                # SECURITY/PRIVACY: This sends audio to Google's servers
                # Consider adding user consent mechanism and privacy disclaimer
                text = self.recognizer.recognize_google(audio)
                
                # Sanitize and validate recognized text
                if not isinstance(text, str):
                    self.error_occurred.emit("Invalid recognition result")
                    return
                
                # Basic sanitization - remove potentially dangerous characters
                text = text.strip()
                if not text:
                    self.error_occurred.emit("Empty command received")
                    return
                
                # Limit length to prevent abuse
                if len(text) > 500:
                    text = text[:500]
                    LOGGER.warning("Voice command truncated to 500 characters")
                
                self.command_received.emit(text)
            except sr.UnknownValueError:
                self.error_occurred.emit("Could not understand audio")
            except sr.RequestError as e:
                self.error_occurred.emit(f"Speech recognition error: {e}")
        except OSError as e:
            # Microphone not available
            self.error_occurred.emit(f"Microphone error: {e}")
        except Exception as e:
            LOGGER.error("Unexpected error in voice recognition: %s", e, exc_info=True)
            self.error_occurred.emit(f"Error listening: {e}")
        finally:
            self.finished.emit()

