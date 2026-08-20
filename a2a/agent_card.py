from dataclasses import dataclass, field


VALID_AGENT_NAMES = {
    "root-agent",
    "flight-agent",
    "hotel-agent",
    "weather-agent",
}


@dataclass
class AgentCard:
    name: str
    description: str
    capabilities: list[str]
    endpoint: str

    def __post_init__(self):

        # ----------------------------------------------------
        # Validate agent name
        # ----------------------------------------------------

        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(
                "AgentCard name must be a non-empty string"
            )

        if self.name not in VALID_AGENT_NAMES:
            raise ValueError(
                f"Unsupported agent name: {self.name}"
            )

        # ----------------------------------------------------
        # Validate description
        # ----------------------------------------------------

        if (
            not isinstance(self.description, str)
            or not self.description.strip()
        ):
            raise ValueError(
                "AgentCard description must be a non-empty string"
            )

        # ----------------------------------------------------
        # Validate capabilities
        # ----------------------------------------------------

        if not isinstance(self.capabilities, list):
            raise ValueError(
                "AgentCard capabilities must be a list"
            )

        if not self.capabilities:
            raise ValueError(
                "AgentCard must contain at least one capability"
            )

        for capability in self.capabilities:
            if (
                not isinstance(capability, str)
                or not capability.strip()
            ):
                raise ValueError(
                    "AgentCard capabilities must contain "
                    "non-empty strings"
                )

        # ----------------------------------------------------
        # Validate endpoint
        # ----------------------------------------------------

        if (
            not isinstance(self.endpoint, str)
            or not self.endpoint.strip()
        ):
            raise ValueError(
                "AgentCard endpoint must be a non-empty string"
            )

    def supports(self, capability: str) -> bool:
        """
        Check whether this agent supports a capability.
        """

        return capability in self.capabilities