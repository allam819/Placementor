from .models import ExecutionRequest, ExecutionResult
from .docker_runner import DockerRunner

class CodeExecutionService:
    @staticmethod
    def execute(req: ExecutionRequest) -> ExecutionResult:
        # We abstract execution here so it can easily support other runners later
        return DockerRunner.execute(req)
