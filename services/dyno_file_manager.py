"""
Dyno File Manager - Manages loading and tracking of multiple dyno files.

Supports up to 15 loaded dyno files for comparison and analysis.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from services.virtual_dyno import DynoCurve
from services.dyno_file_importers import UniversalDynoImporter

LOGGER = logging.getLogger(__name__)

MAX_LOADED_FILES = 15


@dataclass
class LoadedDynoFile:
    """Represents a loaded dyno file."""
    
    file_path: Path
    curve: DynoCurve
    name: str  # Display name
    color: str  # Color for graphing
    visible: bool = True  # Whether curve is visible
    loaded_timestamp: float = field(default_factory=lambda: __import__('time').time())


class DynoFileManager:
    """Manages loading and tracking of multiple dyno files."""
    
    def __init__(self) -> None:
        """Initialize dyno file manager."""
        self.loaded_files: Dict[str, LoadedDynoFile] = {}  # key: file_path as string
        self.importer = UniversalDynoImporter()
        self._color_palette = [
            "#00e0ff",  # Cyan (default)
            "#ff6b6b",  # Red
            "#4ecdc4",  # Teal
            "#ffe66d",  # Yellow
            "#a8e6cf",  # Green
            "#ff8b94",  # Pink
            "#95e1d3",  # Mint
            "#f38181",  # Coral
            "#aa96da",  # Purple
            "#fcbad3",  # Light Pink
            "#a8d8ea",  # Sky Blue
            "#ffffd2",  # Cream
            "#ffd3a5",  # Peach
            "#fd9853",  # Orange
            "#a8e6cf",  # Light Green
        ]
        self._next_color_index = 1  # Start at 1 (0 is default live data color)
    
    def load_file(self, file_path: str | Path) -> LoadedDynoFile:
        """
        Load a dyno file.
        
        Args:
            file_path: Path to dyno file
            
        Returns:
            LoadedDynoFile object
            
        Raises:
            ValueError: If file cannot be loaded or limit reached
        """
        file_path = Path(file_path)
        file_path_str = str(file_path.resolve())
        
        # Check if already loaded
        if file_path_str in self.loaded_files:
            LOGGER.info(f"Dyno file already loaded: {file_path}")
            return self.loaded_files[file_path_str]
        
        # Check limit
        if len(self.loaded_files) >= MAX_LOADED_FILES:
            raise ValueError(
                f"Maximum of {MAX_LOADED_FILES} dyno files can be loaded. "
                "Please remove a file before loading another."
            )
        
        # Import file
        try:
            curve = self.importer.import_file(file_path)
            LOGGER.info(f"Loaded dyno file: {file_path} ({len(curve.readings)} readings)")
        except Exception as e:
            LOGGER.error(f"Failed to load dyno file {file_path}: {e}")
            raise ValueError(f"Failed to load dyno file: {e}")
        
        # Create display name
        name = file_path.stem  # Filename without extension
        
        # Get next color
        color = self._color_palette[self._next_color_index % len(self._color_palette)]
        self._next_color_index += 1
        
        # Create loaded file object
        loaded_file = LoadedDynoFile(
            file_path=file_path,
            curve=curve,
            name=name,
            color=color,
            visible=True,
        )
        
        # Store
        self.loaded_files[file_path_str] = loaded_file
        
        return loaded_file
    
    def remove_file(self, file_path: str | Path) -> bool:
        """
        Remove a loaded dyno file.
        
        Args:
            file_path: Path to file to remove
            
        Returns:
            True if removed, False if not found
        """
        file_path_str = str(Path(file_path).resolve())
        
        if file_path_str in self.loaded_files:
            del self.loaded_files[file_path_str]
            LOGGER.info(f"Removed dyno file: {file_path}")
            return True
        
        return False
    
    def get_file(self, file_path: str | Path) -> Optional[LoadedDynoFile]:
        """Get a loaded file by path."""
        file_path_str = str(Path(file_path).resolve())
        return self.loaded_files.get(file_path_str)
    
    def get_all_files(self) -> List[LoadedDynoFile]:
        """Get all loaded files."""
        return list(self.loaded_files.values())
    
    def get_visible_files(self) -> List[LoadedDynoFile]:
        """Get all visible loaded files."""
        return [f for f in self.loaded_files.values() if f.visible]
    
    def set_visibility(self, file_path: str | Path, visible: bool) -> bool:
        """
        Set visibility of a loaded file.
        
        Args:
            file_path: Path to file
            visible: Whether to show or hide
            
        Returns:
            True if found and updated, False otherwise
        """
        file_path_str = str(Path(file_path).resolve())
        
        if file_path_str in self.loaded_files:
            self.loaded_files[file_path_str].visible = visible
            return True
        
        return False
    
    def set_color(self, file_path: str | Path, color: str) -> bool:
        """
        Set color for a loaded file.
        
        Args:
            file_path: Path to file
            color: Color hex code
            
        Returns:
            True if found and updated, False otherwise
        """
        file_path_str = str(Path(file_path).resolve())
        
        if file_path_str in self.loaded_files:
            self.loaded_files[file_path_str].color = color
            return True
        
        return False
    
    def clear_all(self) -> None:
        """Clear all loaded files."""
        self.loaded_files.clear()
        self._next_color_index = 1
        LOGGER.info("Cleared all loaded dyno files")
    
    def get_count(self) -> int:
        """Get number of loaded files."""
        return len(self.loaded_files)
    
    def get_available_slots(self) -> int:
        """Get number of available slots for loading files."""
        return MAX_LOADED_FILES - len(self.loaded_files)


__all__ = ["DynoFileManager", "LoadedDynoFile", "MAX_LOADED_FILES"]

