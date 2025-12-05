# Performance Tuning Guide

How to optimize Memlyze for different workloads and achieve <5% overhead.

## Understanding Overhead

Memlyze overhead comes from:

1. **Stack trace collection** (~60% of overhead)
2. **Event encoding** (~20% of overhead)
3. **I/O operations** (~15% of overhead)
4. **Synchronization** (~5% of overhead)

## Quick Tuning Guide

### Low Overhead (< 5%) - Default
```bash
Memlyze record python app.py
```
Good for: Most applications

### Ultra-Low Overhead (< 2%)
```bash
Memlyze record \
    --sample-rate 0.1 \
    --max-stack-depth 5 \
    --no-track-gc \
    python app.py
```
Good for: Production monitoring, high-performance apps

### Maximum Detail
```bash
Memlyze record \
    --sample-rate 1.0 \
    --max-stack-depth 25 \
    --track-gc \
    python app.py
```
Good for: Debugging specific issues, development

## Option Reference

### --sample-rate

Controls what fraction of allocations to trace.

| Value | Behavior | Overhead | Use Case |
|-------|----------|----------|----------|
| 1.0 | Trace everything | ~5% | Default, development |
| 0.5 | Trace 50% | ~3% | Reduce overhead slightly |
| 0.1 | Trace 10% | ~1% | Production monitoring |
| 0.01 | Trace 1% | <0.5% | Always-on profiling |

**How it works**: Uses deterministic sampling based on allocation count.

```python
# Every Nth allocation is traced
if allocation_count % (1 / sample_rate) == 0:
    trace_this_allocation()
```

**Trade-offs**:
- ✅ Lower overhead
- ✅ Still catches most leaks
- ❌ May miss short-lived allocations
- ❌ Less precise timing

**When to use**: High allocation rates (>10k/sec)

### --max-stack-depth

Controls how many stack frames to capture.

| Value | Overhead | Trade-off |
|-------|----------|-----------|
| 5 | Low | May miss root cause |
| 10 | Medium | ✅ Good default |
| 25 | High | Full context |

**How it works**: Limits how far up the call stack we walk.

**Trade-offs**:
- Shallow depth (5): Fast, but may not show full context
- Medium depth (10): Good balance
- Deep depth (25): Shows everything, but slower

**When to use**:
- 5: Simple apps with shallow call stacks
- 10: Most applications (default)
- 25: Complex frameworks, deep call stacks

### --no-track-gc

Disables garbage collection event tracking.

**Overhead savings**: ~0.5-1%

**Trade-offs**:
- ✅ Slightly faster
- ❌ Can't correlate GC pauses with allocations
- ❌ Less useful for GC tuning

**When to use**: When you only care about allocations, not GC behavior

## Workload-Specific Tuning

### High Allocation Rate (>100k alloc/sec)

**Problem**: Too many events to track efficiently

**Solution**:
```bash
Memlyze record --sample-rate 0.05 python app.py
```

**Why it helps**: Reduces event stream to manageable size

### Deep Call Stacks (>50 frames)

**Problem**: Stack trace collection is slow

**Solution**:
```bash
Memlyze record --max-stack-depth 8 python app.py
```

**Why it helps**: Most important frames are near the top

### Large Long-Running Apps

**Problem**: Trace file grows very large

**Solution**:
```bash
# Use sampling
Memlyze record --sample-rate 0.1 python app.py

# Or take snapshots periodically instead of continuous tracing
python -c "
import Memlyze
tracer = Memlyze.start('trace\.mlyze')
# ... run app ...
tracer.snapshot()  # Take snapshot every N minutes
"
```

### Multi-Threaded Apps

**Problem**: Synchronization overhead between threads

**Solution**: Memlyze uses thread-local buffers automatically, but you can help:

```python
import Memlyze

# Start tracer before creating threads
tracer = Memlyze.start("trace\.mlyze")

# Create threads
threads = [Thread(target=worker) for _ in range(10)]
for t in threads:
    t.start()

# Periodically snapshot (reduces buffer contention)
for i in range(100):
    time.sleep(1)
    tracer.snapshot()
```

## Optimization Checklist

Before deploying to production:

- [ ] Benchmark with `benchmarks/benchmark_overhead.py`
- [ ] Verify overhead is <5% (or your target)
- [ ] Check trace file size is reasonable
- [ ] Test that important allocations are captured
- [ ] Ensure app behavior is unchanged

## Measuring Overhead

### Method 1: Use Benchmark Script

```bash
# Without tracing
python benchmarks/benchmark_overhead.py
# Note the times

# With tracing
Memlyze record python benchmarks/benchmark_overhead.py
# Compare times

# Calculate overhead
overhead = (with_tracing - without_tracing) / without_tracing * 100
```

### Method 2: Production Metrics

```python
import time
import Memlyze

# Measure without tracing
start = time.time()
run_workload()
baseline = time.time() - start

# Measure with tracing
tracer = Memlyze.start("trace\.mlyze")
start = time.time()
run_workload()
with_tracing = time.time() - start
tracer.stop()

overhead = (with_tracing - baseline) / baseline * 100
print(f"Overhead: {overhead:.2f}%")
```

## Common Performance Issues

### Issue: Overhead > 5%

**Possible causes**:
1. Very high allocation rate
2. Deep stack traces
3. Slow disk I/O
4. Too many threads

**Diagnosis**:
```bash
# Check allocation rate
Memlyze record --sample-rate 1.0 python app.py
# Look at events_written in output
# If > 1M events, you have high allocation rate

# Check stack depth
# Profile stack trace collection time
python -m cProfile -o profile.txt app.py
python -m pstats profile.txt
# Look for time in tracemalloc functions
```

**Solutions**:
- Use sampling: `--sample-rate 0.1`
- Reduce stack depth: `--max-stack-depth 5`
- Use faster disk (SSD)
- Reduce thread count if possible

### Issue: Large Trace Files

**Possible causes**:
1. High sample rate
2. Long-running app
3. High allocation churn

**Solutions**:
```bash
# Check trace file size
ls -lh trace\.mlyze

# If > 1GB, try:
Memlyze record --sample-rate 0.05 python app.py

# Or use periodic snapshots
```

### Issue: Memory Usage of Tracer

**Possible causes**:
1. Ring buffer too large
2. Too many cached stack traces

**Solutions**:
```python
# Reduce ring buffer size
tracer = Memlyze.start(
    "trace\.mlyze",
    max_events=5000  # Default is 10000
)
```

## Advanced Optimizations

### Custom Sampling Strategy

```python
import Memlyze

tracer = Memlyze.start("trace\.mlyze", sample_rate=1.0)

# Sample based on allocation size
# (Only trace large allocations)
def should_trace(size):
    if size > 1024 * 1024:  # > 1MB
        return True
    return random.random() < 0.1  # 10% of small

# This requires modifying tracer.py (Phase 1.5)
```

### Pre-Compute Stack Trace IDs

```python
# Warm up stack trace cache before tracing
import tracemalloc
tracemalloc.start()

# Run warmup
warmup()

# Now start real tracing (cache is warm)
tracer = Memlyze.start("trace\.mlyze")
run_real_workload()
```

## Profiling Memlyze Itself

To find bottlenecks in Memlyze:

```bash
# Profile the tracer
python -m cProfile -o Memlyze.prof -m Memlyze record python app.py

# Analyze
python -m pstats Memlyze.prof
>>> sort cumulative
>>> stats 30

# Look for:
# - Time in format.py (encoding)
# - Time in writer.py (I/O)
# - Time in tracemalloc (stack traces)
```

## Performance Targets by Phase

### Phase 1 (Current - Pure Python)
- Target: <5% overhead
- Achieved: ~3-7% depending on workload

### Phase 1.5 (With C Extension)
- Target: <2% overhead
- Strategy: Replace hot paths with C

### Phase 2 (Optimized)
- Target: <1% overhead
- Strategy: Zero-copy, lock-free queues, mmap

## FAQ

**Q: Why is sampling deterministic instead of random?**

A: Deterministic sampling ensures reproducibility. Running the same app twice produces similar traces. Random sampling would vary between runs.

**Q: Can I change sample rate mid-execution?**

A: Not in Phase 1. Phase 2 will support dynamic sampling:
```python
tracer.set_sample_rate(0.1)  # Reduce to 10%
# ... during high load ...
tracer.set_sample_rate(1.0)  # Back to 100% during idle
```

**Q: Does sampling affect leak detection?**

A: Somewhat. A leak that's sampled will still be detected, but you'll see only a fraction of leaked objects. For leak detection, prefer higher sample rates (0.5-1.0).

**Q: How do I trace only specific functions?**

A: Phase 2 will support filtering:
```python
tracer = Memlyze.start(
    "trace\.mlyze",
    include_patterns=["myapp.*"],  # Only trace myapp module
    exclude_patterns=["*.test"]     # Skip test code
)
```

## Getting Help

If you're seeing unexpectedly high overhead:

1. Run `benchmark_overhead.py` to get baseline
2. Collect stats from tracer output
3. File an issue with:
   - Python version
   - Application type
   - Measured overhead
   - Tracer settings used
   - Number of threads

We'll help you tune for your workload!

