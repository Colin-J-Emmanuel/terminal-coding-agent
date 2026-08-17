import resource

print("Testing each rlimit individually on this OS:\n")

try:
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    print("RLIMIT_CPU: OK (accepted)")
except Exception as e:
    print(f"RLIMIT_CPU: FAILED -> {type(e).__name__}: {e}")

try:
    max_bytes = 100 * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (max_bytes, max_bytes))
    print("RLIMIT_AS (memory): OK (accepted)")
except Exception as e:
    print(f"RLIMIT_AS (memory): FAILED -> {type(e).__name__}: {e}")