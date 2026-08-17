"""
CodeExecutor: runs validated code in an isolated subprocess with a timeout
and best-effort resource caps.

Guarantees differ by platform: the timeout works everywhere; RLIMIT_CPU works
on Linux and macOS; RLIMIT_AS (memory) works on Linux but is refused by macOS.
Limits the OS rejects are skipped rather than crashing execution. Hard memory
capping on macOS requires OS-level isolation (containers), not this module.
"""

import subprocess
import resource
import time

def _set_limits(cpu_seconds, memory_mb):
    """Runs INSIDE the child before user code. Applies each limit defensively."""
    def apply():
        # CPU cap: honored on Linux and MacOS
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
        except (ValueError, OSError):
            pass
        # Memory cap: honored on Linux, refused by macOS - skip if rejected.
        try:
            max_bytes = memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (max_bytes, max_bytes))
        except(ValueError, OSError):
            pass
    return apply

class CodeExecutor:
    def __init__(self, timeout=5, cpu_seconds=2, memory_mb=100):
        self.timeout = timeout
        self.cpu_seconds = cpu_seconds
        self.memory_mb = memory_mb

    def execute(self, code):
        try:
            result = subprocess.run(
                ["python3", "-c", code],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                preexec_fn=_set_limits(self.cpu_seconds, self.memory_mb),
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"Execution exceeded {self.timeout}s limit",
                "returncode": None,
            }
        
if __name__ == "__main__":
    ex = CodeExecutor()

    print("=== normal code ===")
    print(ex.execute("print('ok')"))

    print("\n=== crash ===")
    r = ex.execute("print(1/0)")
    print("success:", r["success"], "| error tail:", repr(r["error"][-60:]))

    print("\n=== infinite loop (timeout) ===")
    start = time.time()
    r = ex.execute("while True: pass")
    print("success:", r["success"], "| error:", r["error"], f"| {time.time()-start:.1f}s")

    print("\n=== cpu bomb (CPU cap, works on macOS) ===")
    r = ex.execute("i=0\nwhile i < 10**12: i+=1")
    print("success:", r["success"], "| returncode:", r["returncode"])