from pydantic import BaseModel
from typing import List, Optional, Any

class TestCaseRequest(BaseModel):
    id: str
    input_data: str  # JSON string representing kwargs
    expected_output: str  # JSON string
    is_hidden: bool = False

class ExecutionRequest(BaseModel):
    language: str
    source_code: str
    test_cases: List[TestCaseRequest]
    timeout_ms: int = 5000

class TestCaseResult(BaseModel):
    test_case_id: str
    passed: bool
    actual_output: Optional[str] = None
    expected_output: str
    error: Optional[str] = None

class ExecutionResult(BaseModel):
    status: str  # PASSED, FAILED, TIMEOUT, RUNTIME_ERROR, COMPILE_ERROR, SANDBOX_ERROR, SANDBOX_UNAVAILABLE
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    test_results: List[TestCaseResult] = []
    execution_time_ms: int
    error_type: Optional[str] = None
