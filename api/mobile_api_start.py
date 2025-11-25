"""
Mobile API Server Startup Script
Starts the mobile API server for Android/iOS app integration
"""

from __future__ import annotations

import asyncio
import logging
import uvicorn

from api.mobile_api_server import app

LOGGER = logging.getLogger(__name__)


def main():
    """Start mobile API server."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Start server
    config = uvicorn.Config(
        app,
        host="0.0.0.0",  # Listen on all interfaces
        port=8000,
        log_level="info",
        access_log=True,
    )
    
    server = uvicorn.Server(config)
    
    LOGGER.info("Starting TelemetryIQ Mobile API Server on http://0.0.0.0:8000")
    LOGGER.info("API Documentation: http://localhost:8000/docs")
    LOGGER.info("WebSocket endpoint: ws://localhost:8000/ws/telemetry")
    
    asyncio.run(server.serve())


if __name__ == "__main__":
    main()
















