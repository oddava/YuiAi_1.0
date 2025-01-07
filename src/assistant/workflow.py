from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.mongodb import MongoDBSaver
from langgraph.prebuilt import ToolNode
from pymongo import MongoClient

from src.agents.langgraph_agent import MemoryAgent, SummarizationAgent, ConversationAgent, ProfileAgent
from src.agents.utils import tools
from src.assistant.state import State
from langgraph.graph import StateGraph, START, END
import os
MONGODB_URI = os.environ.get("MONGODB_URI")

def should_continue(state: State):
    last_message = state["messages"][-1]
    total_messages = len(state["messages"])

    if last_message.tool_calls:
        return "tool_agent"

    elif total_messages > 15:
        return "profile_agent"

    return END


def tool_agent_callback(result):
    # Forward tool results back to the conversation agent or the next node
    return workflow.add_node("conversation_agent", result)


# --- Workflow Definition ---
workflow = StateGraph(State)

# Define agents
memory_agent = MemoryAgent()
summarization_agent = SummarizationAgent()
conversation_agent = ConversationAgent()
profile_agent = ProfileAgent()
tool_agent = ToolNode(tools=tools)

# Add nodes
workflow.add_node("memory_agent", memory_agent.invoke)
workflow.add_node("summarization_agent", summarization_agent.invoke)
workflow.add_node("conversation_agent", conversation_agent.invoke)
workflow.add_node("tool_agent", tool_agent)
workflow.add_node("profile_agent", profile_agent.invoke)

# Add edges
workflow.add_edge(START, "memory_agent")
workflow.add_edge("memory_agent", "conversation_agent")
workflow.add_conditional_edges("conversation_agent", should_continue)
workflow.add_edge("tool_agent", "conversation_agent")
workflow.add_edge("profile_agent", "summarization_agent")
workflow.add_edge("summarization_agent", END)

mongodb_client = MongoClient(MONGODB_URI)
checkpointer = MongoDBSaver(mongodb_client)
# checkpointer = MemorySaver()

graph = workflow.compile(
    checkpointer=checkpointer,
)