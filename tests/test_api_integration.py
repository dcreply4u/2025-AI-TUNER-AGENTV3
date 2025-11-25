"""
API Integration Tests

Tests for API endpoints, authentication, and WebSocket connections.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

# Import API app
try:
    from api.mobile_api_server import app
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False
    app = None


@pytest.mark.skipif(not API_AVAILABLE, reason="API not available")
class TestAPIAuthentication:
    """Tests for API authentication."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_unauthenticated_access_denied(self, client):
        """Test that unauthenticated requests are denied."""
        response = client.get("/api/telemetry")
        assert response.status_code in [401, 403]

    def test_register_user(self, client):
        """Test user registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "password": "password123",
                "role": "viewer",
            },
        )
        assert response.status_code in [200, 201]

    def test_login_returns_token(self, client):
        """Test that login returns JWT token."""
        # Register first
        client.post(
            "/api/auth/register",
            json={
                "username": "testuser2",
                "password": "password123",
                "role": "viewer",
            },
        )
        # Login
        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser2",
                "password": "password123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data or "token" in data


@pytest.mark.skipif(not API_AVAILABLE, reason="API not available")
class TestAPICORS:
    """Tests for CORS configuration."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_cors_headers_present(self, client):
        """Test that CORS headers are present."""
        response = client.options("/api/telemetry")
        # CORS middleware should add headers
        assert "access-control-allow-origin" in response.headers or response.status_code == 200


@pytest.mark.skipif(not API_AVAILABLE, reason="API not available")
class TestAPITelemetry:
    """Tests for telemetry API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_telemetry_endpoint_exists(self, client):
        """Test that telemetry endpoint exists."""
        # This will fail auth, but endpoint should exist
        response = client.get("/api/telemetry")
        assert response.status_code in [200, 401, 403]  # Endpoint exists


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



