"""
Binary trace format specification for .mtrace files.

Format:
    Header (256 bytes):
        - Magic: "MTRC" (4 bytes)
        - Version: uint32
        - Start timestamp: uint64 (microseconds since epoch)
        - Metadata length: uint32
        - Reserved: padding to 256 bytes
        - Metadata: JSON (stack traces, file paths, etc.)
    
    Event Stream:
        Each event is variable length:
        - Event type: uint8
        - Timestamp delta: varint
        - Payload (depends on type)
"""

import struct
import json
from enum import IntEnum
from typing import Dict, Any, Optional, List, Tuple
import time


class EventType(IntEnum):
    """Event types in trace stream."""
    ALLOC = 0
    FREE = 1
    GC = 2
    MARKER = 3


class TraceFormat:
    """Handles encoding/decoding of .mtrace binary format."""
    
    MAGIC = b"MTRC"
    VERSION = 1
    HEADER_SIZE = 256
    
    def __init__(self):
        self.metadata: Dict[str, Any] = {
            "stack_traces": {},  # id -> stack trace info
            "files": {},         # id -> file path
            "functions": {},     # id -> function name
        }
        self.next_stack_id = 0
        self.next_file_id = 0
        self.next_func_id = 0
        self.stack_cache: Dict[Tuple, int] = {}  # Cache for deduplication
        
    def create_header(self, start_timestamp: float) -> bytes:
        """Create trace file header."""
        # Convert timestamp to microseconds
        start_us = int(start_timestamp * 1_000_000)
        
        # Serialize metadata to JSON
        metadata_json = json.dumps(self.metadata).encode('utf-8')
        metadata_len = len(metadata_json)
        
        # Build header
        header = bytearray(self.HEADER_SIZE)
        struct.pack_into('4sIQ', header, 0, 
                        self.MAGIC, 
                        self.VERSION, 
                        start_us)
        struct.pack_into('I', header, 16, metadata_len)
        
        return bytes(header) + metadata_json
    
    def encode_varint(self, value: int) -> bytes:
        """Encode integer as varint (variable-length encoding)."""
        result = bytearray()
        while value > 127:
            result.append((value & 0x7F) | 0x80)
            value >>= 7
        result.append(value & 0x7F)
        return bytes(result)
    
    def decode_varint(self, data: bytes, offset: int) -> Tuple[int, int]:
        """Decode varint from data at offset. Returns (value, new_offset)."""
        value = 0
        shift = 0
        pos = offset
        
        while True:
            byte = data[pos]
            value |= (byte & 0x7F) << shift
            pos += 1
            if (byte & 0x80) == 0:
                break
            shift += 7
            
        return value, pos
    
    def get_or_create_stack_id(self, stack_trace: List[Tuple[str, int, str]]) -> int:
        """
        Get or create ID for a stack trace.
        
        Args:
            stack_trace: List of (filename, lineno, function_name) tuples
            
        Returns:
            Stack trace ID
        """
        # Create cache key
        cache_key = tuple(stack_trace)
        
        if cache_key in self.stack_cache:
            return self.stack_cache[cache_key]
        
        # Create new stack trace entry
        stack_id = self.next_stack_id
        self.next_stack_id += 1
        
        # Store in metadata with file/function IDs
        frames = []
        for filename, lineno, funcname in stack_trace:
            file_id = self._get_or_create_file_id(filename)
            func_id = self._get_or_create_func_id(funcname)
            frames.append({
                "file_id": file_id,
                "line": lineno,
                "func_id": func_id
            })
        
        self.metadata["stack_traces"][str(stack_id)] = frames
        self.stack_cache[cache_key] = stack_id
        
        return stack_id
    
    def _get_or_create_file_id(self, filename: str) -> int:
        """Get or create ID for a filename."""
        # Check if already exists
        for fid, fname in self.metadata["files"].items():
            if fname == filename:
                return int(fid)
        
        # Create new
        file_id = self.next_file_id
        self.next_file_id += 1
        self.metadata["files"][str(file_id)] = filename
        return file_id
    
    def _get_or_create_func_id(self, funcname: str) -> int:
        """Get or create ID for a function name."""
        # Check if already exists
        for fid, fname in self.metadata["functions"].items():
            if fname == funcname:
                return int(fid)
        
        # Create new
        func_id = self.next_func_id
        self.next_func_id += 1
        self.metadata["functions"][str(func_id)] = funcname
        return func_id
    
    def encode_alloc_event(self, 
                          timestamp_delta: int,
                          address: int, 
                          size: int,
                          stack_id: int,
                          thread_id: int) -> bytes:
        """
        Encode an allocation event.
        
        Args:
            timestamp_delta: Microseconds since last event
            address: Memory address
            size: Allocation size in bytes
            stack_id: Stack trace ID
            thread_id: Thread ID
        """
        result = bytearray()
        
        # Event type
        result.append(EventType.ALLOC)
        
        # Timestamp delta (varint)
        result.extend(self.encode_varint(timestamp_delta))
        
        # Address (uint64)
        result.extend(struct.pack('Q', address))
        
        # Size (varint)
        result.extend(self.encode_varint(size))
        
        # Stack trace ID (varint)
        result.extend(self.encode_varint(stack_id))
        
        # Thread ID (uint16)
        result.extend(struct.pack('H', thread_id))
        
        return bytes(result)
    
    def encode_free_event(self, timestamp_delta: int, address: int) -> bytes:
        """
        Encode a deallocation event.
        
        Args:
            timestamp_delta: Microseconds since last event
            address: Memory address being freed
        """
        result = bytearray()
        
        # Event type
        result.append(EventType.FREE)
        
        # Timestamp delta (varint)
        result.extend(self.encode_varint(timestamp_delta))
        
        # Address (uint64)
        result.extend(struct.pack('Q', address))
        
        return bytes(result)
    
    def encode_gc_event(self, 
                       timestamp_delta: int,
                       objects_collected: int,
                       bytes_freed: int) -> bytes:
        """
        Encode a garbage collection event.
        
        Args:
            timestamp_delta: Microseconds since last event
            objects_collected: Number of objects collected
            bytes_freed: Total bytes freed
        """
        result = bytearray()
        
        # Event type
        result.append(EventType.GC)
        
        # Timestamp delta (varint)
        result.extend(self.encode_varint(timestamp_delta))
        
        # Objects collected (varint)
        result.extend(self.encode_varint(objects_collected))
        
        # Bytes freed (varint)
        result.extend(self.encode_varint(bytes_freed))
        
        return bytes(result)
    
    def encode_marker_event(self, timestamp_delta: int, name: str) -> bytes:
        """
        Encode a marker/annotation event.
        
        Args:
            timestamp_delta: Microseconds since last event
            name: Marker name
        """
        result = bytearray()
        
        # Event type
        result.append(EventType.MARKER)
        
        # Timestamp delta (varint)
        result.extend(self.encode_varint(timestamp_delta))
        
        # Get or create name ID
        name_id = self._get_or_create_func_id(name)  # Reuse function ID system
        
        # Name ID (varint)
        result.extend(self.encode_varint(name_id))
        
        return bytes(result)
    
    @staticmethod
    def parse_header(data: bytes) -> Tuple[Dict[str, Any], int]:
        """
        Parse trace file header.
        
        Returns:
            (metadata_dict, offset_to_event_stream)
        """
        # Check magic
        magic = data[0:4]
        if magic != TraceFormat.MAGIC:
            raise ValueError(f"Invalid magic bytes: {magic}")
        
        # Parse header
        version, start_us = struct.unpack_from('IQ', data, 4)
        metadata_len = struct.unpack_from('I', data, 16)[0]
        
        # Parse metadata JSON
        metadata_start = TraceFormat.HEADER_SIZE
        metadata_end = metadata_start + metadata_len
        metadata_json = data[metadata_start:metadata_end]
        metadata = json.loads(metadata_json.decode('utf-8'))
        
        return metadata, metadata_end
