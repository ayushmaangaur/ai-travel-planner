from agents.root_agent import RootTravelAgent


class ConversationStore:

    def __init__(self):
        self.sessions = {}

    def get_agent(self, conversation_id: str) -> RootTravelAgent:
        if conversation_id not in self.sessions:
            self.sessions[conversation_id] = RootTravelAgent()

        return self.sessions[conversation_id]

    def clear(self, conversation_id: str):
        self.sessions.pop(conversation_id, None)