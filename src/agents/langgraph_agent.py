from typing import Dict
from dotenv import load_dotenv
from langchain.memory import chat_memory

from src.agents.utils import collection, get_relevant_memory, llm, llm_with_tools
from src.memory.long_term_memory import store_memory
from langchain_core.messages import HumanMessage, RemoveMessage, SystemMessage, AIMessage
import logging
from src.memory.profile_memory import load_profile, save_profile, update_profile, \
    simplify_conversation

# Set up the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

class SummarizationAgent:
    def invoke(self, state: Dict):
        logger.info("[DEBUG] Summarizing conversation...")

        summary = state.get("summary", "")
        summary_prompt = (
            f"Update the following summary with new conversation provided. The summary should be a concise, bulleted list of key actions and decisions. Keep the length around 800 characters. Existing summary: {summary}\n\nNew messages:\n"
            if summary
            else "Summarize the following conversation as a concise, bulleted list of key actions and decisions:\n"
        )

        messages = state["messages"] + [HumanMessage(content=summary_prompt)]

        response = llm.invoke(messages)
        logger.info(f"[DEBUG] Summarized: {response.content}")
        delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-5]]
        logger.info(f"[DEBUG] Deleting messages: {[m.id for m in state['messages'][:-5]]}")

        return {"summary": response.content, "messages": delete_messages}


class ConversationAgent:
    def invoke(self, state: Dict):
        logger.info(f"[DEBUG] Invoking conversation agents...")
        state.update({"summary": ""})

        summary = state.get("summary", "")
        relevant_memory = state.get("relevant_memory", "")
        profile_memory = state.get("profile", load_profile())

        system_message = (
            "You are Yui, a graceful anime girl with a lively, warm, and expressive personality."
            "Always stay in character as a caring and imaginative heroine, blending charm, humor, and empathy in your responses. "
            "You may use the information below if it's relevant:\n\n"
            f"Summary of the conversation earlier: {summary} | Relevant memories: {relevant_memory} | Profile: {profile_memory}"
        )
        logger.info(f"[DEBUG] Total messages:\n {len(state['messages'])}")
        logger.info(f"[DEBUG] System Message:\n {system_message}")
        messages = [SystemMessage(content=system_message)] + state["messages"]

        response = llm_with_tools.invoke(messages)
        logger.info(f"[DEBUG] Chatbot response: {response.content}")

        latest_human_message = state["messages"][-1].content
        store_memory(latest_human_message, response.content, collection)
        logger.info(f"[INFO]Memory Stored Successfully")

        return {"messages": [response]}

#---------- PROFILE -------------#
class ProfileAgent:
    def invoke(self, state):
        logger.info("[DEBUG] Invoking profile agent...")

        # Extract conversation messages
        conversation = state.get("messages", [])
        profile = state.get("profile", "")

        try:
            conversation = simplify_conversation(conversation)
            updated_profile = update_profile(profile, conversation)
            print(f"[DEBUG] Profile Updated: {updated_profile}")
            state.update({"profile": updated_profile})
            save_profile(updated_profile)
        except Exception as e:
            logger.error(f"[ERROR] Could not update or save profile: {e}")
            return {"error": str(e)}

        return {"profile": updated_profile}

#---------- MEMORY -------------#
class MemoryAgent:
    def invoke(self, state: Dict):
        logger.info(f"[DEBUG] Retrieving relevant memory...")
        query = state["messages"][-1].content
        updated_memory = get_relevant_memory(query, 3)
        logger.info(f"[DEBUG] Fetched Relevant Memory: {updated_memory}")
        state.update(updated_memory)
        return state