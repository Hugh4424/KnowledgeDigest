"""User-facing errors with one stable validation format."""

from __future__ import annotations


class ValidationError(ValueError):
    """An invalid user input that must not produce a traceback."""

    def __init__(self, stage: str, failed_input: object, reason: str) -> None:
        self.stage = stage
        self.failed_input = str(failed_input)
        self.reason = reason
        super().__init__(
            f"validate: stage={self.stage}; failed input {self.failed_input}: {self.reason}. "
            "Rerun after correcting the input."
        )
