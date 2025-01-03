from typing import Annotated, Dict, Any
from langgraph.graph.message import add_messages, MessagesState
from src.agents.langgraph_agent import load_profile
profile = load_profile()

class State(MessagesState):
    messages: Annotated[list, add_messages]
    summary: str
    relevant_memory: str
    profile: Dict[str, Any]