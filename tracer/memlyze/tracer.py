"""
Core memory tracer that hooks into Python's memory allocator.
"""

import tracemalloc
import time
import threading
import gc
import sys
import os
from typing import Optional, List, Tuple
from .format import TraceFormat
from .writer import TraceWriter


# Global tracer instance
_active_tracer: Optional['MemoryTracer'] = None


class MemoryTracer:
    """
    Main memory tracer class.
    
    Hooks into Python's tracemalloc to track allocations with minimal overhead.
    """
    
    def __init__(self,
                 output_file: str = "trace.mlyze",
                 sample_rate: float = 1.0,
                 max_stack_depth: int = 10,
                 track_gc: bool = True,
                 max_events: int = 10000):
        """
        Initialize memory tracer.
        
        Args:
            output_file: Path to output .mlyze file
            sample_rate: Fraction of allocations to track (1.0 = all, 0.1 = 10%)
            max_stack_depth: Maximum stack frames to capture
            track_gc: Whether to track garbage collection events
            max_events: Maximum events to keep in memory (ring buffer)
        """
        self.output_file = output_file
        self.sample_rate = sample_rate
        self.max_stack_depth = max_stack_depth
        self.track_gc = track_gc
        self.max_events = max_events
        
        self.format = TraceFormat()
        self.writer: Optional[TraceWriter] = None
        self.start_time: float = 0
        self.last_event_time: float = 0
        self.is_active = False
        
        # Sampling state
        self.allocation_count = 0
        self.sample_threshold = int(1.0 / sample_rate) if sample_rate < 1.0 else 1
        
        # Statistics
        self.stats = {
            "allocations_seen": 0,
            "allocations_tracked": 0,
            "deallocations_tracked": 0,
            "gc_events": 0,
        }
        
        # Previous snapshot for diff
        self.prev_snapshot: Optional[tracemalloc.Snapshot] = None
        
    def start(self):
        """Start tracing."""
        global _active_tracer
        
        if self.is_active:
            raise RuntimeError("Tracer is already active")
        
        # Start tracemalloc
        tracemalloc.start(self.max_stack_depth)
        
        # Initialize writer
        self.writer = TraceWriter(self.output_file, max_queue_size=self.max_events)
        
        # Record start time
        self.start_time = time.time()
        self.last_event_time = self.start_time
        
        # Write header (will be updated with metadata on close)
        header = self.format.create_header(self.start_time)
        self.writer.open(header)
        
        # Take initial snapshot
        self.prev_snapshot = tracemalloc.take_snapshot()
        
        # Set up GC tracking
        if self.track_gc:
            gc.callbacks.append(self._on_gc)
        
        self.is_active = True
        _active_tracer = self
        
        # Professional startup message with ANSI colors
        print("\n" + self._color("="*70, "cyan"))
        print(self._color("  Memlyze v0.1.0", "cyan", bold=True) + self._color(" | Memory Profiler", "white"))
        print(self._color("="*70, "cyan"))
        print(self._color("  CONFIGURATION", "yellow", bold=True))
        print(self._color("  ├─", "white") + " Output File    : " + self._color(self.output_file, "green"))
        print(self._color("  ├─", "white") + " Sample Rate    : " + self._color(f"{self.sample_rate * 100:.1f}%", "green") + " of allocations")
        print(self._color("  ├─", "white") + " Stack Depth    : " + self._color(f"{self.max_stack_depth}", "green") + " frames")
        print(self._color("  └─", "white") + " GC Tracking    : " + self._color("ENABLED", "green" if self.track_gc else "red"))
        print(self._color("="*70, "cyan"))
        print(self._color("  STATUS", "yellow", bold=True) + " : " + self._color("TRACING ACTIVE", "green", bold=True))
        print(self._color("="*70, "cyan") + "\n")
    
    def stop(self):
        """Stop tracing and save trace file."""
        global _active_tracer
        
        if not self.is_active:
            return
        
        # Remove GC callback
        if self.track_gc and self._on_gc in gc.callbacks:
            gc.callbacks.remove(self._on_gc)
        
        # Take final snapshot and process differences
        current_snapshot = tracemalloc.take_snapshot()
        self._process_snapshot_diff(self.prev_snapshot, current_snapshot)
        
        # Stop tracemalloc
        tracemalloc.stop()
        
        # Close writer
        if self.writer:
            self.writer.close()
            writer_stats = self.writer.get_stats()
            duration = time.time() - self.start_time
            
            # Professional summary with colors
            print("\n" + self._color("="*70, "cyan"))
            print(self._color("  TRACE COMPLETE", "green", bold=True))
            print(self._color("="*70, "cyan"))
            
            # File info section
            print(self._color("\n  OUTPUT", "yellow", bold=True))
            file_size_kb = writer_stats['bytes_written'] / 1024
            file_size_mb = file_size_kb / 1024
            size_str = f"{file_size_mb:.2f} MB" if file_size_mb >= 1 else f"{file_size_kb:.2f} KB"
            print(self._color("  ├─", "white") + " File           : " + self._color(self.output_file, "green"))
            print(self._color("  └─", "white") + " Size           : " + self._color(f"{writer_stats['bytes_written']:,} bytes", "white") + f" ({size_str})")
            
            # Statistics section
            print(self._color("\n  MEMORY EVENTS", "yellow", bold=True))
            print(self._color("  ├─", "white") + " Allocations    : " + self._color(f"{self.stats['allocations_seen']:>10,}", "white") + " seen, " + 
                  self._color(f"{self.stats['allocations_tracked']:>10,}", "green") + " tracked")
            print(self._color("  ├─", "white") + " Deallocations  : " + self._color(f"{self.stats['deallocations_tracked']:>10,}", "white"))
            print(self._color("  └─", "white") + " GC Events      : " + self._color(f"{self.stats['gc_events']:>10,}", "white"))
            
            # Performance section
            print(self._color("\n  PERFORMANCE", "yellow", bold=True))
            print(self._color("  ├─", "white") + " Events Written : " + self._color(f"{writer_stats['events_written']:>10,}", "white"))
            print(self._color("  ├─", "white") + " Events Dropped : " + self._color(f"{writer_stats['events_dropped']:>10,}", "red" if writer_stats['events_dropped'] > 0 else "white"))
            print(self._color("  ├─", "white") + " Duration       : " + self._color(f"{duration:>10.2f}s", "white"))
            
            # Calculate overhead estimate
            if self.stats['allocations_seen'] > 0:
                alloc_rate = self.stats['allocations_seen'] / duration
                print(self._color("  └─", "white") + " Alloc Rate     : " + self._color(f"{alloc_rate:>10,.0f}", "white") + " allocs/sec")
            
            # Sampling efficiency
            if self.stats['allocations_seen'] > 0:
                sample_pct = (self.stats['allocations_tracked'] / self.stats['allocations_seen']) * 100
                print(self._color("\n  SAMPLING", "yellow", bold=True))
                print(self._color("  └─", "white") + " Efficiency     : " + self._color(f"{sample_pct:>10.1f}%", "green") + " captured")
            
            # Warnings section
            if writer_stats['events_dropped'] > 0:
                print(self._color("\n  WARNINGS", "red", bold=True))
                print(self._color("  └─", "white") + " Ring buffer full: " + self._color(f"{writer_stats['events_dropped']:,} events dropped", "red"))
                print(self._color("     Recommendation: Increase --sample-rate or buffer size", "yellow"))
            
            print(self._color("="*70, "cyan"))
            print(self._color("  NEXT STEPS", "yellow", bold=True))
            print(self._color("  └─", "white") + " Analyze results : " + 
                  self._color(f"memlyze analyze {os.path.basename(self.output_file)}", "green"))
            print(self._color("     Web interface : ", "white") + 
                  self._color(f"memlyze serve {os.path.basename(self.output_file)}", "green"))
            print(self._color("     Help          : ", "white") + 
                  self._color("memlyze --help", "green"))
            print(self._color("="*70, "cyan") + "\n")
        
        self.is_active = False
        _active_tracer = None
    
    def _process_snapshot_diff(self, prev: Optional[tracemalloc.Snapshot], current: tracemalloc.Snapshot):
        """Process differences between snapshots to find allocations/deallocations."""
        if prev is None:
            return
        
        # Get differences
        top_stats = current.compare_to(prev, 'lineno')
        
        current_time = time.time()
        timestamp_delta = int((current_time - self.last_event_time) * 1_000_000)
        
        for stat in top_stats:
            self.stats['allocations_seen'] += 1
            
            # Apply sampling
            if self.sample_rate < 1.0:
                self.allocation_count += 1
                if self.allocation_count % self.sample_threshold != 0:
                    continue
            
            if stat.size_diff > 0:
                # Allocation
                self._record_allocation(
                    timestamp_delta,
                    stat.size_diff,
                    stat.traceback
                )
            elif stat.size_diff < 0:
                # Deallocation
                self._record_deallocation(timestamp_delta, abs(stat.size_diff))
        
        self.last_event_time = current_time
    
    def _record_allocation(self, timestamp_delta: int, size: int, traceback: tracemalloc.Traceback):
        """Record an allocation event."""
        if not self.writer:
            return
        
        # Extract stack trace
        stack_trace = []
        for frame in traceback:
            stack_trace.append((frame.filename, frame.lineno, ""))
        
        # Get stack ID
        stack_id = self.format.get_or_create_stack_id(stack_trace)
        
        # Get thread ID
        thread_id = threading.get_ident() & 0xFFFF  # Truncate to uint16
        
        # Encode event
        event_data = self.format.encode_alloc_event(
            timestamp_delta,
            0,  # Address not available from tracemalloc
            size,
            stack_id,
            thread_id
        )
        
        # Write event
        self.writer.write_event(event_data)
        self.stats['allocations_tracked'] += 1
    
    def _record_deallocation(self, timestamp_delta: int, size: int):
        """Record a deallocation event."""
        if not self.writer:
            return
        
        # Encode event (address 0 since we don't have it)
        event_data = self.format.encode_free_event(timestamp_delta, 0)
        
        # Write event
        self.writer.write_event(event_data)
        self.stats['deallocations_tracked'] += 1
    
    def _on_gc(self, phase: str, info: dict):
        """Callback for GC events."""
        if phase != "stop":
            return
        
        if not self.writer:
            return
        
        current_time = time.time()
        timestamp_delta = int((current_time - self.last_event_time) * 1_000_000)
        
        # Encode GC event
        event_data = self.format.encode_gc_event(
            timestamp_delta,
            info.get('collected', 0),
            0  # Bytes freed not available
        )
        
        # Write event
        self.writer.write_event(event_data)
        self.stats['gc_events'] += 1
        self.last_event_time = current_time
    
    def mark(self, name: str):
        """Add a marker/annotation to the trace."""
        if not self.writer or not self.is_active:
            return
        
        current_time = time.time()
        timestamp_delta = int((current_time - self.last_event_time) * 1_000_000)
        
        event_data = self.format.encode_marker_event(timestamp_delta, name)
        self.writer.write_event(event_data)
        self.last_event_time = current_time
    
    def snapshot(self):
        """Take a snapshot and process allocations since last snapshot."""
        if not self.is_active:
            return
        
        current_snapshot = tracemalloc.take_snapshot()
        self._process_snapshot_diff(self.prev_snapshot, current_snapshot)
        self.prev_snapshot = current_snapshot
    
    @staticmethod
    def _color(text, color, bold=False, dim=False):
        """Apply ANSI color codes to text."""
        colors = {
            "black": "30",
            "red": "31",
            "green": "32",
            "yellow": "33",
            "blue": "34",
            "magenta": "35",
            "cyan": "36",
            "white": "37",
        }
        
        code = colors.get(color, "37")
        style = []
        
        if bold:
            style.append("1")
        if dim:
            style.append("2")
        
        if style:
            return f"\033[{';'.join(style)};{code}m{text}\033[0m"
        else:
            return f"\033[{code}m{text}\033[0m"


# Convenience functions
def start(output_file: str = "trace.mlyze",
          sample_rate: float = 1.0,
          max_stack_depth: int = 10,
          track_gc: bool = True) -> MemoryTracer:
    """
    Start memory tracing.
    
    Args:
        output_file: Path to output .mlyze file
        sample_rate: Fraction of allocations to track (1.0 = all, 0.1 = 10%)
        max_stack_depth: Maximum stack frames to capture
        track_gc: Whether to track garbage collection events
        
    Returns:
        MemoryTracer instance
    """
    tracer = MemoryTracer(
        output_file=output_file,
        sample_rate=sample_rate,
        max_stack_depth=max_stack_depth,
        track_gc=track_gc
    )
    tracer.start()
    return tracer


def stop():
    """Stop the active tracer."""
    global _active_tracer
    if _active_tracer:
        _active_tracer.stop()


def is_tracing() -> bool:
    """Check if tracing is active."""
    return _active_tracer is not None and _active_tracer.is_active


def mark(name: str):
    """Add a marker to the active trace."""
    global _active_tracer
    if _active_tracer:
        _active_tracer.mark(name)


def snapshot():
    """Take a snapshot with the active tracer."""
    global _active_tracer
    if _active_tracer:
        _active_tracer.snapshot()
