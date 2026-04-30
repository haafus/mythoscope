import time
import json
import psutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import contextmanager
from datetime import datetime

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Track performance metrics including time and memory usage"""

    def __init__(self, metrics_file: Optional[str] = None, track_memory: bool = True):
        self.metrics_file = Path(metrics_file) if metrics_file else None
        self.track_memory = track_memory
        self.metrics: Dict[str, Any] = {}
        self.current_operation: Optional[str] = None
        self.operation_start: Optional[float] = None
        self.memory_start: Optional[float] = None

    def start_operation(self, name: str) -> None:
        """Start tracking an operation"""
        self.current_operation = name
        self.operation_start = time.time()

        if self.track_memory:
            self.memory_start = self._get_memory_usage()

        logger.debug(f"Starting operation: {name}")

    def end_operation(self, name: Optional[str] = None) -> Dict[str, Any]:
        """End tracking and return metrics for the operation"""
        op_name = name or self.current_operation
        if not op_name or not self.operation_start:
            logger.warning("No active operation to end")
            return {}

        duration = time.time() - self.operation_start

        metrics = {
            "operation": op_name,
            "duration_seconds": duration,
            "timestamp": datetime.now().isoformat()
        }

        if self.track_memory and self.memory_start is not None:
            memory_end = self._get_memory_usage()
            metrics["memory_usage_mb"] = memory_end
            metrics["memory_delta_mb"] = memory_end - self.memory_start

        # Store in metrics dictionary
        if op_name not in self.metrics:
            self.metrics[op_name] = []
        self.metrics[op_name].append(metrics)

        logger.info(f"Operation '{op_name}' completed in {duration:.2f}s")
        if self.track_memory:
            logger.debug(f"Memory usage: {metrics.get('memory_usage_mb', 0):.1f} MB")

        self.current_operation = None
        self.operation_start = None
        self.memory_start = None

        return metrics

    @contextmanager
    def track(self, name: str):
        """Context manager for tracking operations"""
        self.start_operation(name)
        try:
            yield self
        finally:
            self.end_operation(name)

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB with error handling"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.warning(f"Cannot get memory usage: {e}")
            return 0.0

    def get_summary(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """Get summary statistics for operations"""
        if operation:
            ops = self.metrics.get(operation, [])
        else:
            ops = []
            for op_list in self.metrics.values():
                ops.extend(op_list)

        if not ops:
            return {}

        durations = [o["duration_seconds"] for o in ops]

        summary = {
            "total_operations": len(ops),
            "total_time_seconds": sum(durations),
            "avg_duration_seconds": sum(durations) / len(durations),
            "min_duration_seconds": min(durations),
            "max_duration_seconds": max(durations)
        }

        if self.track_memory:
            memory_usages = [o.get("memory_usage_mb", 0) for o in ops if "memory_usage_mb" in o]
            if memory_usages:
                summary["avg_memory_usage_mb"] = sum(memory_usages) / len(memory_usages)
                summary["max_memory_usage_mb"] = max(memory_usages)

        return summary

    def save(self) -> None:
        """Save metrics to file"""
        if not self.metrics_file:
            return

        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)

        output = {
            "summary": self.get_summary(),
            "detailed": self.metrics,
            "generated_at": datetime.now().isoformat()
        }

        with open(self.metrics_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        logger.info(f"Performance metrics saved to {self.metrics_file}")

    def reset(self) -> None:
        """Reset all metrics"""
        self.metrics = {}
        self.current_operation = None
        self.operation_start = None
        self.memory_start = None