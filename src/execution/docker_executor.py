"""
DockerExecutor: runs code inside an isolated Docker container.

Stronger isolation than the subprocess CodeExecutor: the container has its own
filesystem, no network (--network none), and a hard memory cap that is actually
enforced (unlike RLIMIT_AS on macOS). Falls back gracefully if Docker is absent.
"""

import subprocess
import shutil


class DockerExecutor:
    def __init__(self, timeout=10, memory_mb=100, cpus="1.0", image="python:3.12-slim"):
        self.timeout = timeout
        self.memory_mb = memory_mb
        self.cpus = cpus
        self.image = image

    @staticmethod
    def is_available():
        """True only if the docker CLI exists AND the daemon is responding."""
        if shutil.which("docker") is None:
            return False
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, OSError):
            return False

    def _build_command(self, code):
        return [
            "docker", "run",
            "--rm",
            "--network", "none",
            f"--memory={self.memory_mb}m",
            f"--cpus={self.cpus}",
            self.image,
            "python3", "-c", code,
        ]

    def execute(self, code):
        try:
            result = subprocess.run(
                self._build_command(code),
                capture_output=True,
                text=True,
                timeout=self.timeout,
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
    ex = DockerExecutor()
    print("Docker available:", DockerExecutor.is_available())
    if DockerExecutor.is_available():
        print("normal:", ex.execute("print(2 + 2)"))
        print("crash: ", ex.execute("print(1/0)")["success"])
        print("network blocked:", ex.execute(
            "import urllib.request; urllib.request.urlopen('http://example.com')"
        )["success"])