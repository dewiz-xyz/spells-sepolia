#!/usr/bin/env python3
"""
Simple test script to verify the retry mechanism works.
"""
import time
import random
from functools import wraps
from typing import Tuple, Callable


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1,
    max_delay: float = 10,
    backoff_factor: float = 2,
    jitter: float = 0.1,
    exceptions: Tuple[Exception, ...] = (Exception,)
):
    """Test version of the retry decorator."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        print(f"Failed after {max_retries + 1} attempts. Last error: {str(e)}")
                        raise
                    
                    # Calculate delay with exponential backoff and jitter
                    delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                    jitter_amount = delay * jitter * random.uniform(-1, 1)
                    actual_delay = max(0, delay + jitter_amount)
                    
                    print(f"Attempt {attempt + 1} failed: {str(e)}")
                    print(f"Retrying in {actual_delay:.2f} seconds... (attempt {attempt + 2}/{max_retries + 1})")
                    
                    time.sleep(actual_delay)
            
            raise last_exception
        return wrapper
    return decorator


# Test function that fails 2 times then succeeds
call_count = 0

@retry_with_backoff(max_retries=3, base_delay=0.5)
def test_function():
    global call_count
    call_count += 1
    print(f"Function called (attempt {call_count})")
    
    if call_count < 3:
        raise Exception(f"Simulated failure #{call_count}")
    
    return "Success!"


if __name__ == "__main__":
    print("Testing retry mechanism...")
    try:
        result = test_function()
        print(f"✅ Final result: {result}")
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    print(f"\nTotal function calls: {call_count}")
