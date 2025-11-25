"""
ECU Preset Management

Manages ECU parameter presets for quick configuration changes.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional

LOGGER = logging.getLogger(__name__)


@dataclass
class ECUPreset:
    """ECU parameter preset."""

    name: str
    description: str
    parameters: Dict[str, Any]  # parameter_name -> value
    ecu_type: str
    created_at: float
    tags: List[str] = None  # type: ignore


class ECUPresetManager:
    """Manages ECU parameter presets."""

    def __init__(self, presets_dir: str | Path = "presets/ecu") -> None:
        """
        Initialize preset manager.

        Args:
            presets_dir: Directory for preset files
        """
        self.presets_dir = Path(presets_dir)
        self.presets_dir.mkdir(parents=True, exist_ok=True)
        self.presets: Dict[str, ECUPreset] = {}
        self._load_presets()

    def create_preset(
        self,
        name: str,
        parameters: Dict[str, Any],
        ecu_type: str,
        description: str = "",
        tags: Optional[List[str]] = None,
    ) -> ECUPreset:
        """
        Create a new preset.

        Args:
            name: Preset name
            parameters: Parameter values
            ecu_type: ECU type
            description: Preset description
            tags: Optional tags

        Returns:
            Created preset
        """
        import time

        preset = ECUPreset(
            name=name,
            description=description,
            parameters=parameters,
            ecu_type=ecu_type,
            created_at=time.time(),
            tags=tags or [],
        )

        self.presets[name] = preset
        self._save_preset(preset)

        LOGGER.info("Created preset: %s", name)
        return preset

    def load_preset(self, name: str) -> Optional[ECUPreset]:
        """Load a preset by name."""
        return self.presets.get(name)

    def apply_preset(self, preset_name: str, ecu_control) -> tuple[bool, List[str]]:
        """
        Apply a preset to ECU.

        Args:
            preset_name: Preset name
            ecu_control: ECUControl instance

        Returns:
            Tuple of (success, warnings)
        """
        preset = self.presets.get(preset_name)
        if not preset:
            return False, [f"Preset not found: {preset_name}"]

        warnings = []
        success_count = 0

        # Apply each parameter
        for param_name, value in preset.parameters.items():
            success, param_warnings = ecu_control.set_parameter(param_name, value)
            if success:
                success_count += 1
            warnings.extend(param_warnings)

        return success_count == len(preset.parameters), warnings

    def _save_preset(self, preset: ECUPreset) -> None:
        """Save preset to file."""
        preset_file = self.presets_dir / f"{preset.name}.json"
        with open(preset_file, "w") as f:
            json.dump(asdict(preset), f, indent=2)

    def _load_presets(self) -> None:
        """Load all presets from directory."""
        for preset_file in self.presets_dir.glob("*.json"):
            try:
                with open(preset_file, "r") as f:
                    data = json.load(f)
                    preset = ECUPreset(**data)
                    self.presets[preset.name] = preset
            except Exception as e:
                LOGGER.error("Failed to load preset %s: %s", preset_file, e)

    def list_presets(self, ecu_type: Optional[str] = None, tag: Optional[str] = None) -> List[ECUPreset]:
        """List presets, optionally filtered."""
        presets = list(self.presets.values())

        if ecu_type:
            presets = [p for p in presets if p.ecu_type == ecu_type]

        if tag:
            presets = [p for p in presets if tag in p.tags]

        return presets

    def delete_preset(self, name: str) -> bool:
        """Delete a preset."""
        if name not in self.presets:
            return False

        preset_file = self.presets_dir / f"{name}.json"
        if preset_file.exists():
            preset_file.unlink()

        del self.presets[name]
        LOGGER.info("Deleted preset: %s", name)
        return True


__all__ = ["ECUPreset", "ECUPresetManager"]

