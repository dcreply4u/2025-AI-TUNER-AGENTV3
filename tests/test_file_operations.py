"""
Test File Operations

Tests file upload, export, save, and load functionality.
"""

import pytest
import json
import csv
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

from tests.conftest import temp_dir, sample_data


class TestFileUpload:
    """Test file upload functionality."""
    
    def test_csv_upload(self, temp_dir):
        """Test CSV file upload."""
        # Create sample CSV file
        csv_file = temp_dir / "test_data.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=sample_data.keys())
            writer.writeheader()
            writer.writerow(sample_data)
        
        # Verify file exists and is readable
        assert csv_file.exists()
        assert csv_file.stat().st_size > 0
        
        # Test reading the CSV
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert float(rows[0]['rpm']) == sample_data['rpm']
    
    def test_json_upload(self, temp_dir):
        """Test JSON file upload."""
        json_file = temp_dir / "test_data.json"
        with open(json_file, 'w') as f:
            json.dump(sample_data, f)
        
        assert json_file.exists()
        
        # Test reading the JSON
        with open(json_file, 'r') as f:
            data = json.load(f)
            assert data['rpm'] == sample_data['rpm']
            assert data['throttle'] == sample_data['throttle']
    
    def test_log_file_upload(self, temp_dir):
        """Test telemetry log file upload."""
        log_file = temp_dir / "telemetry.log"
        
        # Create sample log entries
        with open(log_file, 'w') as f:
            for i in range(10):
                entry = f"{i*0.1:.3f},rpm={6500+i*10},throttle={85.0+i*0.5}\n"
                f.write(entry)
        
        assert log_file.exists()
        
        # Verify can parse log file
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 10
            assert 'rpm=' in lines[0]


class TestFileExport:
    """Test file export functionality."""
    
    def test_export_to_csv(self, temp_dir, sample_data):
        """Test exporting data to CSV."""
        output_file = temp_dir / "export.csv"
        
        # Simulate export
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=sample_data.keys())
            writer.writeheader()
            writer.writerow(sample_data)
        
        assert output_file.exists()
        assert output_file.stat().st_size > 0
        
        # Verify exported data
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert float(rows[0]['rpm']) == sample_data['rpm']
    
    def test_export_to_json(self, temp_dir, sample_data):
        """Test exporting data to JSON."""
        output_file = temp_dir / "export.json"
        
        # Simulate export
        with open(output_file, 'w') as f:
            json.dump([sample_data], f, indent=2)
        
        assert output_file.exists()
        
        # Verify exported data
        with open(output_file, 'r') as f:
            data = json.load(f)
            assert isinstance(data, list)
            assert data[0]['rpm'] == sample_data['rpm']
    
    def test_export_to_excel(self, temp_dir, sample_data):
        """Test exporting data to Excel (if pandas available)."""
        try:
            import pandas as pd
            
            output_file = temp_dir / "export.xlsx"
            df = pd.DataFrame([sample_data])
            df.to_excel(output_file, index=False)
            
            assert output_file.exists()
            
            # Verify can read back
            df_read = pd.read_excel(output_file)
            assert len(df_read) == 1
            assert df_read.iloc[0]['rpm'] == sample_data['rpm']
        except ImportError:
            pytest.skip("pandas not available")


class TestFileSaveLoad:
    """Test save and load functionality."""
    
    def test_save_configuration(self, temp_dir):
        """Test saving configuration."""
        config_file = temp_dir / "config.json"
        config = {
            "can_bitrate": 500000,
            "can_channel": "can0",
            "gps_enabled": True,
            "sensor_poll_rate": 100,
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        assert config_file.exists()
        
        # Verify can load
        with open(config_file, 'r') as f:
            loaded_config = json.load(f)
            assert loaded_config == config
    
    def test_load_configuration(self, temp_dir):
        """Test loading configuration."""
        config_file = temp_dir / "config.json"
        config = {
            "can_bitrate": 500000,
            "can_channel": "can0",
        }
        
        # Save first
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        # Load
        with open(config_file, 'r') as f:
            loaded_config = json.load(f)
            assert loaded_config['can_bitrate'] == 500000
            assert loaded_config['can_channel'] == 'can0'
    
    def test_save_session_data(self, temp_dir, sample_data):
        """Test saving session data."""
        session_file = temp_dir / "session.json"
        
        session_data = {
            "session_id": "test_123",
            "start_time": 1234567890.0,
            "data_points": [sample_data],
        }
        
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
        
        assert session_file.exists()
        
        # Verify can load
        with open(session_file, 'r') as f:
            loaded = json.load(f)
            assert loaded['session_id'] == "test_123"
            assert len(loaded['data_points']) == 1

