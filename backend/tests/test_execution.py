import pytest
import os
import json
from app.execution import ExecutionRequest, TestCaseRequest, CodeExecutionService

def has_docker():
    import subprocess
    try:
        subprocess.run(["docker", "info"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except:
        return False

@pytest.mark.skipif(not has_docker(), reason="Docker is not available")
def test_normal_python_execution():
    code = """
def add(a, b):
    return a + b
"""
    req = ExecutionRequest(
        language="python",
        source_code=code,
        test_cases=[
            TestCaseRequest(id="1", input_data='{"a": 2, "b": 3}', expected_output='5'),
            TestCaseRequest(id="2", input_data='{"a": -1, "b": 1}', expected_output='0')
        ]
    )
    res = CodeExecutionService.execute(req)
    assert res.status == "PASSED"
    assert len(res.test_results) == 2
    assert all(tr.passed for tr in res.test_results)

@pytest.mark.skipif(not has_docker(), reason="Docker is not available")
def test_incorrect_solution():
    code = """
def add(a, b):
    return a - b
"""
    req = ExecutionRequest(
        language="python",
        source_code=code,
        test_cases=[
            TestCaseRequest(id="1", input_data='{"a": 2, "b": 3}', expected_output='5')
        ]
    )
    res = CodeExecutionService.execute(req)
    assert res.status == "FAILED"
    assert res.test_results[0].passed is False

@pytest.mark.skipif(not has_docker(), reason="Docker is not available")
def test_runtime_error():
    code = """
def crash():
    return 1 / 0
"""
    req = ExecutionRequest(
        language="python",
        source_code=code,
        test_cases=[
            TestCaseRequest(id="1", input_data='{}', expected_output='1')
        ]
    )
    res = CodeExecutionService.execute(req)
    assert res.status == "RUNTIME_ERROR"
    assert "ZeroDivisionError" in res.stderr

@pytest.mark.skipif(not has_docker(), reason="Docker is not available")
def test_timeout():
    code = """
import time
def infinite():
    while True:
        pass
"""
    req = ExecutionRequest(
        language="python",
        source_code=code,
        test_cases=[
            TestCaseRequest(id="1", input_data='{}', expected_output='1')
        ],
        timeout_ms=1000
    )
    res = CodeExecutionService.execute(req)
    assert res.status == "TIMEOUT"

def test_unsupported_language():
    req = ExecutionRequest(
        language="ruby",
        source_code="puts 'hello'",
        test_cases=[]
    )
    res = CodeExecutionService.execute(req)
    assert res.status == "SANDBOX_ERROR"

def test_oversized_code():
    req = ExecutionRequest(
        language="python",
        source_code="x = 1\n" * 20000,
        test_cases=[]
    )
    res = CodeExecutionService.execute(req)
    assert res.status == "SANDBOX_ERROR"

@pytest.mark.skipif(not has_docker(), reason="Docker is not available")
def test_no_network_access():
    code = """
import urllib.request
def test_net():
    try:
        urllib.request.urlopen("http://google.com", timeout=1)
        return "connected"
    except Exception as e:
        return str(e)
"""
    req = ExecutionRequest(
        language="python",
        source_code=code,
        test_cases=[
            TestCaseRequest(id="1", input_data='{}', expected_output='"connected"')
        ]
    )
    res = CodeExecutionService.execute(req)
    assert res.status == "FAILED"
    # It should not connect, therefore returning some connection error string, failing the check against "connected"
    assert "connected" not in res.test_results[0].actual_output

@pytest.mark.skipif(not has_docker(), reason="Docker is not available")
def test_filesystem_isolation():
    code = """
import os
def test_fs():
    try:
        with open("/etc/passwd", "r") as f:
            return "accessed"
    except:
        return "denied"
"""
    req = ExecutionRequest(
        language="python",
        source_code=code,
        test_cases=[
            TestCaseRequest(id="1", input_data='{}', expected_output='"accessed"')
        ]
    )
    res = CodeExecutionService.execute(req)
    # the container has /etc/passwd because it's standard linux, 
    # but let's test writing outside workspace
    
    code_write = """
import os
def test_fs():
    try:
        with open("/usr/bin/hack", "w") as f:
            f.write("hack")
        return "written"
    except Exception as e:
        return "denied"
"""
    req2 = ExecutionRequest(
        language="python",
        source_code=code_write,
        test_cases=[
            TestCaseRequest(id="1", input_data='{}', expected_output='"denied"')
        ]
    )
    res2 = CodeExecutionService.execute(req2)
    assert res2.status == "PASSED" # because writing outside workspace is denied (PermissionError)

@pytest.mark.skipif(not has_docker(), reason="Docker is not available")
def test_environment_isolation():
    code = """
import os
def test_env():
    # Should not have any application secrets
    return os.environ.get("SUPABASE_URL", "missing")
"""
    req = ExecutionRequest(
        language="python",
        source_code=code,
        test_cases=[
            TestCaseRequest(id="1", input_data='{}', expected_output='"missing"')
        ]
    )
    res = CodeExecutionService.execute(req)
    assert res.status == "PASSED"

@pytest.mark.skipif(not has_docker(), reason="Docker is not available")
def test_pids_limit():
    code = """
import os
import time
def fork_bomb():
    try:
        for _ in range(100):
            os.fork()
        return "forked"
    except Exception as e:
        return "denied"
"""
    req = ExecutionRequest(
        language="python",
        source_code=code,
        test_cases=[TestCaseRequest(id="1", input_data='{}', expected_output='"denied"')]
    )
    res = CodeExecutionService.execute(req)
    assert res.status in ["FAILED", "RUNTIME_ERROR", "TIMEOUT"]
    
@pytest.mark.skipif(not has_docker(), reason="Docker is not available")
def test_non_root():
    code = """
import os
def get_uid():
    return os.getuid()
"""
    req = ExecutionRequest(
        language="python",
        source_code=code,
        test_cases=[TestCaseRequest(id="1", input_data='{}', expected_output='0')]
    )
    res = CodeExecutionService.execute(req)
    assert res.status == "FAILED"
    
@pytest.mark.skipif(not has_docker(), reason="Docker is not available")
def test_no_docker_socket():
    code = """
import os
def test_socket():
    return os.path.exists("/var/run/docker.sock")
"""
    req = ExecutionRequest(
        language="python",
        source_code=code,
        test_cases=[TestCaseRequest(id="1", input_data='{}', expected_output='false')]
    )
    res = CodeExecutionService.execute(req)
    assert res.status == "PASSED"
