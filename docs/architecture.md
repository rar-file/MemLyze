# Memlyze Architecture

## System Overview

Memlyze consists of four main components:

```
┌─────────────────────────────────────────────────────────────┐
│                     Your Application                         │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              1. Memory Tracer (Python/C)                     │
│  • Hooks into allocator                                      │
│  • Captures stack traces                                     │
│  • Writes to \.mlyze file                                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼ \.mlyze file
┌─────────────────────────────────────────────────────────────┐
│           2. Analysis Engine (Rust/WASM)                     │
│  • Parses trace files                                        │
│  • Builds timeline                                           │
│  • Detects leaks                                             │
│  • Finds hotspots                                            │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼ JSON API
┌─────────────────────────────────────────────────────────────┐
│          3. Web Visualization (React + Canvas)               │
│  • Interactive timeline                                      │
│  • Heatmaps & flamegraphs                                    │
│  • Code navigation                                           │
└─────────────────────────────────────────────────────────────┘
                        ▲
                        │
┌───────────────────────┴─────────────────────────────────────┐
│              4. CLI Tool (Rust)                              │
│  • Memlyze record                                           │
│  • Memlyze analyze                                          │
│  • Memlyze serve                                            │
└─────────────────────────────────────────────────────────────┘
```

## Component 1: Memory Tracer

### Design Goals
- **<5% overhead**: Fast enough for production use
- **Zero external dependencies**: Pure Python + stdlib
- **Sampling support**: Handle high allocation rates
- **Ring buffer**: Prevent memory explosion

### Implementation

**Language**: Python 3.8+ (with optional C extension in Phase 1.5)

**Key Classes**:

```python
MemoryTracer
├── format: TraceFormat          # Binary encoding
├── writer: TraceWriter           # Async I/O
├── snapshot_thread: Thread       # Periodic snapshots
└── stats: dict                   # Runtime statistics
```

### Data Flow

```
Python App Allocates
        ↓
tracemalloc captures
        ↓
MemoryTracer.snapshot()
        ↓
Diff with previous snapshot
        ↓
For each allocation:
  - Apply sampling
  - Get stack trace
  - Deduplicate via TraceFormat
  - Encode to bytes
        ↓
TraceWriter.write_event()
        ↓
Queue event (ring buffer)
        ↓
Background thread batches writes
        ↓
Flush to \.mlyze file
```

### Optimization Strategies

1. **Stack Trace Caching**
   ```python
   # Cache stack trace IDs
   cache_key = tuple(stack_frames)
   if cache_key in cache:
       return cached_id
   ```

2. **Batched Writes**
   ```python
   # Don't write on every allocation
   buffer = []
   while len(buffer) < BATCH_SIZE:
       buffer.append(event)
   file.write(b''.join(buffer))
   ```

3. **Sampling**
   ```python
   # Only trace 1 in N allocations
   if allocation_count % sample_rate != 0:
       return  # Skip this allocation
   ```

4. **Ring Buffer**
   ```python
   # Limit memory usage
   queue = deque(maxlen=MAX_EVENTS)
   queue.append(event)  # Auto-drops oldest
   ```

## Component 2: Analysis Engine

### Design Goals
- **Fast**: Process 1M allocations in <1 second
- **Memory efficient**: Stream processing where possible
- **Queryable**: Support range queries, aggregations

### Implementation

**Language**: Rust (compiles to WASM for web)

**Architecture**:

```rust
pub struct TraceAnalyzer {
    metadata: Metadata,
    timeline: Timeline,
    index: EventIndex,
}

pub struct Timeline {
    events: Vec<Event>,
    allocations: HashMap<u64, Allocation>,
    time_index: BTreeMap<u64, Vec<usize>>,
}
```

### Algorithms

#### 1. Timeline Builder

```rust
fn build_timeline(events: &[Event]) -> Timeline {
    let mut allocations = HashMap::new();
    let mut current_time = 0;
    
    for event in events {
        current_time += event.timestamp_delta;
        
        match event.event_type {
            EventType::Alloc => {
                allocations.insert(event.address, Allocation {
                    size: event.size,
                    allocated_at: current_time,
                    freed_at: None,
                    stack_id: event.stack_id,
                });
            }
            EventType::Free => {
                if let Some(alloc) = allocations.get_mut(&event.address) {
                    alloc.freed_at = Some(current_time);
                }
            }
        }
    }
    
    Timeline { allocations, ... }
}
```

#### 2. Leak Detection

```rust
fn find_leaks(timeline: &Timeline, min_lifetime: Duration) -> Vec<Leak> {
    let now = timeline.end_time;
    
    timeline.allocations
        .values()
        .filter(|a| a.freed_at.is_none())  // Never freed
        .filter(|a| now - a.allocated_at > min_lifetime)  // Old enough
        .map(|a| Leak::from(a))
        .collect()
}
```

#### 3. Hotspot Analysis

```rust
fn find_hotspots(timeline: &Timeline) -> Vec<Hotspot> {
    let mut by_stack = HashMap::new();
    
    for alloc in timeline.allocations.values() {
        let entry = by_stack.entry(alloc.stack_id).or_insert(Hotspot::default());
        entry.total_bytes += alloc.size;
        entry.count += 1;
    }
    
    let mut hotspots: Vec<_> = by_stack.into_values().collect();
    hotspots.sort_by_key(|h| h.total_bytes);
    hotspots.reverse();
    hotspots
}
```

### Query API

```rust
impl TraceAnalyzer {
    // Time-based queries
    pub fn at_time(&self, t: u64) -> Snapshot;
    pub fn range(&self, start: u64, end: u64) -> Vec<Event>;
    
    // Aggregations
    pub fn total_allocated(&self) -> u64;
    pub fn peak_memory(&self) -> (u64, u64);  // (time, bytes)
    pub fn allocation_rate(&self, window: Duration) -> f64;
    
    // Analysis
    pub fn find_leaks(&self, min_lifetime: Duration) -> Vec<Leak>;
    pub fn top_allocators(&self, n: usize) -> Vec<Hotspot>;
    pub fn reference_chains(&self, addr: u64) -> Vec<RefChain>;
}
```

## Component 3: Web Visualization

### Design Goals
- **Interactive**: 60fps scrubbing
- **Scalable**: Handle millions of allocations
- **Intuitive**: Click to drill down

### Architecture

```
React App
├── TimelineView
│   └── Canvas renderer (Level-of-detail)
├── HeatmapView
│   └── Treemap (proportional sizes)
├── FlamegraphView
│   └── Stack trace visualization
├── ObjectExplorer
│   └── Individual allocation details
└── CodeView
    └── Source code with annotations
```

### Level-of-Detail Rendering

```typescript
function renderTimeline(data: Event[], zoom: number) {
    if (zoom < 0.1) {
        // Zoomed out: show aggregated buckets
        const buckets = aggregateIntoBuckets(data, bucketSize = 1000);
        renderBuckets(buckets);
    } else {
        // Zoomed in: show individual events
        const visible = getVisibleEvents(data, viewport);
        renderEvents(visible);
    }
}
```

### WebAssembly Integration

```typescript
import init, { TraceAnalyzer } from './analyzer.wasm';

await init();

// Load trace in Web Worker
const worker = new Worker('analyzer-worker.js');
worker.postMessage({ file: traceFile });

worker.onmessage = (e) => {
    if (e.data.type === 'timeline') {
        updateTimeline(e.data.timeline);
    }
};
```

## Component 4: CLI Tool

### Commands

```bash
# Recording
Memlyze record python app.py
Memlyze record --sample-rate 0.1 node server.js

# Analysis
Memlyze analyze trace\.mlyze
  # Opens TUI with:
  # - Live stats
  # - Top allocators
  # - Leak list

# Reporting
Memlyze report trace\.mlyze --format html > report.html
Memlyze report trace\.mlyze --format json > stats.json

# Web UI
Memlyze serve trace\.mlyze --port 8080
  # Starts local server
  # Opens browser to http://localhost:8080

# Comparison
Memlyze diff baseline\.mlyze current\.mlyze
  # Shows allocations that increased/decreased
```

### Terminal UI (using ratatui)

```
┌─ Memlyze Analysis ─────────────────────────────────────────────┐
│ File: trace\.mlyze                     Duration: 10.5s           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Memory Usage                                                     │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │                                  ▲                          │ │
│ │                                ▲ █                          │ │
│ │                       ▲       █  █        ▲                 │ │
│ │          ▲    ▂▄▆█   █    ▂▄▆█  █    ▂▄▆█                  │ │
│ │ ─────────█────█████───█────█████──█────█████──────────────  │ │
│ └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ Top Allocators:                                                  │
│   1. process_data (app.py:42)        10.5 MB  (45.2%)          │
│   2. load_config (config.py:15)       8.2 MB  (35.3%)          │
│   3. create_cache (cache.py:88)       4.5 MB  (19.4%)          │
│                                                                  │
│ Potential Leaks: 3 found                                         │
│   • 1.2 MB in process_data (alive 8.5s)                         │
│   • 0.8 MB in create_cache (alive 7.2s)                         │
│                                                                  │
│ [↑/↓] Navigate  [Enter] Details  [q] Quit                       │
└──────────────────────────────────────────────────────────────────┘
```

## Data Flow Example

User runs: `Memlyze record python app.py`

1. **CLI** wraps execution:
   ```python
   tracer = Memlyze.start("trace\.mlyze")
   exec(app_code)
   tracer.stop()
   ```

2. **Tracer** captures allocations:
   - Hooks into tracemalloc
   - Takes periodic snapshots
   - Writes events to trace\.mlyze

3. User runs: `Memlyze serve trace\.mlyze`

4. **CLI** starts web server:
   - Loads analyzer (Rust/WASM)
   - Parses trace file
   - Serves React app

5. **Web UI** renders:
   - Timeline shows memory over time
   - User clicks spike
   - Shows stack trace at that time
   - Highlights code in CodeView

## Performance Characteristics

| Component | Operation | Time | Memory |
|-----------|-----------|------|--------|
| Tracer | Record 1M allocs | 1-2s | <100MB |
| Analyzer | Parse 1M allocs | <1s | ~200MB |
| Web UI | Render timeline | 16ms (60fps) | ~50MB |
| CLI | TUI update | <10ms | ~100MB |

## Error Handling

### Tracer
- **Ring buffer full**: Drop oldest events (log warning)
- **Disk full**: Stop tracing gracefully, save partial trace
- **Exception in callback**: Log but don't crash app

### Analyzer
- **Corrupt trace file**: Skip bad events, parse what's valid
- **Unknown event type**: Skip (forward compatibility)
- **Missing metadata**: Use default values

### Web UI
- **Large trace file**: Show loading progress, stream in chunks
- **Browser memory limit**: Enable virtual scrolling
- **WASM not supported**: Fall back to JS implementation

## Testing Strategy

### Unit Tests
- Format encoding/decoding
- Timeline builder correctness
- Leak detection accuracy

### Integration Tests
- End-to-end: record → analyze → visualize
- Multi-threaded apps
- Large traces (10M+ allocations)

### Performance Tests
- Overhead measurement
- Analyzer throughput
- UI responsiveness

## Future Enhancements

### Phase 1.5: C Extension
Replace Python tracer with C extension for even lower overhead (<2%)

### Phase 2+
- Node.js support
- Rust support
- Reference chain analysis
- Heap snapshots
- Comparison mode
- Export to Chrome DevTools format

