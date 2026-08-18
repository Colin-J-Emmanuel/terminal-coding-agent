import time
from src.execution.executor import CodeExecutor


def test_normal_code_succeeds():
    ex = CodeExecutor()
    result = ex.execute("print('hello')")
    assert result["success"] is True
    assert "hello" in result["output"]


def test_crash_reports_failure():
    ex = CodeExecutor()
    result = ex.execute("print(1/0)")
    assert result["success"] is False
    assert "ZeroDivisionError" in result["error"]


def test_infinite_loop_times_out():
    ex = CodeExecutor(timeout=2)
    start = time.time()
    result = ex.execute("while True: pass")
    elapsed = time.time() - start
    assert result["success"] is False
    # Pin the behavior: it should run ~the timeout, not just "under some ceiling".
    assert 1.5 < elapsed < 3.5


def test_crash_produces_no_output_only_error():
    # Replaces the worthless `is not None` test with a real behavioral check:
    # a crash should yield empty stdout AND a populated error, not just "not None".
    ex = CodeExecutor()
    result = ex.execute("print(1/0)")
    assert result["output"] == ""
    assert result["error"] != ""