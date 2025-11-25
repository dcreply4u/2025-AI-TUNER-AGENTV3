from __future__ import annotations

import logging
from typing import Any, Callable, Optional

try:
    from interfaces.voice_interface import VoiceInterface
except ImportError:
    VoiceInterface = None  # type: ignore

LOGGER = logging.getLogger(__name__)


def _default_command_handler(command: str, ui, start_stream: Callable[[], None]) -> None:
    command = command.lower()
    ai_panel = getattr(ui, "ai_panel", None)
    status_bar = getattr(ui, "status_bar", None)
    controller = getattr(ui, "data_stream_controller", None)
    voice_output = getattr(ui, "voice_output", None)
    agent = getattr(ui, "conversational_agent", None)
    connectivity_manager = getattr(ui, "connectivity_manager", None)
    camera_manager = getattr(ui, "camera_manager", None)

    def _insight(msg: str, level: str | None = None) -> None:
        if ai_panel:
            ai_panel.update_insight(msg, level=level)
        if voice_output and msg:
            voice_output.speak(msg)

    def _set_source(source_label: str) -> None:
        stream_settings = getattr(ui, "stream_settings", None)
        if isinstance(stream_settings, dict):
            stream_settings["source"] = source_label
            stream_settings["mode"] = "live"
        _insight(f"Voice: Switching to {source_label}.")
        if controller:
            controller.stop()
        start_stream()

    if "start" in command:
        _insight("Voice: Starting session.")
        stream_settings = getattr(ui, "stream_settings", None)
        if isinstance(stream_settings, dict):
            stream_settings["mode"] = "live"
        start_stream()
    elif "stop" in command:
        _insight("Voice: Stopping session.", level="warning")
        if controller:
            controller.stop()
        if status_bar:
            status_bar.update_status("Stopped via voice")
    elif "race" in command:
        _set_source("RaceCapture")
    elif "obd" in command or "o.b.d" in command:
        _set_source("OBD-II")
    elif "auto" in command:
        _set_source("Auto")
    elif "fault" in command or "code" in command:
        fault_panel = getattr(ui, "fault_panel", None)
        if fault_panel:
            fault_panel.read_codes()
            _insight("Voice: Fetching diagnostic trouble codes.")
        else:
            _insight("Voice: Fault panel unavailable.", level="warning")
    elif "replay" in command or "simulate" in command:
        stream_settings = getattr(ui, "stream_settings", None)
        replay_file = stream_settings.get("replay_file") if isinstance(stream_settings, dict) else None
        if stream_settings and replay_file:
            stream_settings["mode"] = "replay"
            _insight("Voice: Replaying last selected log.")
            if controller:
                controller.stop()
            start_stream()
        else:
            _insight("Voice: No replay log selected yet.", level="warning")
    elif "network" in command or "link" in command or "connectivity" in command:
        if connectivity_manager:
            summary = connectivity_manager.status.summary()
            _insight(f"Voice: Connectivity {summary}.")
        else:
            _insight("Voice: Connectivity monitor unavailable.", level="warning")
    elif "camera" in command or "record" in command or "video" in command:
        if not camera_manager:
            _insight("Voice: Camera manager unavailable.", level="warning")
        elif "start" in command or "begin" in command or "on" in command:
            if controller and hasattr(controller, "_session_id"):
                session_id = controller._session_id or "manual"
                camera_manager.start_recording(session_id)
                _insight("Voice: Camera recording started.")
            else:
                _insight("Voice: Start a data session first to begin recording.", level="warning")
        elif "stop" in command or "end" in command or "off" in command:
            camera_manager.stop_recording()
            _insight("Voice: Camera recording stopped.")
        elif "status" in command or "check" in command:
            status = camera_manager.get_status()
            camera_count = len(status.get("cameras", {}))
            recording = status.get("recording", False)
            if recording:
                active = len(status.get("active_recordings", []))
                _insight(f"Voice: {camera_count} cameras connected, {active} recording.")
            else:
                _insight(f"Voice: {camera_count} cameras connected, not recording.")
        elif "enable" in command or "turn on" in command:
            # Try to enable a specific camera if mentioned
            if "front" in command:
                _insight("Voice: Use camera configuration dialog to enable cameras.")
            elif "rear" in command:
                _insight("Voice: Use camera configuration dialog to enable cameras.")
            else:
                _insight("Voice: Use camera configuration dialog to enable cameras.")
        elif "disable" in command or "turn off" in command:
            _insight("Voice: Use camera configuration dialog to disable cameras.")
        else:
            _insight("Voice: Camera commands: start recording, stop recording, camera status.")
    else:
        if agent:
            reply = agent.answer(command)
            if reply:
                _insight(f"Voice: {reply}")
            else:
                _insight("Voice: I'm not sure how to answer that.")
        else:
            _insight(f"Voice: Unrecognized command '{command}'.")


def start_voice_listener(ui, start_stream_callback: Optional[Callable[[], None]] = None) -> Optional[Any]:
    """
    Launch the speech recognizer in a background thread and dispatch commands.

    Args:
        ui: Main window reference, expected to expose ai_panel/fault_panel/status_bar.
        start_stream_callback: Callable used to (re)start the data stream.
    """
    if VoiceInterface is None:
        LOGGER.warning("VoiceInterface not available (speech_recognition not installed)")
        ai_panel = getattr(ui, "ai_panel", None)
        if ai_panel:
            ai_panel.update_insight("Voice control unavailable - install SpeechRecognition and PyAudio", level="warning")
        return None

    if start_stream_callback is None:
        from .data_stream_controller import start_data_stream

        start_stream_callback = lambda: start_data_stream(ui)

    handler = getattr(ui, "voice_command_handler", None) or _default_command_handler
    try:
        interface = VoiceInterface(lambda cmd: handler(cmd, ui, start_stream_callback))
    except Exception as exc:  # pragma: no cover - microphone/runtime issues
        LOGGER.error("Voice control unavailable: %s", exc)
        ai_panel = getattr(ui, "ai_panel", None)
        if ai_panel:
            ai_panel.update_insight("Voice control unavailable on this system.", level="warning")
        return None
    interface.start_async()
    setattr(ui, "voice_interface", interface)
    return interface


__all__ = ["start_voice_listener"]

