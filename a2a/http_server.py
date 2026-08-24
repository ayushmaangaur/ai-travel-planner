from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from a2a.messages import A2ARequest
from a2a.router import A2ARouter


class A2AHTTPRequest(BaseModel):
    sender: str
    recipient: str
    task: str
    payload: dict


def create_app(router: A2ARouter) -> FastAPI:
    """
    Create the A2A HTTP application using an injected router.
    """

    if router is None:
        raise ValueError(
            "create_app requires an A2ARouter"
        )

    app = FastAPI(
        title="AI Travel Planner A2A Server",
        version="1.0.0",
    )

    @app.post("/a2a")
    def handle_a2a_request(
        request: A2AHTTPRequest,
    ):
        try:
            a2a_request = A2ARequest(
                sender=request.sender,
                recipient=request.recipient,
                task=request.task,
                payload=request.payload,
            )

        except (ValueError, TypeError) as e:
            raise HTTPException(
                status_code=400,
                detail=str(e),
            )

        try:
            response = router.send(
                a2a_request
            )

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"A2A router failed: {e}",
            )

        return {
            "sender": response.sender,
            "recipient": response.recipient,
            "success": response.success,
            "result": response.result,
            "error": response.error,
        }

    return app