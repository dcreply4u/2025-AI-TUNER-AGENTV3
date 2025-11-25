"""
Security-Critical Function Tests

Tests for authentication, file operations, and security-sensitive code paths.
Target: 70%+ coverage for security-critical modules.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from api.auth import authenticate_user, create_user
from api.users_db import get_user, has_users, init_db
from config import Settings
from services.tune_map_database import TuneMapDatabase


class TestAuthentication:
    """Tests for authentication functions."""

    def test_create_user_hashes_password(self):
        """Test that passwords are hashed, not stored in plaintext."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_users.db"
            with patch("api.users_db.DB_PATH", db_path):
                init_db()
                create_user("testuser", "password123", "viewer")
                user = get_user("testuser")
                assert user is not None
                assert user["password_hash"] != "password123"
                assert user["password_hash"].startswith("$2b$")  # bcrypt hash

    def test_authenticate_user_valid_credentials(self):
        """Test authentication with valid credentials."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_users.db"
            with patch("api.users_db.DB_PATH", db_path):
                init_db()
                create_user("testuser", "password123", "viewer")
                user = authenticate_user("testuser", "password123")
                assert user is not None
                assert user["username"] == "testuser"

    def test_authenticate_user_invalid_password(self):
        """Test authentication with invalid password."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_users.db"
            with patch("api.users_db.DB_PATH", db_path):
                init_db()
                create_user("testuser", "password123", "viewer")
                user = authenticate_user("testuser", "wrongpassword")
                assert user is None

    def test_authenticate_user_nonexistent_user(self):
        """Test authentication with nonexistent user."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_users.db"
            with patch("api.users_db.DB_PATH", db_path):
                init_db()
                user = authenticate_user("nonexistent", "password123")
                assert user is None


class TestJWTConfiguration:
    """Tests for JWT configuration security."""

    def test_jwt_secret_required_in_production(self):
        """Test that JWT secret is required in production."""
        with patch.dict(os.environ, {"DEBUG_MODE": "false", "JWT_SECRET": ""}):
            with pytest.raises(ValueError, match="JWT_SECRET"):
                Settings()

    def test_jwt_secret_generated_in_development(self):
        """Test that JWT secret is generated in development mode."""
        with patch.dict(os.environ, {"DEBUG_MODE": "true", "JWT_SECRET": ""}):
            settings = Settings()
            assert settings.authjwt_secret_key
            assert len(settings.authjwt_secret_key) >= 32

    def test_jwt_secret_from_environment(self):
        """Test that JWT secret is read from environment."""
        test_secret = "test_secret_key_12345"
        with patch.dict(os.environ, {"JWT_SECRET": test_secret}):
            settings = Settings()
            assert settings.authjwt_secret_key == test_secret


class TestPathTraversal:
    """Tests for path traversal prevention."""

    def test_tune_id_validation(self):
        """Test that invalid tune IDs are rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = TuneMapDatabase(storage_path=Path(tmpdir))
            from services.tune_map_database import TuneMap, TuneMapEntry

            # Valid tune ID
            tune = TuneMap(
                tune_id="valid_tune_123",
                name="Test Tune",
                vehicle_make="Toyota",
                vehicle_model="Supra",
                vehicle_year=2020,
                ecu_type="Haltech",
                entries=[],
            )
            assert db.add_tune(tune) is True

            # Invalid tune ID with path traversal
            tune.tune_id = "../../../etc/passwd"
            with pytest.raises(ValueError, match="Invalid tune_id"):
                db.add_tune(tune)

            # Invalid tune ID with special characters
            tune.tune_id = "tune<script>alert('xss')</script>"
            with pytest.raises(ValueError, match="Invalid tune_id"):
                db.add_tune(tune)

    def test_path_traversal_prevention(self):
        """Test that path traversal attempts are blocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = TuneMapDatabase(storage_path=Path(tmpdir))
            from services.tune_map_database import TuneMap, TuneMapEntry

            # Attempt path traversal
            tune = TuneMap(
                tune_id="../../../etc/passwd",
                name="Malicious Tune",
                vehicle_make="Test",
                vehicle_model="Test",
                vehicle_year=2020,
                ecu_type="Test",
                entries=[],
            )
            with pytest.raises(ValueError, match="Path traversal"):
                db.add_tune(tune)


class TestFileOperations:
    """Tests for secure file operations."""

    def test_file_path_validation(self):
        """Test that file paths are validated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db = TuneMapDatabase(storage_path=Path(tmpdir))
            from services.tune_map_database import TuneMap

            # Valid path
            tune = TuneMap(
                tune_id="test_tune",
                name="Test",
                vehicle_make="Test",
                vehicle_model="Test",
                vehicle_year=2020,
                ecu_type="Test",
                entries=[],
            )
            assert db.add_tune(tune) is True

            # Ensure file is created in correct location
            tune_file = Path(tmpdir) / "tunes" / "test_tune.json"
            assert tune_file.exists()
            assert tune_file.is_file()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

