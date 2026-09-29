"""Self-healing reliability layer — MattGPT-Outline.md §12.

Public surface other modules use:

    from mattgpt.self_healing import self_healing, DataIssueError, WrongApproachError

    @self_healing(validate_result=lambda r: r is not None, backup=backup_fn)
    def query_metric(...): ...
"""

from .decorator import self_healing
from .logging_sink import FixLogEntry, FixLogger
from .taxonomy import DataIssueError, FailureType, WrongApproachError

__all__ = [
    "self_healing",
    "FailureType",
    "WrongApproachError",
    "DataIssueError",
    "FixLogger",
    "FixLogEntry",
]
