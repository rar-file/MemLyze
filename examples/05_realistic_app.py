"""
Example 5: Real-world simulation

Simulates a more realistic application with mixed allocation patterns.
"""

import time
import random


class User:
    """Simple user class."""
    def __init__(self, user_id, name, email):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.data = bytearray(512)  # Some user data


class Cache:
    """Simple cache that can leak if not managed properly."""
    def __init__(self, max_size=100):
        self.max_size = max_size
        self.cache = {}
    
    def set(self, key, value):
        if len(self.cache) >= self.max_size:
            # Remove oldest (simplified - should use LRU)
            oldest = list(self.cache.keys())[0]
            del self.cache[oldest]
        self.cache[key] = value
    
    def get(self, key):
        return self.cache.get(key)


def process_users(count=1000):
    """Process a batch of users."""
    print(f"Processing {count} users...")
    
    cache = Cache(max_size=50)
    
    for i in range(count):
        # Create user
        user = User(
            user_id=i,
            name=f"User_{i}",
            email=f"user{i}@example.com"
        )
        
        # Simulate processing
        cache.set(user.user_id, user)
        
        # Simulate some work
        temp_data = [random.randint(0, 255) for _ in range(100)]
        
        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1} users, cache size: {len(cache.cache)}")
    
    return cache


def simulate_api_requests(num_requests=500):
    """Simulate API request handling."""
    print(f"\nSimulating {num_requests} API requests...")
    
    responses = []
    
    for i in range(num_requests):
        # Create response data
        response = {
            "id": i,
            "status": "ok",
            "data": bytearray(1024),  # 1KB response
            "timestamp": time.time(),
        }
        
        responses.append(response)
        
        # Simulate processing time
        time.sleep(0.001)
        
        if (i + 1) % 100 == 0:
            print(f"  Handled {i + 1} requests")
    
    return responses


def main():
    print("Real-world application simulation")
    print("=" * 50)
    
    # Phase 1: Process users
    start = time.time()
    cache = process_users(1000)
    elapsed = time.time() - start
    print(f"Phase 1 completed in {elapsed:.2f}s")
    
    # Phase 2: Handle API requests
    start = time.time()
    responses = simulate_api_requests(500)
    elapsed = time.time() - start
    print(f"Phase 2 completed in {elapsed:.2f}s")
    
    # Phase 3: Cleanup (but keep some data - simulate leak)
    print("\nCleaning up...")
    responses.clear()  # Clear responses
    # Note: cache is still referenced - potential leak if not managed
    
    print(f"Cache still contains {len(cache.cache)} users")
    print("Done!")


if __name__ == "__main__":
    main()
