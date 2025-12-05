# Memlyze Binary Format Specification

Version: 1.0

## Overview

The `\.mlyze` format is a binary file format designed for efficient storage of memory allocation traces. It prioritizes:
- **Compactness**: Variable-length encoding for integers
- **Speed**: Sequential write/read patterns
- **Deduplication**: Stack traces and strings stored once
- **Streaming**: Can be written and read incrementally

## File Structure

```
┌─────────────────────────────────────┐
│         Header (256 bytes)          │
├─────────────────────────────────────┤
│      Metadata (JSON, variable)      │
├─────────────────────────────────────┤
│                                     │
│        Event Stream (variable)      │
│                                     │
│  ┌──────────────────────────────┐  │
│  │ Event 1 (ALLOC)              │  │
│  ├──────────────────────────────┤  │
│  │ Event 2 (ALLOC)              │  │
│  ├──────────────────────────────┤  │
│  │ Event 3 (FREE)               │  │
│  ├──────────────────────────────┤  │
│  │ Event 4 (GC)                 │  │
│  ├──────────────────────────────┤  │
│  │ ...                          │  │
│  └──────────────────────────────┘  │
│                                     │
└─────────────────────────────────────┘
```

## Header Format (256 bytes)

| Offset | Size | Type   | Description                    |
|--------|------|--------|--------------------------------|
| 0      | 4    | char[] | Magic bytes: "MTRC"            |
| 4      | 4    | uint32 | Format version (1)             |
| 8      | 8    | uint64 | Start timestamp (microseconds) |
| 16     | 4    | uint32 | Metadata length in bytes       |
| 20     | 236  | -      | Reserved (padding)             |

The header is always exactly 256 bytes, with unused space reserved for future extensions.

## Metadata Section (JSON)

Immediately follows the header. Contains:

```json
{
  "stack_traces": {
    "0": [
      {"file_id": 0, "line": 42, "func_id": 0},
      {"file_id": 1, "line": 123, "func_id": 1}
    ],
    "1": [...]
  },
  "files": {
    "0": "/path/to/file.py",
    "1": "/path/to/other.py"
  },
  "functions": {
    "0": "main",
    "1": "process_data"
  }
}
```

**Purpose**: Deduplicate common data. Stack traces, file paths, and function names are stored once and referenced by ID in events.

## Event Stream

Events are written sequentially with variable-length encoding.

### Event Types

| Value | Name   | Description              |
|-------|--------|--------------------------|
| 0     | ALLOC  | Memory allocation        |
| 1     | FREE   | Memory deallocation      |
| 2     | GC     | Garbage collection event |
| 3     | MARKER | Custom annotation        |

### ALLOC Event

```
┌─────────┬────────────┬─────────┬──────┬──────────┬───────────┐
│ Type(1) │ Delta(var) │ Addr(8) │ Size │ Stack ID │ Thread(2) │
│  = 0    │            │         │(var) │  (var)   │           │
└─────────┴────────────┴─────────┴──────┴──────────┴───────────┘
```

- **Type**: uint8 = 0
- **Delta**: varint (microseconds since last event)
- **Address**: uint64 (memory address)
- **Size**: varint (bytes allocated)
- **Stack ID**: varint (references metadata.stack_traces)
- **Thread**: uint16 (thread identifier)

**Total size**: 12-30 bytes (depending on varint values)

### FREE Event

```
┌─────────┬────────────┬─────────┐
│ Type(1) │ Delta(var) │ Addr(8) │
│  = 1    │            │         │
└─────────┴────────────┴─────────┘
```

- **Type**: uint8 = 1
- **Delta**: varint (microseconds since last event)
- **Address**: uint64 (memory address being freed)

**Total size**: 10-15 bytes

### GC Event

```
┌─────────┬────────────┬─────────────┬──────────────┐
│ Type(1) │ Delta(var) │ Objects(var)│ Bytes(var)   │
│  = 2    │            │             │              │
└─────────┴────────────┴─────────────┴──────────────┘
```

- **Type**: uint8 = 2
- **Delta**: varint (microseconds since last event)
- **Objects**: varint (number of objects collected)
- **Bytes**: varint (bytes freed)

**Total size**: 4-20 bytes

### MARKER Event

```
┌─────────┬────────────┬───────────┐
│ Type(1) │ Delta(var) │ Name(var) │
│  = 3    │            │           │
└─────────┴────────────┴───────────┘
```

- **Type**: uint8 = 3
- **Delta**: varint (microseconds since last event)
- **Name ID**: varint (references metadata.functions)

**Total size**: 3-10 bytes

## Variable-Length Integer Encoding (Varint)

Uses the same encoding as Protocol Buffers:

- 7 bits of each byte store data
- Bit 8 indicates if more bytes follow (1 = continue, 0 = last byte)
- Little-endian

**Examples:**
- `0` → `0x00` (1 byte)
- `127` → `0x7F` (1 byte)
- `128` → `0x80 0x01` (2 bytes)
- `16,384` → `0x80 0x80 0x01` (3 bytes)

**Benefits:**
- Small numbers (common) use 1 byte
- Large numbers automatically use more bytes
- Average size reduction: 60-70% for typical traces

## Compression (Future Enhancement)

In Phase 2, add optional LZ4 compression:

1. Split event stream into 64KB blocks
2. Compress each block independently
3. Create index file (\.mlyze.idx) mapping offsets
4. Allows random access while compressed

## File Size Estimates

**Uncompressed:**
- Average ALLOC event: ~20 bytes
- Average FREE event: ~12 bytes
- 1 million allocations: ~32 MB

**With compression (Phase 2):**
- Expected ratio: 5:1 to 10:1
- 1 million allocations: ~3-6 MB

## Reading Algorithm

```python
def read_trace(filepath):
    with open(filepath, 'rb') as f:
        # 1. Read header
        header = f.read(256)
        magic, version, start_time, metadata_len = parse_header(header)
        
        # 2. Read metadata
        metadata_json = f.read(metadata_len)
        metadata = json.loads(metadata_json)
        
        # 3. Stream events
        while True:
            event_type = read_byte(f)
            if event_type is None:
                break
            
            timestamp_delta = read_varint(f)
            
            if event_type == ALLOC:
                address = read_uint64(f)
                size = read_varint(f)
                stack_id = read_varint(f)
                thread_id = read_uint16(f)
                yield AllocEvent(...)
            
            elif event_type == FREE:
                address = read_uint64(f)
                yield FreeEvent(...)
            
            # ... handle other event types
```

## Validation

Valid `\.mlyze` files must:
1. Start with magic bytes "MTRC"
2. Have supported version number
3. Have valid metadata JSON
4. All stack_id/file_id/func_id references exist in metadata
5. Event stream contains only valid event types
6. Varints are properly encoded
7. File size matches header + metadata + events

## Compatibility

- **Backwards compatible**: Version 1 readers can read version 1 files
- **Forward compatible**: When reading newer versions, unknown event types should be skipped gracefully
- **Cross-platform**: All integers are fixed endianness (little-endian)

## Future Extensions

Potential additions without breaking compatibility:

1. **Compression flag** (use reserved header bytes)
2. **Checksum** for data integrity
3. **Object type tracking** (new event type 4)
4. **Reference chains** (new event type 5)
5. **Heap snapshots** (new event type 6)

Reserved header space (236 bytes) allows adding fields without changing file format version.

