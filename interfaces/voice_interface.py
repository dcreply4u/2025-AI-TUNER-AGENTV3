from __future__ import annotations

import threading
from typing import Callable

try:
    import speech_recognition as sr
except ImportError:
    sr = None  # type: ignore


class VoiceInterface:
    """Thin wrapper over SpeechRecognition to issue callbacks on utterances."""

    def __init__(self, command_callback: Callable[[str], None]) -> None:
        if sr is None:
            raise RuntimeError("speech_recognition not installed. Install with: pip install SpeechRecognition PyAudio")
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()
        self.command_callback = command_callback

    def listen(self) -> None:
        with self.mic as source:
            print("Listening for voice command...")
            audio = self.recognizer.listen(source)
        try:
            command = self.recognizer.recognize_google(audio).lower()
            print("Heard:", command)
            self.command_callback(command)
        except sr.UnknownValueError:
            print("VoiceInterface could not understand the audio.")
        except sr.RequestError as exc:
            print(f"VoiceInterface speech recognition error: {exc}")

    def start_async(self) -> threading.Thread:
        thread = threading.Thread(target=self.listen, daemon=True)
        thread.start()
        return thread


__all__ = ["VoiceInterface"]

