# Quick Start Guide

Get started with Memlyze in 5 minutes!

## Installation

```bash
cd tracer
pip install -e .
```

## Step 1: Create a Test Program

Create `my_app.py`:

```python
import time

def process_data():
    # Simulate some allocations
    data = []
    for i in range(1000):
        data.append(bytearray(1024))  # 1KB each
        time.sleep(0.001)
    return data

def main():
    print("Starting application...")
    result = process_data()
    print(f"Processed {len(result)} items")
    # Note: result is still referenced, so memory not freed yet

if __name__ == "__main__":
    main()
```

## Step 2: Record a Trace

```bash
Memlyze record python my_app.py
```

You'll see output like:
```
Memlyze: Started tracing to trace\.mlyze
  Sample rate: 1.0
  Max stack depth: 10
  Track GC: True
Starting application...
Processed 1000 items

Memlyze: Stopped tracing
  Trace file: trace\.mlyze
  Allocations tracked: 1,234
  Events written: 2,468
  Bytes written: 45,678
  Duration: 2.5s
```

## Step 3: Inspect the Trace File

```bash
# Check file size
ls -lh trace\.mlyze

# View binary content (first 256 bytes = header)
hexdump -C trace\.mlyze | head -20
```

You should see the magic bytes `MTRC` at the start!

## Step 4: Try Different Options

### Sampling (for high-performance)
```bash
Memlyze record --sample-rate 0.1 python my_app.py
```
Only traces 10% of allocations - much lower overhead!

### Reduce Stack Depth
```bash
Memlyze record --max-stack-depth 5 python my_app.py
```
Faster, but less context.

### Disable GC Tracking
```bash
Memlyze record --no-track-gc python my_app.py
```
Slightly lower overhead.

## Step 5: Try the Examples

```bash
cd ../examples

# Memory leak simulation
Memlyze record python 01_leak_simulation.py

# Deep recursion
Memlyze record python 02_fibonacci.py

# Large allocations
Memlyze record python 03_large_allocations.py

# Many small allocations
Memlyze record python 04_many_small_allocations.py

# Realistic application
Memlyze record python 05_realistic_app.py
```

## Step 6: Measure Overhead

```bash
cd ../benchmarks

# Run without tracing (baseline)
python benchmark_overhead.py

# Run with tracing
Memlyze record python benchmark_overhead.py

# Compare the times to see overhead
```

## Step 7: Use Programmatic API

You can also use Memlyze from code:

```python
import Memlyze
import time

# Start tracing
tracer = Memlyze.start(
    output_file="my_trace\.mlyze",
    sample_rate=1.0,
    max_stack_depth=10,
    track_gc=True
)

# Add markers
Memlyze.mark("Starting Phase 1")

# Your code here
data = [i for i in range(100000)]

Memlyze.mark("Starting Phase 2")

# More code
result = sum(data)

# Take a snapshot (processes allocations so far)
Memlyze.snapshot()

# Stop tracing
tracer.stop()
```

## What's Next?

- **Phase 2** (coming soon): Analyzer to process trace files
- **Phase 3** (coming soon): Web UI to visualize traces
- **Phase 4** (coming soon): Advanced features

For now, you can:
1. Inspect trace files with hex viewers
2. Compare trace file sizes
3. Measure overhead on your applications
4. Help contribute to Phase 2!

## Troubleshooting

### Command not found: Memlyze

Make sure you installed the package:
```bash
cd tracer
pip install -e .
```

### ImportError: No module named 'Memlyze'

You need to install the package first (see above).

### High overhead (>5%)

Try reducing sample rate:
```bash
Memlyze record --sample-rate 0.1 python app.py
```

See [docs/performance.md](docs/performance.md) for detailed tuning.

### Trace file is huge

This is normal for apps with many allocations. Try:
- Lower sample rate: `--sample-rate 0.1`
- Shorter runs
- Compression (Phase 2 feature)

## Getting Help

- Read the [documentation](docs/)
- Check [examples](examples/)
- File an [issue](https://github.com/yourusername/Memlyze/issues)

Happy tracing! 🔍

