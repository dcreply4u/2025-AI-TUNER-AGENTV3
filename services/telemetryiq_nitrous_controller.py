"""
TelemetryIQ Pro Series Nitrous Controller
Complete 6-stage pro series nitrous system with 8 relay controller.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from threading import Lock, Thread

LOGGER = logging.getLogger(__name__)


class StageMode(Enum):
    """Stage activation mode."""
    OFF = "off"
    TIMED = "timed"
    INSTANT = "instant"


class TimerBehavior(Enum):
    """Timer behavior when pedaling throttle."""
    START_OVER = "start_over"
    HOLD = "hold"


class RelayStatus(Enum):
    """Relay status."""
    OK = "ok"
    BLOWN_FUSE = "blown_fuse"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class NitrousTimer:
    """Nitrous timer configuration."""
    timer_id: int
    name: str
    duration_seconds: float
    enabled: bool = True
    start_trigger: str = "trans_brake_release"  # trans_brake_release, shifter_input, manual
    shifter_gear: Optional[int] = None  # For shifter input trigger


@dataclass
class NitrousStage:
    """Nitrous stage configuration (TelemetryIQ Pro Series style)."""
    stage_number: int
    name: str
    enabled: bool = True
    mode: StageMode = StageMode.TIMED
    activation_time: Optional[float] = None  # For timed mode
    timer_behavior: TimerBehavior = TimerBehavior.START_OVER
    start_trigger: str = "trans_brake_release"  # trans_brake_release, shifter_input, manual, stage_previous
    start_delay: float = 0.0  # Delay after trigger (seconds)
    relay_channel: int = 0  # Relay channel (0-7)
    shot_size_hp: int = 100
    hold_on_pedal: bool = True  # Hold timers when pedaling


@dataclass
class RelayController:
    """8-relay controller for nitrous system."""
    relay_id: int
    name: str
    channel: int  # 0-7
    status: RelayStatus = RelayStatus.UNKNOWN
    fuse_status: RelayStatus = RelayStatus.UNKNOWN
    current_amp: float = 0.0
    max_amp: float = 70.0  # 70A for single, 35A for split
    is_split_system: bool = False
    last_check: float = 0.0


@dataclass
class PurgeSystem:
    """Line purge system configuration."""
    purge_id: int
    name: str
    relay_channel: int
    enabled: bool = True
    duration_seconds: float = 3.0
    fuse_status: RelayStatus = RelayStatus.UNKNOWN


class TelemetryIQNitrousController:
    """TelemetryIQ Pro Series nitrous controller with 2-6 stages and 2-10 timers."""
    
    def __init__(
        self,
        num_stages: int = 3,
        num_timers: int = 5,
        enable_relay_controller: bool = True,
    ):
        """
        Initialize TelemetryIQ nitrous controller.
        
        Args:
            num_stages: Number of stages (2-6)
            num_timers: Number of timers (2-10)
            enable_relay_controller: Enable 8-relay controller
        """
        if not (2 <= num_stages <= 6):
            raise ValueError("Number of stages must be between 2 and 6")
        if not (2 <= num_timers <= 10):
            raise ValueError("Number of timers must be between 2 and 10")
        
        self.num_stages = num_stages
        self.num_timers = num_timers
        
        # Initialize stages
        self.stages: List[NitrousStage] = []
        for i in range(num_stages):
            self.stages.append(NitrousStage(
                stage_number=i + 1,
                name=f"Stage {i + 1}",
                relay_channel=i,
            ))
        
        # Initialize timers
        self.timers: List[NitrousTimer] = []
        for i in range(num_timers):
            self.timers.append(NitrousTimer(
                timer_id=i + 1,
                name=f"Timer {i + 1}",
                duration_seconds=2.0,
            ))
        
        # 8-relay controller
        self.relays: List[RelayController] = []
        if enable_relay_controller:
            for i in range(8):
                self.relays.append(RelayController(
                    relay_id=i + 1,
                    name=f"Relay {i + 1}",
                    channel=i,
                ))
        
        # Purge systems
        self.purges: List[PurgeSystem] = [
            PurgeSystem(
                purge_id=1,
                name="Motor Purge",
                relay_channel=6,
            ),
            PurgeSystem(
                purge_id=2,
                name="Line Purge 1",
                relay_channel=7,
            ),
            PurgeSystem(
                purge_id=3,
                name="Line Purge 2",
                relay_channel=8 if len(self.relays) > 8 else 7,
            ),
        ]
        
        # Control state
        self.active_stages: List[int] = []
        self.active_timers: List[int] = []
        self.stage_start_times: Dict[int, float] = {}
        self.timer_start_times: Dict[int, float] = {}
        self.trans_brake_active: bool = False
        self.clutch_active: bool = False
        self.shifter_gear: Optional[int] = None
        self.throttle_pedaling: bool = False
        
        # Staging interrupt (nanosecond response)
        self.staging_interrupt_enabled: bool = True
        self.last_interrupt_time: float = 0.0
        
        # Lock for thread safety
        self._lock = Lock()
        self._monitoring_thread: Optional[Thread] = None
        self._running = False
        
        # Status callbacks
        self.status_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        
        LOGGER.info(
            "TelemetryIQ nitrous controller initialized: %d stages, %d timers, %d relays",
            num_stages, num_timers, len(self.relays)
        )
    
    def start_monitoring(self) -> None:
        """Start monitoring thread."""
        if self._running:
            return
        
        self._running = True
        self._monitoring_thread = Thread(target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()
        LOGGER.info("Nitrous controller monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop monitoring thread."""
        self._running = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=2.0)
        LOGGER.info("Nitrous controller monitoring stopped")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                with self._lock:
                    current_time = time.time()
                    
                    # Check relay status
                    self._check_relay_status()
                    
                    # Update active stages
                    self._update_active_stages(current_time)
                    
                    # Update active timers
                    self._update_active_timers(current_time)
                    
                    # Broadcast status
                    self._broadcast_status()
                
                time.sleep(0.01)  # 100 Hz update rate
                
            except Exception as e:
                LOGGER.error("Error in nitrous monitoring loop: %s", e)
                time.sleep(0.1)
    
    def _check_relay_status(self) -> None:
        """Check relay and fuse status."""
        for relay in self.relays:
            # Simulate status check (would integrate with hardware)
            # Check fuse status
            if relay.fuse_status == RelayStatus.UNKNOWN:
                # Simulate fuse check
                relay.fuse_status = RelayStatus.OK
            
            # Check relay status
            if relay.status == RelayStatus.UNKNOWN:
                relay.status = RelayStatus.OK
            
            relay.last_check = time.time()
    
    def _update_active_stages(self, current_time: float) -> None:
        """Update active stages based on timers and triggers."""
        for stage in self.stages:
            if not stage.enabled or stage.mode == StageMode.OFF:
                if stage.stage_number in self.active_stages:
                    self.active_stages.remove(stage.stage_number)
                    self._deactivate_relay(stage.relay_channel)
                continue
            
            # Check if stage should be active
            should_be_active = False
            
            if stage.stage_number in self.active_stages:
                # Stage is already active
                if stage.mode == StageMode.TIMED and stage.activation_time:
                    # Check if timer has expired
                    start_time = self.stage_start_times.get(stage.stage_number, current_time)
                    if current_time - start_time >= stage.activation_time:
                        should_be_active = False
                    else:
                        should_be_active = True
                elif stage.mode == StageMode.INSTANT:
                    should_be_active = True
            else:
                # Check if stage should activate
                if self._check_stage_trigger(stage, current_time):
                    should_be_active = True
                    self.stage_start_times[stage.stage_number] = current_time
            
            # Update active state
            if should_be_active and stage.stage_number not in self.active_stages:
                self.active_stages.append(stage.stage_number)
                self._activate_relay(stage.relay_channel)
            elif not should_be_active and stage.stage_number in self.active_stages:
                self.active_stages.remove(stage.stage_number)
                self._deactivate_relay(stage.relay_channel)
    
    def _update_active_timers(self, current_time: float) -> None:
        """Update active timers."""
        for timer in self.timers:
            if not timer.enabled:
                if timer.timer_id in self.active_timers:
                    self.active_timers.remove(timer.timer_id)
                continue
            
            if timer.timer_id in self.active_timers:
                # Check if timer expired
                start_time = self.timer_start_times.get(timer.timer_id, current_time)
                if current_time - start_time >= timer.duration_seconds:
                    self.active_timers.remove(timer.timer_id)
            else:
                # Check if timer should start
                if self._check_timer_trigger(timer, current_time):
                    self.active_timers.append(timer.timer_id)
                    self.timer_start_times[timer.timer_id] = current_time
    
    def _check_stage_trigger(self, stage: NitrousStage, current_time: float) -> bool:
        """Check if stage trigger condition is met."""
        if stage.start_trigger == "trans_brake_release":
            return self.trans_brake_active and not self._was_trans_brake_released()
        elif stage.start_trigger == "shifter_input":
            return self.shifter_gear is not None and self.shifter_gear == stage.start_delay
        elif stage.start_trigger == "stage_previous":
            # Activate when previous stage activates
            if stage.stage_number > 1:
                prev_stage_num = stage.stage_number - 1
                return prev_stage_num in self.active_stages
        elif stage.start_trigger == "manual":
            return False  # Manual activation only
        
        return False
    
    def _check_timer_trigger(self, timer: NitrousTimer, current_time: float) -> bool:
        """Check if timer trigger condition is met."""
        if timer.start_trigger == "trans_brake_release":
            return self.trans_brake_active and not self._was_trans_brake_released()
        elif timer.start_trigger == "shifter_input":
            if timer.shifter_gear:
                return self.shifter_gear == timer.shifter_gear
            return self.shifter_gear is not None
        elif timer.start_trigger == "manual":
            return False  # Manual activation only
        
        return False
    
    def _was_trans_brake_released(self) -> bool:
        """Check if trans brake was just released (for nanosecond response)."""
        # This would check hardware interrupt
        # For now, simulate
        return False
    
    def _activate_relay(self, channel: int) -> None:
        """Activate relay channel."""
        if 0 <= channel < len(self.relays):
            relay = self.relays[channel]
            relay.status = RelayStatus.OK
            LOGGER.debug("Activated relay channel %d", channel)
    
    def _deactivate_relay(self, channel: int) -> None:
        """Deactivate relay channel."""
        if 0 <= channel < len(self.relays):
            relay = self.relays[channel]
            LOGGER.debug("Deactivated relay channel %d", channel)
    
    def set_trans_brake_state(self, active: bool) -> None:
        """Set trans brake state (nanosecond response interrupt)."""
        with self._lock:
            if active != self.trans_brake_active:
                self.trans_brake_active = active
                self.last_interrupt_time = time.time()
                
                if not active and self.staging_interrupt_enabled:
                    # Trans brake released - trigger stages/timers
                    self._handle_trans_brake_release()
    
    def set_clutch_state(self, active: bool) -> None:
        """Set clutch state."""
        with self._lock:
            self.clutch_active = active
    
    def set_shifter_gear(self, gear: Optional[int]) -> None:
        """Set shifter gear (for shifter input triggers)."""
        with self._lock:
            if gear != self.shifter_gear:
                self.shifter_gear = gear
                if gear is not None:
                    self._handle_shifter_input(gear)
    
    def set_throttle_pedaling(self, pedaling: bool) -> None:
        """Set throttle pedaling state."""
        with self._lock:
            self.throttle_pedaling = pedaling
            
            if pedaling:
                # Handle timer behavior
                for stage in self.stages:
                    if stage.stage_number in self.active_stages:
                        if stage.timer_behavior == TimerBehavior.START_OVER:
                            # Restart timers
                            if stage.stage_number in self.stage_start_times:
                                self.stage_start_times[stage.stage_number] = time.time()
                        elif stage.timer_behavior == TimerBehavior.HOLD:
                            # Hold timers (do nothing)
                            pass
    
    def _handle_trans_brake_release(self) -> None:
        """Handle trans brake release (nanosecond response)."""
        # Activate stages/timers configured for trans brake release
        for stage in self.stages:
            if stage.enabled and stage.start_trigger == "trans_brake_release":
                if stage.stage_number not in self.active_stages:
                    self.active_stages.append(stage.stage_number)
                    self.stage_start_times[stage.stage_number] = time.time()
                    self._activate_relay(stage.relay_channel)
        
        for timer in self.timers:
            if timer.enabled and timer.start_trigger == "trans_brake_release":
                if timer.timer_id not in self.active_timers:
                    self.active_timers.append(timer.timer_id)
                    self.timer_start_times[timer.timer_id] = time.time()
    
    def _handle_shifter_input(self, gear: int) -> None:
        """Handle shifter input (after gear shift)."""
        # Activate stages/timers configured for shifter input
        for stage in self.stages:
            if stage.enabled and stage.start_trigger == "shifter_input":
                if stage.stage_number not in self.active_stages:
                    self.active_stages.append(stage.stage_number)
                    self.stage_start_times[stage.stage_number] = time.time()
                    self._activate_relay(stage.relay_channel)
        
        for timer in self.timers:
            if timer.enabled and timer.start_trigger == "shifter_input":
                if timer.shifter_gear is None or timer.shifter_gear == gear:
                    if timer.timer_id not in self.active_timers:
                        self.active_timers.append(timer.timer_id)
                        self.timer_start_times[timer.timer_id] = time.time()
    
    def activate_purge(self, purge_id: int) -> bool:
        """Activate line purge."""
        purge = next((p for p in self.purges if p.purge_id == purge_id), None)
        if not purge or not purge.enabled:
            return False
        
        # Activate purge relay
        if purge.relay_channel < len(self.relays):
            self._activate_relay(purge.relay_channel)
            LOGGER.info("Activated purge: %s", purge.name)
            return True
        
        return False
    
    def deactivate_purge(self, purge_id: int) -> bool:
        """Deactivate line purge."""
        purge = next((p for p in self.purges if p.purge_id == purge_id), None)
        if not purge:
            return False
        
        if purge.relay_channel < len(self.relays):
            self._deactivate_relay(purge.relay_channel)
            LOGGER.info("Deactivated purge: %s", purge.name)
            return True
        
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        with self._lock:
            return {
                "stages": {
                    "total": self.num_stages,
                    "active": self.active_stages,
                    "config": [
                        {
                            "stage": s.stage_number,
                            "name": s.name,
                            "enabled": s.enabled,
                            "mode": s.mode.value,
                            "active": s.stage_number in self.active_stages,
                        }
                        for s in self.stages
                    ],
                },
                "timers": {
                    "total": self.num_timers,
                    "active": self.active_timers,
                },
                "relays": [
                    {
                        "id": r.relay_id,
                        "name": r.name,
                        "status": r.status.value,
                        "fuse_status": r.fuse_status.value,
                        "current_amp": r.current_amp,
                    }
                    for r in self.relays
                ],
                "purges": [
                    {
                        "id": p.purge_id,
                        "name": p.name,
                        "enabled": p.enabled,
                        "fuse_status": p.fuse_status.value,
                    }
                    for p in self.purges
                ],
                "inputs": {
                    "trans_brake": self.trans_brake_active,
                    "clutch": self.clutch_active,
                    "shifter_gear": self.shifter_gear,
                    "throttle_pedaling": self.throttle_pedaling,
                },
                "staging_interrupt": {
                    "enabled": self.staging_interrupt_enabled,
                    "last_interrupt": self.last_interrupt_time,
                },
            }
    
    def _broadcast_status(self) -> None:
        """Broadcast status to callbacks."""
        status = self.get_status()
        for callback in self.status_callbacks:
            try:
                callback(status)
            except Exception as e:
                LOGGER.error("Error in status callback: %s", e)
    
    def register_status_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register status callback."""
        self.status_callbacks.append(callback)
    
    def update_stage_config(self, stage_number: int, config: Dict[str, Any]) -> bool:
        """Update stage configuration."""
        stage = next((s for s in self.stages if s.stage_number == stage_number), None)
        if not stage:
            return False
        
        with self._lock:
            if "enabled" in config:
                stage.enabled = config["enabled"]
            if "mode" in config:
                stage.mode = StageMode(config["mode"])
            if "activation_time" in config:
                stage.activation_time = config["activation_time"]
            if "timer_behavior" in config:
                stage.timer_behavior = TimerBehavior(config["timer_behavior"])
            if "start_trigger" in config:
                stage.start_trigger = config["start_trigger"]
            if "start_delay" in config:
                stage.start_delay = config["start_delay"]
            if "hold_on_pedal" in config:
                stage.hold_on_pedal = config["hold_on_pedal"]
        
        LOGGER.info("Updated stage %d configuration", stage_number)
        return True
    
    def update_timer_config(self, timer_id: int, config: Dict[str, Any]) -> bool:
        """Update timer configuration."""
        timer = next((t for t in self.timers if t.timer_id == timer_id), None)
        if not timer:
            return False
        
        with self._lock:
            if "enabled" in config:
                timer.enabled = config["enabled"]
            if "duration_seconds" in config:
                timer.duration_seconds = config["duration_seconds"]
            if "start_trigger" in config:
                timer.start_trigger = config["start_trigger"]
            if "shifter_gear" in config:
                timer.shifter_gear = config["shifter_gear"]
        
        LOGGER.info("Updated timer %d configuration", timer_id)
        return True


__all__ = [
    "TelemetryIQNitrousController",
    "NitrousStage",
    "NitrousTimer",
    "RelayController",
    "PurgeSystem",
    "StageMode",
    "TimerBehavior",
    "RelayStatus",
]
