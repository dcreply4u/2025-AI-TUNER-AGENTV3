"""
Data Exporter Service

Exports telemetry, video, GPS, and diagnostic data in various formats:
- CSV, JSON, Excel, Parquet
- Video formats (MP4, AVI)
- GPS formats (GPX, KML)
"""

from __future__ import annotations

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import openpyxl
except ImportError:
    openpyxl = None

LOGGER = logging.getLogger(__name__)


class DataExporter:
    """Exports data in various formats."""

    SUPPORTED_FORMATS = {
        "telemetry": ["csv", "json", "excel", "parquet"],
        "video": ["mp4", "avi"],
        "gps": ["gpx", "kml", "csv", "json"],
        "diagnostics": ["csv", "json", "excel"],
    }

    def __init__(self, output_dir: Union[str, Path] = "exports") -> None:
        """
        Initialize data exporter.

        Args:
            output_dir: Base directory for exports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_telemetry(
        self,
        data: List[Dict[str, Any]],
        format: str = "csv",
        filename: Optional[str] = None,
        include_metadata: bool = True,
    ) -> Path:
        """
        Export telemetry data.

        Args:
            data: List of telemetry records
            format: Export format (csv, json, excel, parquet)
            filename: Output filename (auto-generated if None)
            include_metadata: Include metadata header

        Returns:
            Path to exported file
        """
        if not data:
            raise ValueError("No data to export")

        format = format.lower()
        if format not in self.SUPPORTED_FORMATS["telemetry"]:
            raise ValueError(f"Unsupported format: {format}. Supported: {self.SUPPORTED_FORMATS['telemetry']}")

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"telemetry_{timestamp}.{format}"

        output_path = self.output_dir / filename

        if format == "csv":
            return self._export_csv(data, output_path, include_metadata)
        elif format == "json":
            return self._export_json(data, output_path, include_metadata)
        elif format == "excel":
            return self._export_excel(data, output_path, include_metadata)
        elif format == "parquet":
            return self._export_parquet(data, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def export_gps(
        self,
        gps_data: List[Dict[str, Any]],
        format: str = "gpx",
        filename: Optional[str] = None,
        track_name: str = "GPS Track",
    ) -> Path:
        """
        Export GPS data.

        Args:
            gps_data: List of GPS records with lat, lon, timestamp, etc.
            format: Export format (gpx, kml, csv, json)
            filename: Output filename (auto-generated if None)
            track_name: Name for track/route

        Returns:
            Path to exported file
        """
        if not gps_data:
            raise ValueError("No GPS data to export")

        format = format.lower()
        if format not in self.SUPPORTED_FORMATS["gps"]:
            raise ValueError(f"Unsupported format: {format}. Supported: {self.SUPPORTED_FORMATS['gps']}")

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gps_{timestamp}.{format}"

        output_path = self.output_dir / filename

        if format == "gpx":
            return self._export_gpx(gps_data, output_path, track_name)
        elif format == "kml":
            return self._export_kml(gps_data, output_path, track_name)
        elif format == "csv":
            return self._export_csv(gps_data, output_path)
        elif format == "json":
            return self._export_json(gps_data, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def export_diagnostics(
        self,
        diagnostics: Dict[str, Any],
        format: str = "json",
        filename: Optional[str] = None,
    ) -> Path:
        """
        Export diagnostic data.

        Args:
            diagnostics: Diagnostic data dictionary
            format: Export format (csv, json, excel)
            filename: Output filename (auto-generated if None)

        Returns:
            Path to exported file
        """
        if not diagnostics:
            raise ValueError("No diagnostic data to export")

        format = format.lower()
        if format not in self.SUPPORTED_FORMATS["diagnostics"]:
            raise ValueError(f"Unsupported format: {format}. Supported: {self.SUPPORTED_FORMATS['diagnostics']}")

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"diagnostics_{timestamp}.{format}"

        output_path = self.output_dir / filename

        # Convert dict to list of records for CSV/Excel
        if format in ["csv", "excel"]:
            data = [{"metric": k, "value": v} for k, v in diagnostics.items()]
            if format == "csv":
                return self._export_csv(data, output_path)
            else:
                return self._export_excel(data, output_path)
        else:
            return self._export_json(diagnostics, output_path)

    def export_session(
        self,
        session_data: Dict[str, Any],
        formats: List[str] = ["csv", "json"],
        base_filename: Optional[str] = None,
    ) -> Dict[str, Path]:
        """
        Export complete session data in multiple formats.

        Args:
            session_data: Dictionary with keys: telemetry, gps, diagnostics, video_paths
            formats: List of formats to export
            base_filename: Base filename (auto-generated if None)

        Returns:
            Dictionary mapping format to exported file path
        """
        if base_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"session_{timestamp}"

        exported = {}

        # Export telemetry
        if "telemetry" in session_data:
            for fmt in formats:
                if fmt in self.SUPPORTED_FORMATS["telemetry"]:
                    try:
                        path = self.export_telemetry(
                            session_data["telemetry"],
                            format=fmt,
                            filename=f"{base_filename}_telemetry.{fmt}",
                        )
                        exported[f"telemetry_{fmt}"] = path
                    except Exception as e:
                        LOGGER.error("Error exporting telemetry as %s: %s", fmt, e)

        # Export GPS
        if "gps" in session_data:
            for fmt in formats:
                if fmt in self.SUPPORTED_FORMATS["gps"]:
                    try:
                        path = self.export_gps(
                            session_data["gps"],
                            format=fmt,
                            filename=f"{base_filename}_gps.{fmt}",
                        )
                        exported[f"gps_{fmt}"] = path
                    except Exception as e:
                        LOGGER.error("Error exporting GPS as %s: %s", fmt, e)

        # Export diagnostics
        if "diagnostics" in session_data:
            for fmt in formats:
                if fmt in self.SUPPORTED_FORMATS["diagnostics"]:
                    try:
                        path = self.export_diagnostics(
                            session_data["diagnostics"],
                            format=fmt,
                            filename=f"{base_filename}_diagnostics.{fmt}",
                        )
                        exported[f"diagnostics_{fmt}"] = path
                    except Exception as e:
                        LOGGER.error("Error exporting diagnostics as %s: %s", fmt, e)

        return exported

    # Internal export methods

    def _export_csv(self, data: List[Dict[str, Any]], output_path: Path, include_metadata: bool = False) -> Path:
        """Export data as CSV."""
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            if not data:
                return output_path

            fieldnames = list(data[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            if include_metadata:
                # Add metadata as comments (CSV doesn't support comments, so we'll skip this)
                pass

            writer.writerows(data)

        return output_path

    def _export_json(self, data: Union[List[Dict[str, Any]], Dict[str, Any]], output_path: Path, include_metadata: bool = False) -> Path:
        """Export data as JSON."""
        export_data = data
        if include_metadata:
            export_data = {
                "metadata": {
                    "export_date": datetime.now().isoformat(),
                    "record_count": len(data) if isinstance(data, list) else 1,
                },
                "data": data,
            }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, default=str)

        return output_path

    def _export_excel(self, data: List[Dict[str, Any]], output_path: Path, include_metadata: bool = False) -> Path:
        """Export data as Excel."""
        if pd is None:
            raise RuntimeError("pandas required for Excel export. Install with: pip install pandas openpyxl")

        df = pd.DataFrame(data)

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            if include_metadata:
                # Write metadata to first sheet
                metadata_df = pd.DataFrame(
                    [
                        {"Key": "Export Date", "Value": datetime.now().isoformat()},
                        {"Key": "Record Count", "Value": len(data)},
                    ]
                )
                metadata_df.to_excel(writer, sheet_name="Metadata", index=False)

            # Write data to main sheet
            df.to_excel(writer, sheet_name="Data", index=False)

        return output_path

    def _export_parquet(self, data: List[Dict[str, Any]], output_path: Path) -> Path:
        """Export data as Parquet."""
        if pd is None:
            raise RuntimeError("pandas required for Parquet export. Install with: pip install pandas pyarrow")

        df = pd.DataFrame(data)
        df.to_parquet(output_path, index=False)
        return output_path

    def _export_gpx(self, gps_data: List[Dict[str, Any]], output_path: Path, track_name: str = "GPS Track") -> Path:
        """Export GPS data as GPX."""
        from xml.etree.ElementTree import Element, SubElement, tostring
        from xml.dom import minidom

        gpx = Element("gpx", version="1.1", creator="AI Tuner Agent")
        trk = SubElement(gpx, "trk")
        SubElement(trk, "name").text = track_name
        trkseg = SubElement(trk, "trkseg")

        for point in gps_data:
            trkpt = SubElement(trkseg, "trkpt", lat=str(point.get("lat", point.get("latitude", 0))), lon=str(point.get("lon", point.get("longitude", 0))))

            if "timestamp" in point or "time" in point:
                time_str = point.get("timestamp") or point.get("time")
                if isinstance(time_str, (int, float)):
                    time_str = datetime.fromtimestamp(time_str).isoformat() + "Z"
                SubElement(trkpt, "time").text = time_str

            if "elevation" in point or "alt" in point:
                ele = point.get("elevation") or point.get("alt")
                SubElement(trkpt, "ele").text = str(ele)

            if "speed" in point or "speed_mps" in point:
                speed = point.get("speed") or point.get("speed_mps")
                ext = SubElement(trkpt, "extensions")
                SubElement(ext, "speed").text = str(speed)

        # Pretty print XML
        xml_str = minidom.parseString(tostring(gpx)).toprettyxml(indent="  ")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        return output_path

    def _export_kml(self, gps_data: List[Dict[str, Any]], output_path: Path, track_name: str = "GPS Track") -> Path:
        """Export GPS data as KML."""
        from xml.etree.ElementTree import Element, SubElement, tostring
        from xml.dom import minidom

        kml = Element("kml", xmlns="http://www.opengis.net/kml/2.2")
        doc = SubElement(kml, "Document")
        SubElement(doc, "name").text = track_name

        # Create placemark with line string
        placemark = SubElement(doc, "Placemark")
        SubElement(placemark, "name").text = track_name
        linestring = SubElement(placemark, "LineString")
        SubElement(linestring, "tessellate").text = "1"
        coordinates = SubElement(linestring, "coordinates")

        coords_text = []
        for point in gps_data:
            lon = point.get("lon", point.get("longitude", 0))
            lat = point.get("lat", point.get("latitude", 0))
            alt = point.get("elevation", point.get("alt", 0))
            coords_text.append(f"{lon},{lat},{alt}")

        coordinates.text = " ".join(coords_text)

        # Pretty print XML
        xml_str = minidom.parseString(tostring(kml)).toprettyxml(indent="  ")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(xml_str)

        return output_path


__all__ = ["DataExporter"]

