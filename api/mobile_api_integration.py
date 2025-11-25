"""
Mobile API Integration
Connects desktop application to mobile API server for data sharing
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Dict, Optional

import aiohttp

LOGGER = logging.getLogger(__name__)


class MobileAPIClient:
    """
    Client for connecting desktop app to mobile API server.
    Pushes telemetry data and receives commands from mobile app.
    """
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        """
        Initialize mobile API client.
        
        Args:
            api_url: Base URL of mobile API server
        """
        self.api_url = api_url.rstrip("/")
        self.session: Optional[aiohttp.ClientSession] = None
        self.running = False
        self.update_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start API client."""
        self.session = aiohttp.ClientSession()
        self.running = True
        LOGGER.info("Mobile API client started")
    
    async def stop(self) -> None:
        """Stop API client."""
        self.running = False
        if self.update_task:
            self.update_task.cancel()
        if self.session:
            await self.session.close()
        LOGGER.info("Mobile API client stopped")
    
    async def update_telemetry(self, telemetry: Dict[str, float]) -> bool:
        """
        Update telemetry data on API server.
        
        Args:
            telemetry: Telemetry data dictionary
            
        Returns:
            True if successful
        """
        if not self.session:
            return False
        
        try:
            async with self.session.post(
                f"{self.api_url}/api/telemetry/update",
                json=telemetry,
                timeout=aiohttp.ClientTimeout(total=2)
            ) as response:
                if response.status == 200:
                    return True
                else:
                    LOGGER.warning("Telemetry update failed: %d", response.status)
                    return False
        except Exception as e:
            LOGGER.debug("Error updating telemetry: %s", e)
            return False
    
    async def start_telemetry_updates(self, telemetry_callback, update_rate: float = 0.1) -> None:
        """
        Start periodic telemetry updates.
        
        Args:
            telemetry_callback: Callback function that returns current telemetry
            update_rate: Update rate in seconds
        """
        self.update_task = asyncio.create_task(self._update_loop(telemetry_callback, update_rate))
    
    async def _update_loop(self, telemetry_callback, update_rate: float) -> None:
        """Background loop for telemetry updates."""
        while self.running:
            try:
                telemetry = telemetry_callback()
                if telemetry:
                    await self.update_telemetry(telemetry)
                await asyncio.sleep(update_rate)
            except asyncio.CancelledError:
                break
            except Exception as e:
                LOGGER.error("Error in telemetry update loop: %s", e)
                await asyncio.sleep(update_rate)


# Global instance
_mobile_api_client: Optional[MobileAPIClient] = None


def get_mobile_api_client() -> Optional[MobileAPIClient]:
    """Get global mobile API client instance."""
    return _mobile_api_client


def initialize_mobile_api(api_url: str = "http://localhost:8000") -> MobileAPIClient:
    """Initialize global mobile API client."""
    global _mobile_api_client
    _mobile_api_client = MobileAPIClient(api_url)
    return _mobile_api_client
















