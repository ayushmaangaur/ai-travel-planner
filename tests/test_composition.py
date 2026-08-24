from unittest.mock import MagicMock

from app.composition import (
    create_local_agent,
    create_http_agent,
)

from agents.root_agent import RootTravelAgent
from a2a.local_transport import LocalA2ATransport
from a2a.http_transport import HTTPA2ATransport


def test_create_local_agent():
    agent = create_local_agent()

    assert isinstance(agent, RootTravelAgent)
    assert isinstance(
        agent.a2a_transport,
        LocalA2ATransport
    )


def test_create_http_agent():
    agent = create_http_agent(
        "http://localhost:8000"
    )

    assert isinstance(agent, RootTravelAgent)
    assert isinstance(
        agent.a2a_transport,
        HTTPA2ATransport
    )


def test_create_http_agent_passes_configuration():
    agent = create_http_agent(
        "http://localhost:9000/",
        timeout=5.0,
    )

    assert agent.a2a_transport.base_url == (
        "http://localhost:9000"
    )

    assert agent.a2a_transport.timeout == 5.0