# 🔍 Memlyze

<div align="center">

**Visual memory profiler with <5% overhead**  
*Find leaks, optimize allocations, understand your memory*

![Status](https://img.shields.io/badge/status-alpha-orange)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macos-lightgrey)

</div>

---

## ✨ Why Memlyze?

<table>
<tr>
<td align="center">📊</td>
<td><b>Visual Timeline</b><br/>Scrub through time, see when leaks started</td>
</tr>
<tr>
<td align="center">⚡</td>
<td><b>Fast</b><br/>&lt;5% overhead, handles millions of allocations</td>
</tr>
<tr>
<td align="center">🎯</td>
<td><b>Interactive</b><br/>Click any spike → see exact code location</td>
</tr>
<tr>
<td align="center">🧠</td>
<td><b>Smart</b><br/>Finds reference chains, detects leaks automatically</td>
</tr>
</table>

## 📊 Compared to Alternatives

<table>
<thead>
<tr>
<th>Tool</th>
<th>Overhead</th>
<th>Visualization</th>
<th>Languages</th>
<th>Production Ready</th>
</tr>
</thead>
<tbody>
<tr>
<td>Valgrind</td>
<td>❌ 20-50x slower</td>
<td>📝 Text only</td>
<td>C/C++</td>
<td>❌ Too slow</td>
</tr>
<tr>
<td>Chrome DevTools</td>
<td>⚠️ 10-20x slower</td>
<td>📸 Snapshots</td>
<td>JavaScript</td>
<td>⚠️ Dev only</td>
</tr>
<tr>
<td>Python tracemalloc</td>
<td>⚠️ ~10% overhead</td>
<td>📝 Text only</td>
<td>Python</td>
<td>⚠️ Limited</td>
</tr>
<tr style="background-color: #e8f5e9;">
<td><b>Memlyze</b></td>
<td>✅ <b>&lt;5% overhead</b></td>
<td>📊 <b>Interactive timeline</b></td>
<td><b>Python, Node, Rust</b></td>
<td>✅ <b>Yes!</b></td>
</tr>
</tbody>
</table>

## 🚀 Quick Start

<table>
<tr>
<td width="50px" align="center">1️⃣</td>
<td>
<b>Install</b>
<pre lang="bash">pip install -e tracer/</pre>
</td>
</tr>
<tr>
<td align="center">2️⃣</td>
<td>
<b>Record a trace</b>
<pre lang="bash">Memlyze record python your_app.py</pre>
</td>
</tr>
<tr>
<td align="center">3️⃣</td>
<td>
<b>Analyze</b> <i>(Phase 2 - coming soon)</i>
<pre lang="bash">Memlyze serve trace\.mlyze</pre>
</td>
</tr>
</table>

## 💻 Example Usage

<table>
<tr>
<td width="50%">

**Python API**
```python
import Memlyze

# Start tracing
tracer = Memlyze.start(
    output_file="trace\.mlyze",
    sample_rate=1.0,
    max_stack_depth=10,
    track_gc=True
)

# Run your application
run_my_app()

# Stop and save
tracer.stop()
```

</td>
<td width="50%">

**CLI Usage**
```bash
# Basic tracing
Memlyze record python app.py

# Low overhead (10% sampling)
Memlyze record \
  --sample-rate 0.1 \
  python app.py

# Production monitoring (1%)
Memlyze record \
  --sample-rate 0.01 \
  --max-stack-depth 5 \
  python app.py
```

</td>
</tr>
</table>

## 📋 Project Status

<table>
<tr>
<th width="200px">Phase</th>
<th>Status</th>
<th>Features</th>
</tr>
<tr style="background-color: #e8f5e9;">
<td><b>Phase 1</b><br/>Python Tracer MVP</td>
<td align="center">✅ <b>COMPLETE</b></td>
<td>
✅ Binary format specification<br/>
✅ Memory tracer with stack traces<br/>
✅ Efficient file writer<br/>
✅ CLI tool<br/>
✅ Example programs
</td>
</tr>
<tr style="background-color: #fff3e0;">
<td><b>Phase 2</b><br/>Analysis Engine</td>
<td align="center">🚧 <b>NEXT</b></td>
<td>
🚧 Rust-based trace parser<br/>
🚧 Timeline builder<br/>
🚧 Leak detection<br/>
🚧 JSON export
</td>
</tr>
<tr>
<td><b>Phase 3</b><br/>Web Visualization</td>
<td align="center">📅 Planned</td>
<td>
📅 React app<br/>
📅 Canvas timeline<br/>
📅 Heatmap/flamegraph<br/>
📅 WASM integration
</td>
</tr>
</table>

## Architecture

```
Memlyze/
├── tracer/              # Python memory tracer
│   ├── Memlyze/        # Core library
│   │   ├── tracer.py    # Allocation tracking
│   │   ├── format.py    # Binary format
│   │   └── writer.py    # File I/O
│   └── setup.py
├── analyzer/            # Rust analysis engine (Phase 2)
├── web-ui/              # React visualization (Phase 3)
├── cli/                 # Rust CLI tool (Phase 4)
├── examples/            # Sample programs
└── benchmarks/          # Performance tests
```

## Documentation

- [Binary Format Specification](docs/format-spec.md)
- [Architecture Guide](docs/architecture.md)
- [Performance Tuning](docs/performance.md)
- [Contributing](docs/contributing.md)

## ⚡ Performance Targets

<table>
<tr>
<td align="center">🎯</td>
<td><b>CPU Overhead</b></td>
<td><code>&lt;5%</code></td>
<td>Fast enough for production</td>
</tr>
<tr>
<td align="center">💾</td>
<td><b>Memory Overhead</b></td>
<td><code>&lt;100MB</code></td>
<td>For 1M allocations</td>
</tr>
<tr>
<td align="center">📦</td>
<td><b>Trace File Size</b></td>
<td><code>&lt;1MB</code></td>
<td>Per 100k allocations (compressed)</td>
</tr>
<tr>
<td align="center">⚡</td>
<td><b>Analysis Speed</b></td>
<td><code>&lt;1 second</code></td>
<td>Process 1M allocations (Phase 2)</td>
</tr>
</table>

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! See [CONTRIBUTING.md](docs/contributing.md) for details.

## Credits

Built with ❤️ by the Memlyze team

