import functools, time

def log(*a):
    print(*a, flush=True)

def retry(tries=4, delay=5):
    """Retry a function with growing waits. Re-raises the last error."""
    def deco(fn):
        @functools.wraps(fn)
        def wrap(*a, **k):
            last = None
            for i in range(tries):
                try:
                    return fn(*a, **k)
                except Exception as e:
                    last = e
                    log(f"[retry] {fn.__name__} attempt {i+1}/{tries} failed: {e}")
                    if i < tries - 1:
                        time.sleep(delay * (i + 1))
            raise last
        return wrap
    return deco
