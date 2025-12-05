"""
Example 3: Large allocations

Tests handling of large memory allocations.
"""

import time


def allocate_large_blocks():
    """Allocate several large blocks of memory."""
    blocks = []
    
    print("Large allocation test")
    print("=" * 50)
    
    sizes = [
        (1, "1 MB"),
        (10, "10 MB"),
        (50, "50 MB"),
        (100, "100 MB"),
    ]
    
    for size_mb, label in sizes:
        print(f"\nAllocating {label}...")
        start = time.time()
        
        # Allocate size_mb megabytes
        block = bytearray(size_mb * 1024 * 1024)
        
        elapsed = time.time() - start
        print(f"  Allocated in {elapsed:.4f}s")
        
        blocks.append(block)
        time.sleep(0.5)
    
    print(f"\nTotal allocated: {sum(len(b) for b in blocks):,} bytes")
    
    # Free blocks one by one
    print("\nFreeing blocks...")
    for i, block in enumerate(blocks):
        size_mb = len(block) // (1024 * 1024)
        print(f"  Freeing {size_mb} MB block...")
        del block
        time.sleep(0.5)
    
    blocks.clear()
    print("All blocks freed!")


def main():
    allocate_large_blocks()


if __name__ == "__main__":
    main()
