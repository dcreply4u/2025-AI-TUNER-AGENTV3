"""Main entry point for FastAPI server."""

from __future__ import annotations

import asyncio
import logging

import uvicorn

from api.server import app
from telemetry.can_logger import CANDataLogger

LOGGER = logging.getLogger(__name__)


async def start_services() -> None:
    """Start API server and background telemetry logging."""
    logger = CANDataLogger()
    logger.start_background_stream()

    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


def main() -> None:
    """Main entry point."""
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_services())


if __name__ == "__main__":
    main()

