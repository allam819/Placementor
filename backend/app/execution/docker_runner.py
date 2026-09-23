import os
import tempfile
import shutil
import json
import subprocess
import time
from .models import ExecutionRequest, ExecutionResult, TestCaseResult
from .config import EXECUTION_MEMORY_LIMIT, EXECUTION_CPU_LIMIT, EXECUTION_PIDS_LIMIT

RUNNER_SCRIPT = """
import json
import sys
import importlib.util
import time
import traceback
import contextlib
import io

def run_tests():
    with open('test_cases.json') as f:
        tests = json.load(f)
        
    captured_stdout = io.StringIO()
    
    try:
        spec = importlib.util.spec_from_file_location("solution", "solution.py")
        solution_mod = importlib.util.module_from_spec(spec)
        with contextlib.redirect_stdout(captured_stdout):
            spec.loader.exec_module(solution_mod)
    except Exception as e:
        return {
            "status": "RUNTIME_ERROR",
            "stderr": traceback.format_exc(),
            "stdout": captured_stdout.getvalue(),
            "test_results": []
        }
        
    funcs = [getattr(solution_mod, name) for name in dir(solution_mod) if callable(getattr(solution_mod, name)) and not name.startswith('_') and name not in ['contextlib', 'io', 'json', 'sys', 'time', 'traceback']]
    
    if not funcs:
        return {
            "status": "RUNTIME_ERROR",
            "stderr": "No function found in solution.py",
            "stdout": captured_stdout.getvalue(),
            "test_results": []
        }
        
    func = funcs[-1] # Target function is usually defined last
    
    test_results = []
    has_failure = False
    has_error = False
    first_error = None
    
    for t in tests:
        test_case_id = t["id"]
        try:
            input_data = json.loads(t["input_data"])
            expected_output = json.loads(t["expected_output"])
        except json.JSONDecodeError:
            # If the input isn't valid JSON, fallback to raw string passing
            input_data = t["input_data"]
            expected_output = t["expected_output"]
        
        try:
            with contextlib.redirect_stdout(captured_stdout):
                if isinstance(input_data, dict):
                    actual = func(**input_data)
                elif isinstance(input_data, list):
                    actual = func(*input_data)
                else:
                    actual = func(input_data)
                
            passed = (actual == expected_output)
            if not passed:
                has_failure = True
                
            test_results.append({
                "test_case_id": test_case_id,
                "passed": passed,
                "actual_output": json.dumps(actual) if actual is not None else "null",
                "expected_output": json.dumps(expected_output) if expected_output is not None else "null",
                "error": None
            })
            
        except Exception as e:
            has_error = True
            err_str = traceback.format_exc()
            if not first_error:
                first_error = err_str
            test_results.append({
                "test_case_id": test_case_id,
                "passed": False,
                "actual_output": None,
                "expected_output": json.dumps(expected_output) if expected_output is not None else "null",
                "error": err_str
            })
            
    if has_error:
        status = "RUNTIME_ERROR"
    elif has_failure:
        status = "FAILED"
    else:
        status = "PASSED"
        
    return {
        "status": status,
        "stdout": captured_stdout.getvalue(),
        "stderr": first_error,
        "test_results": test_results
    }

if __name__ == "__main__":
    start_time = time.perf_counter()
    res = run_tests()
    res["execution_time_ms"] = int((time.perf_counter() - start_time) * 1000)
    with open('results.json', 'w') as f:
        json.dump(res, f)
"""

class DockerRunner:
    @staticmethod
    def execute(req: ExecutionRequest) -> ExecutionResult:
        if req.language.lower() != "python":
            return ExecutionResult(status="SANDBOX_ERROR", execution_time_ms=0, error_type="Unsupported language")
            
        # Basic validation
        if len(req.source_code) > 50000:
            return ExecutionResult(status="SANDBOX_ERROR", execution_time_ms=0, error_type="Source code too large")

        # Check docker availability
        try:
            subprocess.run(["docker", "info"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except Exception:
            return ExecutionResult(status="SANDBOX_UNAVAILABLE", execution_time_ms=0, error_type="Docker is not available")

        # Create temporary workspace
        workspace = tempfile.mkdtemp(prefix="sandbox_")
        
        try:
            import stat
            os.chmod(workspace, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            
            # Write files
            with open(os.path.join(workspace, "solution.py"), "w", encoding="utf-8") as f:
                f.write(req.source_code)
                
            with open(os.path.join(workspace, "runner.py"), "w", encoding="utf-8") as f:
                f.write(RUNNER_SCRIPT)
                
            test_cases = []
            for tc in req.test_cases:
                test_cases.append({
                    "id": tc.id,
                    "input_data": tc.input_data,
                    "expected_output": tc.expected_output
                })
            with open(os.path.join(workspace, "test_cases.json"), "w", encoding="utf-8") as f:
                json.dump(test_cases, f)
                
            # JUSTIFICATION for subprocess: We must orchestrate the Docker container execution securely.
            # Using subprocess strictly to invoke 'docker run' isolates the untrusted candidate code inside the container.
            # The host only manages the container lifecycle and never evaluates the candidate code directly.
            docker_cmd = [
                "docker", "run",
                "--rm",
                "--network", "none",                   # Network isolation
                "-m", EXECUTION_MEMORY_LIMIT,          # Memory limit
                "--cpus", str(EXECUTION_CPU_LIMIT),    # CPU limit
                "--pids-limit", str(EXECUTION_PIDS_LIMIT), # PID limit against fork bombs
                "--cap-drop", "ALL",                   # Drop all Linux capabilities
                "--read-only",                         # Read-only root filesystem
                "--tmpfs", "/tmp",                     # Provide writable /tmp for python
                "--user", "nobody",                    # Non-root user execution
                "-v", f"{workspace}:/workspace",       # Mount temp workspace
                "-w", "/workspace",                    # Set working directory
                "python:3.11-slim",                    # Base image
                "timeout", str(req.timeout_ms // 1000 + 1),  # Fail-safe timeout inside container
                "python", "runner.py"
            ]
            
            start_time = time.perf_counter()
            process = subprocess.run(
                docker_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=req.timeout_ms / 1000 + 2, # Host timeout just in case
                text=True
            )
            exec_time = int((time.perf_counter() - start_time) * 1000)
            
            # Read results
            results_path = os.path.join(workspace, "results.json")
            if not os.path.exists(results_path):
                # Did it timeout or OOM?
                if process.returncode == 124 or process.returncode == 137 or "Killed" in process.stderr:
                    return ExecutionResult(status="TIMEOUT", execution_time_ms=exec_time, stderr="Execution timed out or exceeded memory limits")
                
                return ExecutionResult(
                    status="SANDBOX_ERROR",
                    execution_time_ms=exec_time,
                    stderr=process.stderr,
                    error_type="Container failed to produce results"
                )
                
            with open(results_path, "r", encoding="utf-8") as f:
                res_data = json.load(f)
                
            test_results = [TestCaseResult(**tr) for tr in res_data.get("test_results", [])]
            return ExecutionResult(
                status=res_data.get("status", "SANDBOX_ERROR"),
                stdout=res_data.get("stdout"),
                stderr=res_data.get("stderr"),
                test_results=test_results,
                execution_time_ms=res_data.get("execution_time_ms", exec_time)
            )
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(status="TIMEOUT", execution_time_ms=req.timeout_ms, error_type="Execution timed out on host")
        except Exception as e:
            return ExecutionResult(status="SANDBOX_ERROR", execution_time_ms=0, error_type=str(e))
        finally:
            # Always clean up
            shutil.rmtree(workspace, ignore_errors=True)
