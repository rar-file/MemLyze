"""
Efficient trace file writer with batching and compression.
"""

import io
import threading
from typing import Optional
from collections import deque
import time


class TraceWriter:
    """
    Writes trace events to disk efficiently.
    
    Features:
    - Batched writes (don't flush on every event)
    - Background thread for async I/O
    - Ring buffer to prevent memory explosion
    """
    
    def __init__(self, 
                 filepath: str,
                 buffer_size: int = 64 * 1024,  # 64KB buffer
                 max_queue_size: int = 10000):
        """
        Initialize trace writer.
        
        Args:
            filepath: Path to output .mtrace file
            buffer_size: Size of write buffer in bytes
            max_queue_size: Maximum events in queue (ring buffer)
        """
        self.filepath = filepath
        self.buffer_size = buffer_size
        self.max_queue_size = max_queue_size
        
        self.file: Optional[io.BufferedWriter] = None
        self.buffer = bytearray()
        self.queue: deque = deque(maxlen=max_queue_size)
        self.lock = threading.Lock()
        self.writer_thread: Optional[threading.Thread] = None
        self.should_stop = threading.Event()
        self.events_written = 0
        self.bytes_written = 0
        self.events_dropped = 0
        
    def open(self, header: bytes):
        """Open file and write header."""
        self.file = open(self.filepath, 'wb')
        self.file.write(header)
        self.bytes_written += len(header)
        
        # Start background writer thread
        self.should_stop.clear()
        self.writer_thread = threading.Thread(target=self._writer_loop, daemon=True)
        self.writer_thread.start()
    
    def write_event(self, event_data: bytes):
        """
        Queue an event for writing.
        
        Args:
            event_data: Encoded event bytes
        """
        with self.lock:
            if len(self.queue) >= self.max_queue_size:
                # Ring buffer is full, drop oldest event
                self.queue.popleft()
                self.events_dropped += 1
            
            self.queue.append(event_data)
    
    def _writer_loop(self):
        """Background thread that flushes events to disk."""
        while not self.should_stop.is_set():
            # Get events from queue
            events_to_write = []
            with self.lock:
                while self.queue and len(events_to_write) < 1000:  # Batch up to 1000 events
                    events_to_write.append(self.queue.popleft())
            
            if events_to_write:
                # Write batch
                for event_data in events_to_write:
                    self.buffer.extend(event_data)
                    self.events_written += 1
                    
                    # Flush if buffer is full
                    if len(self.buffer) >= self.buffer_size:
                        self._flush_buffer()
            else:
                # No events, sleep briefly
                time.sleep(0.001)  # 1ms
    
    def _flush_buffer(self):
        """Flush buffer to disk."""
        if self.file and self.buffer:
            self.file.write(self.buffer)
            self.bytes_written += len(self.buffer)
            self.buffer.clear()
    
    def close(self):
        """Close file and stop background thread."""
        # Signal thread to stop
        self.should_stop.set()
        
        # Wait for thread to finish
        if self.writer_thread:
            self.writer_thread.join(timeout=5.0)
        
        # Flush any remaining events
        with self.lock:
            while self.queue:
                event_data = self.queue.popleft()
                self.buffer.extend(event_data)
                self.events_written += 1
        
        # Final flush
        self._flush_buffer()
        
        # Close file
        if self.file:
            self.file.close()
            self.file = None
    
    def get_stats(self) -> dict:
        """Get writer statistics."""
        return {
            "events_written": self.events_written,
            "events_dropped": self.events_dropped,
            "bytes_written": self.bytes_written,
            "queue_size": len(self.queue),
        }
