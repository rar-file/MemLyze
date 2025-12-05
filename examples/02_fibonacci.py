"""
Example 2: Fibonacci with recursion

Tests stack trace capturing with deep call stacks.
"""

import time
import sys


def fibonacci(n):
    """Recursive fibonacci - creates deep call stacks."""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def fibonacci_with_allocation(n):
    """Fibonacci that also allocates memory."""
    if n <= 1:
        # Allocate some data at leaf nodes
        data = bytearray(100)  # 100 bytes
        return n
    
    return fibonacci_with_allocation(n - 1) + fibonacci_with_allocation(n - 2)


def main():
    print("Fibonacci with deep recursion and allocations")
    print("=" * 50)
    
    # Increase recursion limit
    sys.setrecursionlimit(10000)
    
    for n in [5, 10, 15, 20]:
        print(f"\nCalculating fibonacci({n})...")
        start = time.time()
        result = fibonacci_with_allocation(n)
        elapsed = time.time() - start
        print(f"  Result: {result}")
        print(f"  Time: {elapsed:.4f}s")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
