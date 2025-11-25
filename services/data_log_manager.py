"""
Data Log Management

Features:
- Save and organize data logs
- Export to CSV/JSON/Excel
- Import from various formats
- Session management
- Metadata tracking
"""

from __future__ import annotations

import csv
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    LOGGER.warning("pandas not available - Excel export disabled")

LOGGER = logging.getLogger(__name__)


@dataclass
class DataLogMetadata:
    """Data log metadata."""
    name: str
    timestamp: float
    duration: float
    channels: List[str]
    sample_rate: float
    vehicle_info: Optional[Dict[str, Any]] = None
    session_info: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class DataLogManager:
    """Data log management system."""
    
    def __init__(self, log_directory: Optional[Path] = None) -> None:
        """
        Initialize data log manager.
        
        Args:
            log_directory: Directory for storing logs (default: data/logs)
        """
        if log_directory is None:
            log_directory = Path("data") / "logs"
        
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        # Metadata file
        self.metadata_file = self.log_directory / "metadata.json"
        self.metadata: Dict[str, DataLogMetadata] = {}
        self._load_metadata()
    
    def _load_metadata(self) -> None:
        """Load metadata from file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    for name, meta_dict in data.items():
                        self.metadata[name] = DataLogMetadata(**meta_dict)
            except Exception as e:
                LOGGER.error("Failed to load metadata: %s", e)
    
    def _save_metadata(self) -> None:
        """Save metadata to file."""
        try:
            data = {
                name: {
                    'name': meta.name,
                    'timestamp': meta.timestamp,
                    'duration': meta.duration,
                    'channels': meta.channels,
                    'sample_rate': meta.sample_rate,
                    'vehicle_info': meta.vehicle_info,
                    'session_info': meta.session_info,
                    'notes': meta.notes,
                }
                for name, meta in self.metadata.items()
            }
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            LOGGER.error("Failed to save metadata: %s", e)
    
    def save_log(self, data: Dict[str, List[float]], metadata: DataLogMetadata,
                 format: str = "csv") -> Path:
        """
        Save data log.
        
        Args:
            data: Dictionary of {channel_name: [values]}
            metadata: Log metadata
            format: Export format (csv, json, excel)
            
        Returns:
            Path to saved file
        """
        timestamp_str = datetime.fromtimestamp(metadata.timestamp).strftime("%Y%m%d_%H%M%S")
        filename = f"{metadata.name}_{timestamp_str}.{format}"
        filepath = self.log_directory / filename
        
        if format == "csv":
            self._save_csv(data, filepath)
        elif format == "json":
            self._save_json(data, metadata, filepath)
        elif format == "excel" and PANDAS_AVAILABLE:
            self._save_excel(data, filepath)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Save metadata
        self.metadata[metadata.name] = metadata
        self._save_metadata()
        
        LOGGER.info("Saved data log: %s", filepath)
        return filepath
    
    def _save_csv(self, data: Dict[str, List[float]], filepath: Path) -> None:
        """Save data as CSV."""
        # Determine number of rows
        if not data:
            return
        
        num_rows = max(len(values) for values in data.values())
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(data.keys())
            
            # Write data
            for i in range(num_rows):
                row = [data[channel][i] if i < len(data[channel]) else "" for channel in data.keys()]
                writer.writerow(row)
    
    def _save_json(self, data: Dict[str, List[float]], metadata: DataLogMetadata, filepath: Path) -> None:
        """Save data as JSON."""
        json_data = {
            'metadata': {
                'name': metadata.name,
                'timestamp': metadata.timestamp,
                'duration': metadata.duration,
                'channels': metadata.channels,
                'sample_rate': metadata.sample_rate,
                'vehicle_info': metadata.vehicle_info,
                'session_info': metadata.session_info,
                'notes': metadata.notes,
            },
            'data': data,
        }
        
        with open(filepath, 'w') as f:
            json.dump(json_data, f, indent=2)
    
    def _save_excel(self, data: Dict[str, List[float]], filepath: Path) -> None:
        """Save data as Excel."""
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas required for Excel export")
        
        df = pd.DataFrame(data)
        df.to_excel(filepath, index=False)
    
    def load_log(self, filepath: Path) -> Tuple[Dict[str, List[float]], Optional[DataLogMetadata]]:
        """
        Load data log.
        
        Args:
            filepath: Path to log file
            
        Returns:
            Tuple of (data, metadata)
        """
        filepath = Path(filepath)
        suffix = filepath.suffix.lower()
        
        if suffix == '.csv':
            return self._load_csv(filepath), None
        elif suffix == '.json':
            return self._load_json(filepath)
        elif suffix == '.xlsx' or suffix == '.xls':
            return self._load_excel(filepath), None
        else:
            raise ValueError(f"Unsupported file format: {suffix}")
    
    def _load_csv(self, filepath: Path) -> Dict[str, List[float]]:
        """Load CSV file."""
        data: Dict[str, List[float]] = {}
        
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                for key, value in row.items():
                    if key not in data:
                        data[key] = []
                    try:
                        data[key].append(float(value))
                    except (ValueError, TypeError):
                        data[key].append(0.0)
        
        return data
    
    def _load_json(self, filepath: Path) -> Tuple[Dict[str, List[float]], Optional[DataLogMetadata]]:
        """Load JSON file."""
        with open(filepath, 'r') as f:
            json_data = json.load(f)
        
        if 'metadata' in json_data and 'data' in json_data:
            metadata_dict = json_data['metadata']
            metadata = DataLogMetadata(
                name=metadata_dict.get('name', ''),
                timestamp=metadata_dict.get('timestamp', 0.0),
                duration=metadata_dict.get('duration', 0.0),
                channels=metadata_dict.get('channels', []),
                sample_rate=metadata_dict.get('sample_rate', 0.0),
                vehicle_info=metadata_dict.get('vehicle_info'),
                session_info=metadata_dict.get('session_info'),
                notes=metadata_dict.get('notes'),
            )
            return json_data['data'], metadata
        else:
            return json_data, None
    
    def _load_excel(self, filepath: Path) -> Dict[str, List[float]]:
        """Load Excel file."""
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas required for Excel import")
        
        df = pd.read_excel(filepath)
        return df.to_dict('list')
    
    def list_logs(self) -> List[DataLogMetadata]:
        """List all available logs."""
        return list(self.metadata.values())
    
    def delete_log(self, name: str) -> bool:
        """Delete log and metadata."""
        if name in self.metadata:
            del self.metadata[name]
            self._save_metadata()
            return True
        return False


__all__ = [
    "DataLogManager",
    "DataLogMetadata",
]

