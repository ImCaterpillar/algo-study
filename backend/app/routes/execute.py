from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..config import CODE_EXECUTION_ENABLED, MAX_CODE_EXECUTION_TIMEOUT
from ..services.execution_service import execute_code
from ..models import User
from .auth import get_current_user

router = APIRouter(prefix="/execute", tags=["execute"])

class ExecuteRequest(BaseModel):
    language: str = Field(pattern="^(python|javascript|java|cpp)$")
    code: str = Field(min_length=1, max_length=200_000)
    stdin: str = Field(default="", max_length=100_000)
    timeout: int = Field(default=10, ge=1, le=MAX_CODE_EXECUTION_TIMEOUT)

class ExecuteResponse(BaseModel):
    success: bool
    output: str
    error: str
    runtime_ms: int
    status: str

@router.post("", response_model=ExecuteResponse)
def execute(request: ExecuteRequest, current_user: User = Depends(get_current_user)):
    if not CODE_EXECUTION_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Code execution is disabled by server configuration.",
        )
    result = execute_code(
        language=request.language,
        code=request.code,
        stdin=request.stdin,
        timeout=request.timeout,
    )
    return ExecuteResponse(
        success=result.success,
        output=result.output,
        error=result.error,
        runtime_ms=result.runtime_ms,
        status=result.status,
    )
