# Memlyze Development Roadmap

## Vision

Build the fastest, most intuitive visual memory profiler for Python, Node.js, and Rust with <5% overhead.

---

## Phase 1: Python Tracer MVP ✅ **COMPLETE**

**Goal**: Prove the concept with a working Python tracer

**Status**: ✅ Complete (December 2025)

**Deliverables**:
- [x] Binary \.mlyze format specification
- [x] Python memory tracer (tracemalloc wrapper)
- [x] Efficient binary writer (batching, async I/O)
- [x] CLI tool (`Memlyze record`)
- [x] Example programs (5 scenarios)
- [x] Performance benchmarks
- [x] Comprehensive documentation

**Performance**: Target <5% overhead (design supports this)

**What You Can Do Now**:
```bash
Memlyze record python app.py
# Creates trace\.mlyze file
```

---

## Phase 2: Analysis Engine 🚧 **NEXT**

**Goal**: Build Rust-based analyzer to process trace files

**Timeline**: 2-3 weeks

**Key Components**:

### 2.1 Trace Parser
- [ ] Binary format decoder
- [ ] Streaming parser (handle large files)
- [ ] Validation & error recovery
- [ ] Index builder for fast seeking

### 2.2 Timeline Builder
- [ ] Convert event stream to timeline data structure
- [ ] Track allocation/deallocation pairs
- [ ] Compute memory usage over time
- [ ] Calculate peak memory and timestamps

### 2.3 Analysis Algorithms
- [ ] **Leak detection**: Find allocations never freed
- [ ] **Hotspot analysis**: Top allocators by size/count
- [ ] **Lifetime analysis**: Average/max object lifetimes
- [ ] **Churn analysis**: Allocation rate by time window

### 2.4 Query API
```rust
// Example API
let trace = TraceFile::open("trace\.mlyze")?;
let timeline = trace.build_timeline()?;

// Queries
let peak = timeline.peak_memory();
let leaks = timeline.find_leaks(Duration::from_secs(60));
let top = timeline.top_allocators(10);
let at_time = timeline.snapshot_at(Duration::from_secs(5));
```

### 2.5 JSON Export
- [ ] Export timeline as JSON for web UI
- [ ] Pagination support (don't export millions of events)
- [ ] Summary statistics

**Deliverables**:
- Rust library crate (`Memlyze-analyzer`)
- CLI tool (`Memlyze analyze trace\.mlyze`)
- JSON export for web UI
- Unit tests for algorithms
- Performance benchmarks (target: 1M events in <1s)

---

## Phase 3: Web Visualization 🚧 **FUTURE**

**Goal**: Interactive web UI for exploring traces

**Timeline**: 3-4 weeks

**Components**:

### 3.1 Timeline Component
- [ ] Canvas-based rendering (60fps)
- [ ] Level-of-detail (aggregate when zoomed out)
- [ ] Scrubbing with preview
- [ ] Zoom/pan controls
- [ ] Minimap navigation
- [ ] Click to drill down

### 3.2 Heatmap View
- [ ] Treemap showing allocations by function
- [ ] Color by lifetime/size/count
- [ ] Drill-down navigation
- [ ] Filtering and search

### 3.3 Flamegraph View
- [ ] Stack trace visualization
- [ ] Click to zoom into call paths
- [ ] Color by size/count
- [ ] Export as SVG

### 3.4 Object Explorer
- [ ] Details for individual allocations
- [ ] Reference chains (what keeps it alive)
- [ ] Historical view (previous allocations at same address)
- [ ] Code navigation

### 3.5 Code View
- [ ] Syntax highlighting
- [ ] Inline annotations (allocations per line)
- [ ] Jump to definition
- [ ] Filter by file/function

### 3.6 WebAssembly Integration
- [ ] Compile analyzer to WASM
- [ ] Stream processing in Web Worker
- [ ] Shared memory for large datasets
- [ ] Incremental loading

**Tech Stack**:
- React + TypeScript
- Canvas API for rendering
- WebAssembly (Rust analyzer)
- Web Workers for background processing
- Vite for build

**Deliverables**:
- React web application
- WASM-compiled analyzer
- `Memlyze serve trace\.mlyze` command
- Docker image for easy deployment

---

## Phase 4: CLI & Advanced Features 🚧 **FUTURE**

**Goal**: Production-ready tools and advanced analysis

**Timeline**: 2-3 weeks

### 4.1 Terminal UI
- [ ] Interactive TUI (using ratatui)
- [ ] Live updating stats
- [ ] Keyboard navigation (vim-style)
- [ ] Split panes (timeline, details, code)
- [ ] Export commands

### 4.2 Comparison Mode
```bash
Memlyze diff baseline\.mlyze current\.mlyze
# Shows what changed
```
- [ ] Diff two trace files
- [ ] Show allocations that increased/decreased
- [ ] Identify new leaks
- [ ] Regression detection

### 4.3 Report Generation
```bash
Memlyze report trace\.mlyze --format html > report.html
Memlyze report trace\.mlyze --format json > stats.json
Memlyze report trace\.mlyze --format pdf > report.pdf
```

### 4.4 Continuous Profiling
- [ ] Always-on profiling mode (very low overhead)
- [ ] Periodic snapshots
- [ ] Automatic leak detection
- [ ] Alerts and notifications

### 4.5 Export Formats
- [ ] Chrome DevTools format
- [ ] Speedscope format
- [ ] CSV export for spreadsheet analysis

---

## Phase 5: Multi-Language Support 🚧 **FUTURE**

**Goal**: Support Node.js and Rust in addition to Python

**Timeline**: 4-6 weeks

### 5.1 Node.js Support
- [ ] V8 heap profiler integration
- [ ] Native addon (C++)
- [ ] Same \.mlyze format
- [ ] CLI: `Memlyze record node app.js`

### 5.2 Rust Support
- [ ] Global allocator wrapper
- [ ] Macro-based instrumentation
- [ ] Stack unwinding with backtrace
- [ ] CLI: `Memlyze record cargo run`

### 5.3 Language Detection
- [ ] Auto-detect language from command
- [ ] Unified CLI interface
- [ ] Language-specific optimizations

---

## Phase 6: Performance & Optimization 🚧 **FUTURE**

**Goal**: Achieve <2% overhead for all languages

**Timeline**: 2-3 weeks

### 6.1 C Extension for Python
- [ ] Replace hot paths with C
- [ ] Zero-copy stack traces
- [ ] Lock-free queues
- [ ] Memory-mapped I/O

### 6.2 Compression
- [ ] LZ4 compression (5-10x reduction)
- [ ] Block-based (64KB blocks)
- [ ] Index file for random access
- [ ] Streaming decompression

### 6.3 Smart Sampling
- [ ] Adaptive sampling (increase when idle)
- [ ] Size-based sampling (always trace large allocations)
- [ ] Hotspot-aware sampling
- [ ] Statistical guarantees

---

## Phase 7: Reference Chain Analysis 🚧 **ADVANCED**

**Goal**: Understand why objects aren't being freed

**Timeline**: 3-4 weeks

### 7.1 Heap Snapshots
- [ ] Capture full heap state
- [ ] Object graph construction
- [ ] Reference tracking

### 7.2 GC Integration
- [ ] Hook into garbage collector
- [ ] Track object liveness
- [ ] Identify cycles

### 7.3 Root Analysis
- [ ] Find GC roots
- [ ] Path to root for any object
- [ ] Visualize reference chains

---

## Success Metrics

### Technical
- **Overhead**: <5% CPU (Phase 1-4), <2% (Phase 5+)
- **Memory**: <100MB for 1M allocations
- **Trace size**: <1MB per 100k allocations (compressed)
- **Analysis speed**: 1M allocations in <1s
- **UI responsiveness**: 60fps timeline

### User
- **Time to insight**: <2 minutes (install → find leak)
- **Supported languages**: Python ✅, Node.js 🚧, Rust 🚧
- **GitHub stars**: 1k+ in 6 months
- **Production deployments**: 100+ companies

---

## Contributing

Want to help? Areas needing work:

**Phase 2 (Current Priority)**:
- Rust analyzer implementation
- Leak detection algorithm
- Timeline builder
- JSON API design

**Phase 3**:
- UI/UX design
- React components
- Canvas rendering optimization
- WASM integration

**General**:
- Testing on Linux/macOS
- Documentation improvements
- Example applications
- Bug fixes

See `docs/contributing.md` for details!

---

## Timeline Summary

| Phase | Duration | Status |
|-------|----------|--------|
| Phase 1: Python Tracer | 2 weeks | ✅ Complete |
| Phase 2: Analyzer | 2-3 weeks | 🚧 Next |
| Phase 3: Web UI | 3-4 weeks | 🚧 Future |
| Phase 4: CLI & Advanced | 2-3 weeks | 🚧 Future |
| Phase 5: Multi-Language | 4-6 weeks | 🚧 Future |
| Phase 6: Performance | 2-3 weeks | 🚧 Future |
| Phase 7: Ref Chains | 3-4 weeks | 🚧 Future |
| **Total** | **18-25 weeks** | **~6 months** |

---

## Get Involved

- **GitHub**: Star the repo
- **Issues**: Report bugs or request features
- **Discussions**: Share use cases and ideas
- **PRs**: Contributions welcome!

Let's build the best memory profiler together! 🚀

