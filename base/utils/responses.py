from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class RepositoryResponse:
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None


@dataclass
class APIResponse:
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None
    errors: Optional[Any] = None
    code: Optional[int] = None