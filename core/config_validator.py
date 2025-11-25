"""
Configuration Validator

Validates configuration settings and provides helpful error messages.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Configuration validation error."""

    pass


class ConfigValidator:
    """Validates configuration settings."""

    @staticmethod
    def validate_all() -> Dict[str, Any]:
        """
        Validate all configuration settings.

        Returns:
            Dictionary with validation results
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "checks": {},
        }

        # Check CAN configuration
        can_result = ConfigValidator.validate_can()
        results["checks"]["can"] = can_result
        if not can_result["valid"]:
            results["valid"] = False
            results["errors"].extend(can_result["errors"])

        # Check paths
        path_result = ConfigValidator.validate_paths()
        results["checks"]["paths"] = path_result
        if not path_result["valid"]:
            results["valid"] = False
            results["errors"].extend(path_result["errors"])

        # Check AWS IoT (optional)
        aws_result = ConfigValidator.validate_aws_iot()
        results["checks"]["aws_iot"] = aws_result
        if not aws_result["valid"]:
            results["warnings"].extend(aws_result["warnings"])

        # Check hardware
        hw_result = ConfigValidator.validate_hardware()
        results["checks"]["hardware"] = hw_result
        if not hw_result["valid"]:
            results["warnings"].extend(hw_result["warnings"])

        return results

    @staticmethod
    def validate_can() -> Dict[str, Any]:
        """Validate CAN bus configuration."""
        result = {"valid": True, "errors": [], "warnings": []}

        try:
            from config import CAN_CHANNEL, CAN_BITRATE, CAN_BUSTYPE

            # Check CAN channel
            if not CAN_CHANNEL:
                result["errors"].append("CAN_CHANNEL is not set")
                result["valid"] = False

            # Check if CAN interface exists
            can_path = Path(f"/sys/class/net/{CAN_CHANNEL}")
            if not can_path.exists():
                result["warnings"].append(f"CAN interface {CAN_CHANNEL} not found. May need to be configured.")
            else:
                # Check if interface is up
                operstate_file = can_path / "operstate"
                if operstate_file.exists():
                    state = operstate_file.read_text().strip()
                    if state != "UP":
                        result["warnings"].append(f"CAN interface {CAN_CHANNEL} is {state}, not UP")

            # Check bitrate
            if CAN_BITRATE not in [125000, 250000, 500000, 1000000]:
                result["warnings"].append(f"Unusual CAN bitrate: {CAN_BITRATE}")

            # Check bustype
            if CAN_BUSTYPE not in ["socketcan", "serial", "usb"]:
                result["warnings"].append(f"Unusual CAN bustype: {CAN_BUSTYPE}")

        except ImportError as e:
            result["errors"].append(f"Failed to import config: {e}")
            result["valid"] = False
        except Exception as e:
            result["errors"].append(f"Error validating CAN: {e}")
            result["valid"] = False

        return result

    @staticmethod
    def validate_paths() -> Dict[str, Any]:
        """Validate file paths and directories."""
        result = {"valid": True, "errors": [], "warnings": []}

        try:
            from config import LOG_FILE, MODEL_PATH, DBC_FILE

            # Check log directory
            if LOG_FILE:
                log_dir = Path(LOG_FILE).parent
                if not log_dir.exists():
                    try:
                        log_dir.mkdir(parents=True, exist_ok=True)
                        result["warnings"].append(f"Created log directory: {log_dir}")
                    except Exception as e:
                        result["errors"].append(f"Cannot create log directory {log_dir}: {e}")
                        result["valid"] = False

            # Check model path
            if MODEL_PATH:
                model_path = Path(MODEL_PATH)
                if not model_path.exists():
                    result["warnings"].append(f"Model path does not exist: {MODEL_PATH}")

            # Check DBC file (optional)
            if DBC_FILE:
                dbc_path = Path(DBC_FILE)
                if not dbc_path.exists():
                    result["warnings"].append(f"DBC file not found: {DBC_FILE}")

        except ImportError as e:
            result["errors"].append(f"Failed to import config: {e}")
            result["valid"] = False
        except Exception as e:
            result["errors"].append(f"Error validating paths: {e}")
            result["valid"] = False

        return result

    @staticmethod
    def validate_aws_iot() -> Dict[str, Any]:
        """Validate AWS IoT configuration (optional)."""
        result = {"valid": True, "errors": [], "warnings": []}

        try:
            from config import AWS_ENDPOINT, CA_CERT, DEVICE_CERT, PRIVATE_KEY

            # Check if AWS is configured
            if AWS_ENDPOINT == "your-iot-endpoint.amazonaws.com":
                result["warnings"].append("AWS IoT endpoint not configured (using default)")

            # Check certificates
            certs = {
                "CA": CA_CERT,
                "Device": DEVICE_CERT,
                "Private Key": PRIVATE_KEY,
            }

            for name, cert_path in certs.items():
                if cert_path and not Path(cert_path).exists():
                    result["warnings"].append(f"AWS IoT {name} certificate not found: {cert_path}")

        except ImportError:
            result["warnings"].append("AWS IoT configuration not available")
        except Exception as e:
            result["warnings"].append(f"Error validating AWS IoT: {e}")

        return result

    @staticmethod
    def validate_hardware() -> Dict[str, Any]:
        """Validate hardware detection."""
        result = {"valid": True, "errors": [], "warnings": []}

        try:
            from core import get_hardware_config

            config = get_hardware_config()

            if config.platform_name == "Unknown":
                result["warnings"].append("Hardware platform not detected")

            if not config.can_channels:
                result["warnings"].append("No CAN channels detected")

            # Check if CAN interfaces actually exist
            for channel in config.can_channels:
                can_path = Path(f"/sys/class/net/{channel}")
                if not can_path.exists():
                    result["warnings"].append(f"CAN channel {channel} not found in system")

        except Exception as e:
            result["warnings"].append(f"Error validating hardware: {e}")

        return result

    @staticmethod
    def print_validation_report(results: Dict[str, Any]) -> None:
        """Print validation report to console."""
        print("=" * 60)
        print("Configuration Validation Report")
        print("=" * 60)

        if results["valid"]:
            print("✓ Configuration is valid")
        else:
            print("✗ Configuration has errors")

        if results["errors"]:
            print("\nErrors:")
            for error in results["errors"]:
                print(f"  ✗ {error}")

        if results["warnings"]:
            print("\nWarnings:")
            for warning in results["warnings"]:
                print(f"  ⚠ {warning}")

        print("\nDetailed Checks:")
        for check_name, check_result in results["checks"].items():
            status = "✓" if check_result["valid"] else "✗"
            print(f"  {status} {check_name}")
            if check_result.get("errors"):
                for error in check_result["errors"]:
                    print(f"      - {error}")
            if check_result.get("warnings"):
                for warning in check_result["warnings"]:
                    print(f"      - {warning}")

        print("=" * 60)


__all__ = ["ConfigValidator", "ConfigValidationError"]

