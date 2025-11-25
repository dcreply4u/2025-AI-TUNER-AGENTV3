"""
Lap Comparison and Analysis Tools

Features:
- Side-by-side lap comparison
- Sector analysis
- Theoretical lap time calculation
- Predictive timing
- Performance deltas
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QComboBox,
)

from ui.advanced_graph_widget import AdvancedGraphWidget

LOGGER = logging.getLogger(__name__)

pg.setConfigOptions(antialias=True, background="black", foreground="white")


@dataclass
class LapData:
    """Lap data structure."""
    lap_number: int
    lap_time: float  # seconds
    sectors: List[float]  # Sector times in seconds
    data: Dict[str, List[float]]  # Channel data over time
    timestamp: float


@dataclass
class SectorSplit:
    """Sector split timing."""
    sector_number: int
    time: float
    start_distance: float
    end_distance: float


class LapComparisonWidget(QWidget):
    """Side-by-side lap comparison widget."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize lap comparison widget."""
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        self.lap1_combo = QComboBox()
        self.lap1_combo.setPlaceholderText("Select Lap 1")
        control_layout.addWidget(QLabel("Lap 1:"))
        control_layout.addWidget(self.lap1_combo)
        
        self.lap2_combo = QComboBox()
        self.lap2_combo.setPlaceholderText("Select Lap 2")
        control_layout.addWidget(QLabel("Lap 2:"))
        control_layout.addWidget(self.lap2_combo)
        
        compare_btn = QPushButton("Compare")
        compare_btn.clicked.connect(self._compare_laps)
        control_layout.addWidget(compare_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # Split view
        splitter = QSplitter(Qt.Horizontal)
        
        # Left graph (Lap 1)
        self.graph1 = AdvancedGraphWidget(title="Lap 1")
        splitter.addWidget(self.graph1)
        
        # Right graph (Lap 2)
        self.graph2 = AdvancedGraphWidget(title="Lap 2")
        splitter.addWidget(self.graph2)
        
        layout.addWidget(splitter)
        
        # Delta table
        self.delta_table = QTableWidget()
        self.delta_table.setColumnCount(4)
        self.delta_table.setHorizontalHeaderLabels(["Metric", "Lap 1", "Lap 2", "Delta"])
        layout.addWidget(self.delta_table)
        
        self.laps: Dict[int, LapData] = {}
        
    def add_lap(self, lap: LapData) -> None:
        """Add lap data."""
        self.laps[lap.lap_number] = lap
        self.lap1_combo.addItem(f"Lap {lap.lap_number} ({lap.lap_time:.3f}s)", lap.lap_number)
        self.lap2_combo.addItem(f"Lap {lap.lap_number} ({lap.lap_time:.3f}s)", lap.lap_number)
    
    def _compare_laps(self) -> None:
        """Compare selected laps."""
        lap1_idx = self.lap1_combo.currentIndex()
        lap2_idx = self.lap2_combo.currentIndex()
        
        if lap1_idx < 0 or lap2_idx < 0:
            return
        
        lap1_num = self.lap1_combo.itemData(lap1_idx)
        lap2_num = self.lap2_combo.itemData(lap2_idx)
        
        lap1 = self.laps.get(lap1_num)
        lap2 = self.laps.get(lap2_num)
        
        if not lap1 or not lap2:
            return
        
        # Plot both laps
        self._plot_lap(self.graph1, lap1, "#00e0ff")
        self._plot_lap(self.graph2, lap2, "#ff6b6b")
        
        # Calculate and display deltas
        self._calculate_deltas(lap1, lap2)
    
    def _plot_lap(self, graph: AdvancedGraphWidget, lap: LapData, color: str) -> None:
        """Plot lap data on graph."""
        # Plot speed vs time
        if 'Speed' in lap.data and 'Time' in lap.data:
            time_data = lap.data['Time']
            speed_data = lap.data['Speed']
            graph.set_data(time_data, speed_data, x_label="Time (s)", y_label="Speed (mph)", 
                          label="Speed", color=color)
    
    def _calculate_deltas(self, lap1: LapData, lap2: LapData) -> None:
        """Calculate and display performance deltas."""
        self.delta_table.setRowCount(0)
        
        # Lap time delta
        delta_time = lap2.lap_time - lap1.lap_time
        self._add_delta_row("Lap Time", f"{lap1.lap_time:.3f}s", f"{lap2.lap_time:.3f}s", 
                           f"{delta_time:+.3f}s")
        
        # Sector deltas
        for i, (s1, s2) in enumerate(zip(lap1.sectors, lap2.sectors)):
            delta = s2 - s1
            self._add_delta_row(f"Sector {i+1}", f"{s1:.3f}s", f"{s2:.3f}s", f"{delta:+.3f}s")
        
        # Peak values
        for channel in ['Speed', 'RPM', 'Boost']:
            if channel in lap1.data and channel in lap2.data:
                peak1 = max(lap1.data[channel]) if lap1.data[channel] else 0
                peak2 = max(lap2.data[channel]) if lap2.data[channel] else 0
                delta = peak2 - peak1
                self._add_delta_row(f"Peak {channel}", f"{peak1:.2f}", f"{peak2:.2f}", f"{delta:+.2f}")
    
    def _add_delta_row(self, metric: str, lap1_val: str, lap2_val: str, delta: str) -> None:
        """Add row to delta table."""
        row = self.delta_table.rowCount()
        self.delta_table.insertRow(row)
        
        self.delta_table.setItem(row, 0, QTableWidgetItem(metric))
        self.delta_table.setItem(row, 1, QTableWidgetItem(lap1_val))
        self.delta_table.setItem(row, 2, QTableWidgetItem(lap2_val))
        
        delta_item = QTableWidgetItem(delta)
        # Color code: green for faster, red for slower
        if delta.startswith('-') or delta.startswith('+') and float(delta.replace('+', '')) < 0:
            delta_item.setForeground(Qt.GlobalColor.green)
        else:
            delta_item.setForeground(Qt.GlobalColor.red)
        self.delta_table.setItem(row, 3, delta_item)


class TheoreticalLapTimeCalculator:
    """Calculate theoretical fastest lap from best sectors."""
    
    @staticmethod
    def calculate(laps: List[LapData]) -> Tuple[float, List[float]]:
        """
        Calculate theoretical fastest lap time.
        
        Args:
            laps: List of lap data
            
        Returns:
            Tuple of (theoretical_lap_time, best_sectors)
        """
        if not laps:
            return 0.0, []
        
        # Find best sector times
        num_sectors = len(laps[0].sectors)
        best_sectors = []
        
        for sector_idx in range(num_sectors):
            best_time = min(lap.sectors[sector_idx] for lap in laps if sector_idx < len(lap.sectors))
            best_sectors.append(best_time)
        
        # Theoretical lap time is sum of best sectors
        theoretical_time = sum(best_sectors)
        
        return theoretical_time, best_sectors
    
    @staticmethod
    def calculate_improvement_potential(actual_lap: LapData, theoretical_time: float) -> Dict[str, float]:
        """
        Calculate improvement potential.
        
        Args:
            actual_lap: Actual lap data
            theoretical_time: Theoretical fastest time
            
        Returns:
            Dictionary with improvement metrics
        """
        improvement = actual_lap.lap_time - theoretical_time
        improvement_percent = (improvement / actual_lap.lap_time) * 100
        
        # Sector improvements
        sector_improvements = []
        for i, sector_time in enumerate(actual_lap.sectors):
            # Would need best sectors to calculate per-sector improvement
            sector_improvements.append(0.0)  # Placeholder
        
        return {
            'improvement_seconds': improvement,
            'improvement_percent': improvement_percent,
            'sector_improvements': sector_improvements,
        }


class PredictiveTimingWidget(QWidget):
    """Predictive timing widget for real-time feedback."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize predictive timing widget."""
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        
        # Reference lap selector
        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("Reference Lap:"))
        self.reference_combo = QComboBox()
        control_layout.addWidget(self.reference_combo)
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # Status display
        self.status_label = QLabel("Waiting for reference lap...")
        self.status_label.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Delta display
        self.delta_label = QLabel("")
        self.delta_label.setStyleSheet("font-size: 18px; padding: 10px;")
        self.delta_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.delta_label)
        
        # Graph showing current vs reference
        self.graph = AdvancedGraphWidget(title="Current vs Reference")
        layout.addWidget(self.graph)
        
        self.reference_lap: Optional[LapData] = None
        self.current_sectors: List[float] = []
        self.current_time: float = 0.0
        
    def set_reference_lap(self, lap: LapData) -> None:
        """Set reference lap."""
        self.reference_lap = lap
        self.status_label.setText(f"Reference: Lap {lap.lap_number} ({lap.lap_time:.3f}s)")
    
    def update_current_lap(self, current_time: float, sectors: List[float]) -> None:
        """Update current lap progress."""
        self.current_time = current_time
        self.current_sectors = sectors
        
        if not self.reference_lap:
            return
        
        # Calculate delta
        if len(sectors) <= len(self.reference_lap.sectors):
            ref_sector_time = sum(self.reference_lap.sectors[:len(sectors)])
            current_sector_time = sum(sectors)
            delta = current_sector_time - ref_sector_time
            
            # Update display
            if delta < 0:
                self.delta_label.setText(f"FASTER by {abs(delta):.3f}s")
                self.delta_label.setStyleSheet("font-size: 18px; color: green; padding: 10px;")
            else:
                self.delta_label.setText(f"SLOWER by {delta:.3f}s")
                self.delta_label.setStyleSheet("font-size: 18px; color: red; padding: 10px;")
            
            # Update graph
            if 'Time' in self.reference_lap.data and 'Speed' in self.reference_lap.data:
                ref_time = self.reference_lap.data['Time']
                ref_speed = self.reference_lap.data['Speed']
                
                # Plot reference
                self.graph.set_data(ref_time, ref_speed, x_label="Time (s)", y_label="Speed (mph)",
                                  label="Reference", color="#00e0ff", clear=True)
                
                # Plot current (if available)
                # Would need current lap data structure


__all__ = [
    "LapComparisonWidget",
    "LapData",
    "SectorSplit",
    "TheoreticalLapTimeCalculator",
    "PredictiveTimingWidget",
]






