from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from a2a.messages import A2ARequest
from a2a.router import A2ARouter


# ============================================================
# HTTP request schema
# ============================================================

class A2AHTTPRequest(BaseModel):
    sender: str
    recipient: str
    task: str
    payload: dict


# ============================================================
# Application factory
# ============================================================

def create_app(router: A2ARouter) -> FastAPI:
    """
    Create the A2A HTTP application using an injected router.

    The HTTP server is responsible only for:
        HTTP request
            ↓
        A2ARequest
            ↓
        A2ARouter
            ↓
        A2AResponse
            ↓
        HTTP response

    It does not create or own the specialized agents.
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
        """
        Receive an A2A request over HTTP and route it.
        """

        # ----------------------------------------------------
        # Convert HTTP request into our internal A2A message
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Send through injected A2A router
        # ----------------------------------------------------

        try:

            response = router.send(
                a2a_request
            )

        except Exception as e:

            raise HTTPException(
                status_code=500,
                detail=f"A2A router failed: {e}",
            )

        # ----------------------------------------------------
        # Return A2A response as JSON
        # ----------------------------------------------------

        return {
            "sender": response.sender,
            "recipient": response.recipient,
            "success": response.success,
            "result": response.result,
            "error": response.error,
        }

    return app


# ============================================================
# Default application
# ============================================================
#
# This is useful when starting the server with Uvicorn:
#
#     uvicorn a2a.http_server:app
#
# The router is still created outside create_app(), so the
# application factory remains injectable and easy to test.
# ============================================================

app = create_app(
    A2ARouter()
)