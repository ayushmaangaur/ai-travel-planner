import requests

from a2a.messages import A2ARequest, A2AResponse


class HTTPA2ATransport:
    """
    HTTP-based A2A transport.

    Sends A2ARequest objects to a remote A2A HTTP endpoint
    and converts the HTTP response back into an A2AResponse.

    This class is transport-only.

    It does NOT:
    - route tasks
    - call specialized agents
    - call Gemini
    - contain RootTravelAgent logic
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 10.0,
    ):
        if not isinstance(base_url, str) or not base_url.strip():
            raise ValueError(
                "HTTPA2ATransport requires a non-empty base_url"
            )

        if timeout <= 0:
            raise ValueError(
                "HTTPA2ATransport timeout must be greater than 0"
            )

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def send(self, message: A2ARequest) -> A2AResponse:
        """
        Send an A2ARequest to the remote HTTP endpoint.

        The request is serialized into JSON.

        The remote endpoint is expected to return JSON containing:

        {
            "sender": "...",
            "recipient": "...",
            "success": true,
            "result": ...,
            "error": null
        }
        """

        if not isinstance(message, A2ARequest):
            raise TypeError(
                "HTTPA2ATransport.send expects an A2ARequest"
            )

        url = f"{self.base_url}/a2a"

        payload = {
            "sender": message.sender,
            "recipient": message.recipient,
            "task": message.task,
            "payload": message.payload,
        }

        # TravelRequest is a dataclass, so convert it to a
        # dictionary when necessary.
        if hasattr(message.payload, "__dataclass_fields__"):
            payload["payload"] = {
                field_name: getattr(
                    message.payload,
                    field_name
                )
                for field_name in message.payload.__dataclass_fields__
            }

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
            )

        except requests.RequestException as e:
            raise RuntimeError(
                f"A2A HTTP request failed: {e}"
            ) from e

        if response.status_code != 200:
            raise RuntimeError(
                f"A2A HTTP endpoint returned "
                f"status {response.status_code}"
            )

        try:
            data = response.json()

        except ValueError as e:
            raise RuntimeError(
                "A2A HTTP endpoint returned invalid JSON"
            ) from e

        if not isinstance(data, dict):
            raise RuntimeError(
                "A2A HTTP endpoint must return a JSON object"
            )

        try:
            return A2AResponse(
                sender=data["sender"],
                recipient=data["recipient"],
                success=data["success"],
                result=data.get("result"),
                error=data.get("error"),
            )

        except (KeyError, TypeError, ValueError) as e:
            raise RuntimeError(
                f"Invalid A2A HTTP response: {e}"
            ) from e