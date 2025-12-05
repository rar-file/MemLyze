"""
Example 4: Many small allocations

Tests handling of high allocation rates.
"""

import time


def many_small_allocations():
    """Create many small allocations quickly."""
    print("Many small allocations test")
    print("=" * 50)
    
    print("\nCreating 10,000 small allocations...")
    start = time.time()
    
    objects = []
    for i in range(10000):
        # 100 byte allocation
        obj = bytearray(100)
        objects.append(obj)
        
        if (i + 1) % 1000 == 0:
            print(f"  Created {i + 1} objects...")
    
    elapsed = time.time() - start
    print(f"\nCreated 10,000 objects in {elapsed:.4f}s")
    print(f"Rate: {10000 / elapsed:.0f} allocations/second")
    
    # Clean up
    print("\nCleaning up...")
    objects.clear()
    print("Done!")


def list_comprehension_test():
    """Test list comprehensions (fast allocation)."""
    print("\n" + "=" * 50)
    print("List comprehension test")
    print("=" * 50)
    
    print("\nCreating list with 100,000 integers...")
    start = time.time()
    numbers = [i for i in range(100000)]
    elapsed = time.time() - start
    print(f"Created in {elapsed:.4f}s")
    
    print("\nCreating list with 100,000 strings...")
    start = time.time()
    strings = [f"string_{i}" for i in range(100000)]
    elapsed = time.time() - start
    print(f"Created in {elapsed:.4f}s")
    
    print("\nCreating list with 10,000 bytearrays...")
    start = time.time()
    arrays = [bytearray(100) for i in range(10000)]
    elapsed = time.time() - start
    print(f"Created in {elapsed:.4f}s")


def main():
    many_small_allocations()
    list_comprehension_test()


if __name__ == "__main__":
    main()
