# Memlyze Examples

This directory contains example programs to test and demonstrate Memlyze.

## Examples

### 01_leak_simulation.py
Intentionally leaks memory by keeping references to large objects.
Perfect for testing leak detection algorithms.

**Run:**
```bash
Memlyze record python 01_leak_simulation.py
```

### 02_fibonacci.py
Recursive fibonacci with memory allocations at each call.
Tests stack trace capturing with deep call stacks.

**Run:**
```bash
Memlyze record python 02_fibonacci.py
```

### 03_large_allocations.py
Allocates large blocks of memory (1MB to 100MB).
Tests handling of large allocations and proper deallocation tracking.

**Run:**
```bash
Memlyze record python 03_large_allocations.py
```

### 04_many_small_allocations.py
Creates thousands of small allocations quickly.
Tests high allocation rate handling and sampling.

**Run:**
```bash
Memlyze record python 04_many_small_allocations.py
# Or with sampling:
Memlyze record --sample-rate 0.1 python 04_many_small_allocations.py
```

### 05_realistic_app.py
Simulates a realistic application with:
- User object creation
- Cache management
- API request handling
- Mixed allocation patterns

**Run:**
```bash
Memlyze record python 05_realistic_app.py
```

## Usage

All examples can be run with Memlyze using the pattern:

```bash
# Install Memlyze first
cd ../tracer
pip install -e .

# Then run examples
cd ../examples
Memlyze record python <example_name>.py
```

This will create a `trace\.mlyze` file that can be analyzed (in Phase 2+).

## What to Look For

When analyzing traces:
- **Leak simulation**: Look for allocations that never get freed
- **Fibonacci**: Deep stack traces showing recursive calls
- **Large allocations**: Memory spikes and proper deallocation
- **Many small**: High allocation rate, effect of sampling
- **Realistic app**: Mixed patterns, cache behavior

## Next Steps

Once Phase 2 (analyzer) is complete, you'll be able to:
```bash
Memlyze analyze trace\.mlyze
Memlyze serve trace\.mlyze
```

