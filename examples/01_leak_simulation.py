"""
Example 1: Simple leak simulation

This program intentionally leaks memory by creating objects that are never freed.
Great for testing leak detection.
"""

import time


def leak_memory():
    """Leak memory by keeping references to large objects."""
    leaked = []
    
    print("Starting memory leak simulation...")
    print("Creating 100 allocations of 1KB each...")
    
    for i in range(100):
        # Allocate 1KB
        data = bytearray(1024)
        leaked.append(data)
        
        if (i + 1) % 10 == 0:
            print(f"  Leaked {i + 1} objects ({(i + 1) * 1024} bytes)")
        
        time.sleep(0.01)  # Small delay to spread allocations
    
    print(f"Total leaked: {len(leaked)} objects ({len(leaked) * 1024:,} bytes)")
    print("These objects will never be freed!")
    
    # Keep references alive
    return leaked


def main():
    leaked_objects = leak_memory()
    
    # Do some other work
    print("\nDoing other work...")
    for i in range(10):
        temp = [j for j in range(1000)]  # Temporary allocations
        time.sleep(0.1)
    
    print("\nProgram ending with leaked objects still in memory")
    # leaked_objects still referenced, so never freed


if __name__ == "__main__":
    main()
