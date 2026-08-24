from a2a.messages import A2ARequest, A2AResponse
from a2a.router import A2ARouter


class LocalA2ATransport:
    """
    Local in-process A2A transport.

    This transport simulates agent-to-agent communication
    without using HTTP or a network.

    The RootTravelAgent sends an A2ARequest to this transport.
    The transport forwards the request to A2ARouter.
    The router dispatches it to the appropriate specialized agent.
    """

    def __init__(self, router: A2ARouter):
        if router is None:
            raise ValueError(
                "LocalA2ATransport requires an A2ARouter"
            )

        self.router = router

    def send(self, message: A2ARequest) -> A2AResponse:
        """
        Send an A2A request through the local transport.

        No network communication occurs here.
        """

        if not isinstance(message, A2ARequest):
            raise TypeError(
                "LocalA2ATransport.send expects an A2ARequest"
            )

        return self.router.send(message)