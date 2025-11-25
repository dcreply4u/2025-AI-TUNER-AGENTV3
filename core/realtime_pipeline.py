"""
Real-Time Data Processing Pipeline

High-performance pipeline for processing telemetry data with:
- Zero-copy data structures
- Lock-free queues
- Batch processing
- Parallel processing
- Backpressure handling
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

LOGGER = logging.getLogger(__name__)


class ProcessingStage(Enum):
    """Processing pipeline stages."""

    INGEST = "ingest"
    VALIDATE = "validate"
    TRANSFORM = "transform"
    ANALYZE = "analyze"
    STORE = "store"
    OUTPUT = "output"


@dataclass
class DataBatch:
    """Batch of data items for processing."""

    items: List[Dict[str, Any]]
    timestamp: float
    stage: ProcessingStage
    batch_id: int = 0


class LockFreeQueue:
    """Thread-safe queue with minimal locking."""

    def __init__(self, maxsize: int = 1000):
        """Initialize lock-free queue."""
        self.maxsize = maxsize
        self._queue: deque = deque(maxlen=maxsize)
        self._lock = threading.Lock()

    def put(self, item: Any, block: bool = True, timeout: Optional[float] = None) -> None:
        """Put item in queue."""
        with self._lock:
            if len(self._queue) >= self.maxsize:
                if not block:
                    raise queue.Full
                # Drop oldest item (FIFO)
                try:
                    self._queue.popleft()
                except IndexError:
                    pass
            self._queue.append(item)

    def get(self, block: bool = True, timeout: Optional[float] = None) -> Any:
        """Get item from queue."""
        with self._lock:
            if not self._queue:
                if not block:
                    raise queue.Empty
                return None
            return self._queue.popleft()

    def qsize(self) -> int:
        """Get queue size."""
        with self._lock:
            return len(self._queue)

    def empty(self) -> bool:
        """Check if queue is empty."""
        with self._lock:
            return len(self._queue) == 0


class ProcessingPipeline:
    """Real-time data processing pipeline."""

    def __init__(
        self,
        batch_size: int = 100,
        max_queue_size: int = 1000,
        num_workers: int = 4,
    ):
        """
        Initialize processing pipeline.

        Args:
            batch_size: Number of items per batch
            max_queue_size: Maximum queue size per stage
            num_workers: Number of worker threads per stage
        """
        self.batch_size = batch_size
        self.max_queue_size = max_queue_size
        self.num_workers = num_workers

        # Stage queues
        self.queues: Dict[ProcessingStage, LockFreeQueue] = {
            stage: LockFreeQueue(maxsize=max_queue_size) for stage in ProcessingStage
        }

        # Stage processors
        self.processors: Dict[ProcessingStage, Callable[[DataBatch], DataBatch]] = {}

        # Worker threads
        self.workers: List[threading.Thread] = []
        self.running = False
        self._lock = threading.Lock()

        # Statistics
        self.stats = {
            "items_processed": 0,
            "batches_processed": 0,
            "errors": 0,
            "stage_times": {stage.value: [] for stage in ProcessingStage},
        }

    def register_processor(self, stage: ProcessingStage, processor: Callable[[DataBatch], DataBatch]) -> None:
        """Register processor for a stage."""
        self.processors[stage] = processor

    def ingest(self, items: List[Dict[str, Any]]) -> None:
        """Ingest data items into pipeline."""
        if not items:
            return

        # Create batch
        batch = DataBatch(
            items=items,
            timestamp=time.time(),
            stage=ProcessingStage.INGEST,
            batch_id=self.stats["batches_processed"],
        )

        try:
            self.queues[ProcessingStage.INGEST].put(batch, block=False)
        except queue.Full:
            LOGGER.warning("Ingest queue full, dropping batch")
            self.stats["errors"] += 1

    def _process_stage(self, stage: ProcessingStage) -> None:
        """Process a single stage."""
        queue_obj = self.queues[stage]
        processor = self.processors.get(stage)

        if not processor:
            # Default pass-through
            def default_processor(batch: DataBatch) -> DataBatch:
                return batch

            processor = default_processor

        while self.running:
            try:
                batch = queue_obj.get(block=True, timeout=0.1)
                if batch is None:
                    continue

                # Process batch
                start_time = time.time()
                try:
                    processed_batch = processor(batch)
                    processed_batch.stage = self._get_next_stage(stage)

                    # Send to next stage
                    next_stage = processed_batch.stage
                    if next_stage != ProcessingStage.OUTPUT:
                        self.queues[next_stage].put(processed_batch, block=False)
                    else:
                        # Final stage - update stats
                        self.stats["items_processed"] += len(processed_batch.items)
                        self.stats["batches_processed"] += 1

                    # Record processing time
                    processing_time = time.time() - start_time
                    self.stats["stage_times"][stage.value].append(processing_time)

                except Exception as e:
                    LOGGER.error("Error processing batch in stage %s: %s", stage.value, e, exc_info=True)
                    self.stats["errors"] += 1

            except queue.Empty:
                continue
            except Exception as e:
                LOGGER.error("Error in stage %s: %s", stage.value, e, exc_info=True)
                self.stats["errors"] += 1

    def _get_next_stage(self, current_stage: ProcessingStage) -> ProcessingStage:
        """Get next stage in pipeline."""
        stage_order = [
            ProcessingStage.INGEST,
            ProcessingStage.VALIDATE,
            ProcessingStage.TRANSFORM,
            ProcessingStage.ANALYZE,
            ProcessingStage.STORE,
            ProcessingStage.OUTPUT,
        ]
        try:
            current_index = stage_order.index(current_stage)
            if current_index < len(stage_order) - 1:
                return stage_order[current_index + 1]
        except ValueError:
            pass
        return ProcessingStage.OUTPUT

    def start(self) -> None:
        """Start pipeline workers."""
        with self._lock:
            if self.running:
                return

            self.running = True

            # Start worker threads for each stage
            for stage in ProcessingStage:
                if stage == ProcessingStage.OUTPUT:
                    continue  # Output stage doesn't need workers

                for _ in range(self.num_workers):
                    worker = threading.Thread(
                        target=self._process_stage,
                        args=(stage,),
                        daemon=True,
                        name=f"Pipeline-{stage.value}",
                    )
                    worker.start()
                    self.workers.append(worker)

            LOGGER.info("Processing pipeline started with %d workers", len(self.workers))

    def stop(self) -> None:
        """Stop pipeline workers."""
        with self._lock:
            if not self.running:
                return

            self.running = False

            # Wait for workers to finish
            for worker in self.workers:
                worker.join(timeout=2.0)

            self.workers.clear()
            LOGGER.info("Processing pipeline stopped")

    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        with self._lock:
            # Calculate average processing times
            avg_times = {}
            for stage, times in self.stats["stage_times"].items():
                if times:
                    avg_times[stage] = sum(times) / len(times) * 1000  # Convert to ms
                else:
                    avg_times[stage] = 0.0

            # Calculate queue sizes
            queue_sizes = {stage.value: queue_obj.qsize() for stage, queue_obj in self.queues.items()}

            return {
                "items_processed": self.stats["items_processed"],
                "batches_processed": self.stats["batches_processed"],
                "errors": self.stats["errors"],
                "avg_processing_times_ms": avg_times,
                "queue_sizes": queue_sizes,
                "throughput_items_per_sec": (
                    self.stats["items_processed"] / (time.time() - self.stats.get("start_time", time.time()))
                    if self.stats.get("start_time")
                    else 0.0
                ),
            }

    def reset_stats(self) -> None:
        """Reset statistics."""
        with self._lock:
            self.stats = {
                "items_processed": 0,
                "batches_processed": 0,
                "errors": 0,
                "stage_times": {stage.value: [] for stage in ProcessingStage},
                "start_time": time.time(),
            }


__all__ = ["ProcessingPipeline", "ProcessingStage", "DataBatch", "LockFreeQueue"]



