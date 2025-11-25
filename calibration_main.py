"""Main entry point for calibration editing workflow."""

from __future__ import annotations

import logging

from ai_engine.tuner import AITuningEngine
from calibration.editor import CalibrationEditor
from can_interface.ecu_flash import ECUFlashManager

LOGGER = logging.getLogger(__name__)


def main() -> None:
    """Main calibration editing workflow."""
    logging.basicConfig(level=logging.INFO)

    ecu = ECUFlashManager()
    ai_engine = AITuningEngine()

    # 1. Read ECU binary
    LOGGER.info("Reading ECU memory...")
    raw_data = ecu.read_ecu(0x000000, 0x10000)

    # 2. AI tuning
    LOGGER.info("Running AI tuning analysis...")
    telemetry_sample = [[3000, 0.85, 14.7]]  # rpm, load, afr
    adjustments = ai_engine.suggest_adjustments(telemetry_sample)

    # 3. Apply calibration edits
    LOGGER.info("Applying calibration modifications...")
    editor = CalibrationEditor(raw_data)
    adjustment_bytes = [int(max(0, min(255, a))) for a in adjustments[0]]
    editor.modify_map(0x2000, adjustment_bytes)
    editor.save("modified_calibration.bin")

    # 4. Flash new calibration (optional - commented for safety)
    # LOGGER.info("Flashing calibration to ECU...")
    # with open("modified_calibration.bin", "rb") as f:
    #     ecu.write_ecu(0x000000, f.read())

    LOGGER.info("Calibration workflow complete")


if __name__ == "__main__":
    main()

