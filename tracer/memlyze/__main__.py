"""
CLI entry point for memlyze.

Usage:
    memlyze record python script.py
    memlyze record --sample-rate 0.1 python app.py
"""

import sys
import argparse
import subprocess
import os


def cmd_record(args):
    """Record command: trace a program execution."""
    # Build command to run
    if not args.command:
        print("Error: No command specified")
        print("Usage: memlyze record <command> [args...]")
        return 1
    
    # Get absolute paths (use raw strings in wrapper, so don't escape here)
    output_path = os.path.abspath(args.output)
    cwd = os.getcwd()
    script_path = os.path.abspath(args.command[1])
    
    # Create wrapper script with raw strings for Windows paths
    wrapper_code = f"""
import sys
import memlyze

# Start tracing
tracer = memlyze.start(
    output_file=r'''{output_path}''',
    sample_rate={args.sample_rate},
    max_stack_depth={args.max_stack_depth},
    track_gc={args.track_gc}
)

# Inject path for the script
sys.path.insert(0, r'''{cwd}''')

# Run the target script
try:
    with open(r'''{script_path}''', 'r', encoding='utf-8') as f:
        code = f.read()
    exec(compile(code, r'''{script_path}''', 'exec'), {{'__name__': '__main__', '__file__': r'''{script_path}'''}})
finally:
    tracer.stop()
"""
    
    # Write wrapper to temp file
    wrapper_file = ".memlyze_wrapper.py"
    with open(wrapper_file, 'w') as f:
        f.write(wrapper_code)
    
    try:
        # Run Python with wrapper
        cmd = [args.command[0], wrapper_file] + args.command[2:]
        result = subprocess.run(cmd)
        return result.returncode
    finally:
        # Clean up wrapper
        if os.path.exists(wrapper_file):
            os.remove(wrapper_file)


def cmd_analyze(args):
    """Analyze command: open trace file in analyzer."""
    import struct
    import json
    from collections import defaultdict
    
    print("\n" + _color("="*70, "cyan"))
    print(_color("  Memlyze v0.1.0", "cyan", bold=True) + _color(" | Trace Analyzer", "white"))
    print(_color("="*70, "cyan"))
    print(_color("  TRACE FILE", "yellow", bold=True))
    print(_color("  └─", "white") + f" {args.trace_file}")
    print(_color("="*70, "cyan"))
    
    # Check if file exists
    if not os.path.exists(args.trace_file):
        print(_color("\n  ERROR", "red", bold=True))
        print(_color("  └─", "white") + " File not found: " + _color(args.trace_file, "red"))
        print(_color("="*70, "cyan") + "\n")
        return 1
    
    # Get file info
    file_size = os.path.getsize(args.trace_file)
    size_kb = file_size / 1024
    size_mb = size_kb / 1024
    size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{size_kb:.2f} KB"
    
    print(_color("\n  FILE INFO", "yellow", bold=True))
    print(_color("  ├─", "white") + f" Size           : {file_size:,} bytes ({size_str})")
    
    # Parse trace file
    try:
        with open(args.trace_file, 'rb') as f:
            # Read header
            magic = f.read(4)
            if magic != b'MTRC':
                print(_color("  └─", "white") + " Format         : " + _color("Invalid file format", "red"))
                print(_color("="*70, "cyan") + "\n")
                return 1
            
            print(_color("  ├─", "white") + " Format         : " + _color("Valid Memlyze file", "green"))
            
            version = struct.unpack('I', f.read(4))[0]
            start_time = struct.unpack('Q', f.read(8))[0]
            metadata_len = struct.unpack('I', f.read(4))[0]
            
            print(_color("  └─", "white") + f" Version        : {version}")
            
            # Skip to metadata
            f.seek(256)
            metadata_json = f.read(metadata_len)
            metadata = json.loads(metadata_json.decode('utf-8'))
            
            # Parse events
            events = []
            allocations = {}  # address -> info
            alloc_by_stack = defaultdict(lambda: {'count': 0, 'total_bytes': 0})
            current_time = start_time
            
            event_count = 0
            alloc_count = 0
            free_count = 0
            gc_count = 0
            
            while True:
                event_type_bytes = f.read(1)
                if not event_type_bytes:
                    break
                
                event_type = event_type_bytes[0]
                event_count += 1
                
                # Read timestamp delta (varint)
                delta = _read_varint(f)
                current_time += delta
                
                if event_type == 0:  # ALLOC
                    address = struct.unpack('Q', f.read(8))[0]
                    size = _read_varint(f)
                    stack_id = _read_varint(f)
                    thread_id = struct.unpack('H', f.read(2))[0]
                    
                    allocations[address] = {
                        'size': size,
                        'stack_id': stack_id,
                        'time': current_time,
                        'freed': False
                    }
                    
                    alloc_by_stack[stack_id]['count'] += 1
                    alloc_by_stack[stack_id]['total_bytes'] += size
                    alloc_count += 1
                    
                elif event_type == 1:  # FREE
                    address = struct.unpack('Q', f.read(8))[0]
                    if address in allocations:
                        allocations[address]['freed'] = True
                    free_count += 1
                    
                elif event_type == 2:  # GC
                    objects = _read_varint(f)
                    bytes_freed = _read_varint(f)
                    gc_count += 1
            
            # Analysis
            print(_color("\n  EVENTS PARSED", "yellow", bold=True))
            print(_color("  ├─", "white") + f" Total Events   : {event_count:,}")
            print(_color("  ├─", "white") + f" Allocations    : {alloc_count:,}")
            print(_color("  ├─", "white") + f" Deallocations  : {free_count:,}")
            print(_color("  └─", "white") + f" GC Events      : {gc_count:,}")
            
            # Find leaks (never freed)
            leaks = [a for a in allocations.values() if not a['freed']]
            leaked_bytes = sum(a['size'] for a in leaks)
            
            print(_color("\n  LEAK DETECTION", "yellow", bold=True))
            print(_color("  ├─", "white") + f" Still Allocated: " + 
                  _color(f"{len(leaks):,}", "red" if len(leaks) > 0 else "green"))
            print(_color("  └─", "white") + f" Total Size     : " + 
                  _color(f"{leaked_bytes:,} bytes ({leaked_bytes/1024:.1f} KB)", 
                         "red" if leaked_bytes > 0 else "green"))
            
            # Top allocators
            if alloc_by_stack:
                sorted_stacks = sorted(alloc_by_stack.items(), 
                                     key=lambda x: x[1]['total_bytes'], 
                                     reverse=True)[:5]
                
                print(_color("\n  TOP ALLOCATORS", "yellow", bold=True))
                for i, (stack_id, info) in enumerate(sorted_stacks, 1):
                    stack_str = str(stack_id)
                    if stack_str in metadata.get('stack_traces', {}):
                        frames = metadata['stack_traces'][stack_str]
                        if frames:
                            first_frame = frames[0]
                            file_id = str(first_frame.get('file_id', ''))
                            func_id = str(first_frame.get('func_id', ''))
                            line = first_frame.get('line', 0)
                            
                            filename = metadata.get('files', {}).get(file_id, 'unknown')
                            funcname = metadata.get('functions', {}).get(func_id, 'unknown')
                            
                            location = f"{os.path.basename(filename)}:{line} {funcname}()"
                        else:
                            location = "unknown"
                    else:
                        location = f"stack_{stack_id}"
                    
                    pct = (info['total_bytes'] / sum(s['total_bytes'] for s in alloc_by_stack.values())) * 100
                    prefix = "  └─" if i == len(sorted_stacks) else "  ├─"
                    
                    print(_color(prefix, "white") + 
                          f" #{i}: {info['total_bytes']:>10,} bytes ({pct:>5.1f}%) - {location[:50]}")
            
            # Memory statistics
            total_allocated = sum(a['size'] for a in allocations.values())
            total_freed = sum(a['size'] for a in allocations.values() if a['freed'])
            
            print(_color("\n  MEMORY STATISTICS", "yellow", bold=True))
            print(_color("  ├─", "white") + f" Total Allocated: {total_allocated:,} bytes ({total_allocated/1024:.1f} KB)")
            print(_color("  ├─", "white") + f" Total Freed    : {total_freed:,} bytes ({total_freed/1024:.1f} KB)")
            print(_color("  └─", "white") + f" Still in Use   : {leaked_bytes:,} bytes ({leaked_bytes/1024:.1f} KB)")
            
            # Recommendations
            if leaked_bytes > 1024 * 1024:  # > 1MB
                print(_color("\n  RECOMMENDATIONS", "yellow", bold=True))
                print(_color("  └─", "white") + _color(" CRITICAL: ", "red", bold=True) + 
                      f"Significant memory leak detected ({leaked_bytes/1024/1024:.1f} MB)")
            elif leaked_bytes > 100 * 1024:  # > 100KB
                print(_color("\n  RECOMMENDATIONS", "yellow", bold=True))
                print(_color("  └─", "white") + _color(" WARNING: ", "yellow", bold=True) + 
                      f"Potential memory leak ({leaked_bytes/1024:.1f} KB)")
            
    except Exception as e:
        print(_color("\n  ERROR", "red", bold=True))
        print(_color("  └─", "white") + f" Failed to parse: {str(e)}")
        print(_color("="*70, "cyan") + "\n")
        return 1
    
    print(_color("="*70, "cyan"))
    print(_color("  Analysis complete. Use --detailed for more info (coming soon)", "white", dim=True))
    print(_color("="*70, "cyan") + "\n")
    return 0


def _read_varint(f):
    """Read a varint from file."""
    result = 0
    shift = 0
    while True:
        byte_data = f.read(1)
        if not byte_data:
            return 0
        byte = byte_data[0]
        result |= (byte & 0x7F) << shift
        if (byte & 0x80) == 0:
            break
        shift += 7
    return result


def cmd_serve(args):
    """Serve command: start web UI server."""
    print("\n" + _color("="*70, "cyan"))
    print(_color("  Memlyze v0.1.0", "cyan", bold=True) + _color(" | Web Server", "white"))
    print(_color("="*70, "cyan"))
    print(_color("  TRACE FILE", "yellow", bold=True))
    print(_color("  └─", "white") + f" {args.trace_file}")
    print(_color("="*70, "cyan"))
    
    # Check if file exists
    if not os.path.exists(args.trace_file):
        print(_color("\n  ERROR", "red", bold=True))
        print(_color("  └─", "white") + " File not found: " + _color(args.trace_file, "red"))
        print(_color("="*70, "cyan") + "\n")
        return 1
    
    print(_color("\n  WEB UI STATUS", "yellow", bold=True))
    print(_color("  └─", "white") + " Phase 3 web interface not yet implemented")
    
    print(_color("\n  COMING SOON", "yellow", bold=True))
    print(_color("  ├─", "white") + " Interactive timeline (scrubbing, zoom)")
    print(_color("  ├─", "white") + " Memory heatmaps and treemaps")
    print(_color("  ├─", "white") + " Click-to-code navigation")
    print(_color("  ├─", "white") + " Real-time filtering and search")
    print(_color("  └─", "white") + f" Local server on http://localhost:{args.port}")
    
    print(_color("\n  CURRENT OPTIONS", "yellow", bold=True))
    print(_color("  └─", "white") + " Terminal UI    : " + _color(f"memtrace analyze {args.trace_file}", "green"))
    
    print(_color("="*70, "cyan"))
    print(_color("  Track progress at: github.com/yourusername/memtrace", "white", dim=True))
    print(_color("="*70, "cyan") + "\n")
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='memlyze',
        description='Visual memory profiler with <5%% overhead'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Record command
    record_parser = subparsers.add_parser('record', help='Record a trace')
    record_parser.add_argument('command', nargs='+', help='Command to trace')
    record_parser.add_argument('-o', '--output', default='trace.mlyze', 
                              help='Output file (default: trace.mlyze)')
    record_parser.add_argument('--sample-rate', type=float, default=1.0,
                              help='Sample rate (default: 1.0 = trace everything)')
    record_parser.add_argument('--max-stack-depth', type=int, default=10,
                              help='Maximum stack depth (default: 10)')
    record_parser.add_argument('--no-track-gc', dest='track_gc', action='store_false',
                              help='Disable GC tracking')
    record_parser.set_defaults(func=cmd_record, track_gc=True)
    
    # Analyze command (Phase 2)
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a trace file')
    analyze_parser.add_argument('trace_file', help='Trace file to analyze')
    analyze_parser.set_defaults(func=cmd_analyze)
    
    # Serve command (Phase 3)
    serve_parser = subparsers.add_parser('serve', help='Start web UI server')
    serve_parser.add_argument('trace_file', help='Trace file to visualize')
    serve_parser.add_argument('-p', '--port', type=int, default=8080,
                             help='Port to serve on (default: 8080)')
    serve_parser.set_defaults(func=cmd_serve)
    
    # Parse args
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Run command
    return args.func(args)


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


if __name__ == '__main__':
    sys.exit(main())
