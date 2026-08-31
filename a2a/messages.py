from dataclasses import dataclass
from typing import Any, Optional


# ============================================================
# Supported A2A task names
# ============================================================

VALID_TASKS = {
    "search_flights",
    "search_hotels",
    "get_weather",
}


# ============================================================
# A2A Request
# ============================================================

@dataclass
class A2ARequest:
    sender: str
    recipient: str
    task: str
    payload: Any

    def __post_init__(self):
        # Validate sender
        if not isinstance(self.sender, str) or not self.sender.strip():
            raise ValueError("A2ARequest sender must be a non-empty string")

        # Validate recipient
        if not isinstance(self.recipient, str) or not self.recipient.strip():
            raise ValueError("A2ARequest recipient must be a non-empty string")

        # Sender and recipient should be different
        if self.sender == self.recipient:
            raise ValueError(
                "A2ARequest sender and recipient must be different"
            )

        # Validate task
        if self.task not in VALID_TASKS:
            raise ValueError(
                f"Unsupported A2A task: {self.task}"
            )

        # Payload must exist
        if self.payload is None:
            raise ValueError(
                "A2ARequest payload cannot be None"
            )


# ============================================================
# A2A Response
# ============================================================

@dataclass
class A2AResponse:
    sender: str = "test-sender"
    recipient: str = "test-recipient"
    success: bool = False
    result: Optional[Any] = None
    error: Optional[str] = None

    def __post_init__(self):

        # Validate sender
        if not isinstance(self.sender, str) or not self.sender.strip():
            raise ValueError(
                "A2AResponse sender must be a non-empty string"
            )

        # Validate recipient
        if not isinstance(self.recipient, str) or not self.recipient.strip():
            raise ValueError(
                "A2AResponse recipient must be a non-empty string"
            )

        # Sender and recipient should be different
        if self.sender == self.recipient:
            raise ValueError(
                "A2AResponse sender and recipient must be different"
            )

        # success must be boolean
        if not isinstance(self.success, bool):
            raise ValueError(
                "A2AResponse success must be a boolean"
            )

        # Successful response should contain a result
        if self.success and self.result is None:
            raise ValueError(
                "Successful A2AResponse must contain a result"
            )

        # Failed response should contain an error
        if not self.success and not self.error:
            raise ValueError(
                "Failed A2AResponse must contain an error"
            )