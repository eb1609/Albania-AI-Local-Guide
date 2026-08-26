# backend/services/tracer.py
import os
import time
from typing import Callable, Any
from langfuse import Langfuse

# Initialize Langfuse client safely
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY", "pk-dummy"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY", "sk-dummy"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)

def trace_step(step_name: str):
    """Decorator to log latency and execution status of pipeline steps."""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "SUCCESS"
            error_msg = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "ERROR"
                error_msg = str(e)
                raise e
            finally:
                duration_ms = round((time.time() - start_time) * 1000, 2)
                print(f"[TRACE] Step: '{step_name}' | Duration: {duration_ms}ms | Status: {status}")
                if error_msg:
                    print(f"[TRACE ERROR] {error_msg}")
        return wrapper
    return decorator