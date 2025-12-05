"""
Memlyze - Visual Memory Profiler

A low-overhead memory profiler that tracks allocations in real-time
and provides interactive visualization.
"""

__version__ = "0.1.0"

from .tracer import MemoryTracer, start, stop, is_tracing
from .format import TraceFormat, EventType

__all__ = [
    "MemoryTracer",
    "start",
    "stop",
    "is_tracing",
    "TraceFormat",
    "EventType",
    "__version__",
]
