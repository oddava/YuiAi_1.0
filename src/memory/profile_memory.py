import json
from langchain_core.messages import HumanMessage, AIMessage
from src.agents.utils import llm
import logging
from typing import Dict

# Set up the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_profile(profile: Dict, conversation):
    """Update the user's profile based on recent conversation."""
    # Preprocess conversation to extract meaningful details

    prompt = (
        "### User Profile Update Task ###\n\n"
        "#### Current User Profile ####\n"
        f"{json.dumps(profile, indent=2)}\n\n"
        "#### Recent Conversation ####\n"
        f"{json.dumps(conversation, indent=2)}\n\n"
        "#### Task Instructions ####\n"
        "Analyze the provided user profile and recent conversation to update the profile, following these rules:\n\n"
        "1. **Analyze the Conversation**:\n"
        "   - Identify explicitly stated user attributes.\n"
        "   - Do not infer or guess attributes.\n\n"
        "2. **Update the Profile**:\n"
        "   - Modify existing attributes if explicitly mentioned.\n"
        "   - Add new attributes explicitly stated, using the correct data types:\n"
        "     - Strings for single values (e.g., `name`, `email`).\n"
        "     - Lists of strings for multiple values (e.g., `interests`, `skills`).\n"
        "     - Dictionaries for locations (e.g., `{'city': 'X', 'state': 'Y', 'country': 'Z'}`).\n"
        "   - Retain attributes not explicitly mentioned.\n\n"
        "3. **Output Format**:\n"
        "   - Return the updated profile as valid JSON if changes are made.\n"
        "   - If no changes are necessary, return the original profile EXACTLY as valid JSON.\n"
        "   - Do not include explanations, code blocks, or any text outside the JSON.\n\n"
        "#### Example Outputs ####\n"
        "1. **With Updates**:\n"
        "{\n"
        '  "name": "John Doe",\n'
        '  "interests": ["reading", "traveling", "coding"],\n'
        '  "location": {"city": "San Francisco", "state": "CA", "country": "USA"}\n'
        "}\n\n"
        "2. **Without Updates**:\n"
        "{\n"
        '  "name": "John Doe",\n'
        '  "interests": ["reading", "traveling"],\n'
        '  "location": {"city": "New York", "state": "NY", "country": "USA"}\n'
        "}\n\n"
        "Return only the JSON object."
    )

    try:
        response = llm.invoke([HumanMessage(content=prompt)]).content
        logger.debug(f"[DEBUG] Raw profile updater LLM Response:\n{response}")

        updated_profile = json.loads(response)

        # Validate and return updated profile
        if isinstance(updated_profile, dict):
            return updated_profile
        else:
            raise ValueError("Invalid response format.")
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON response: {e}. Response: {response}")
    except Exception as e:
        logger.error(f"Error updating profile: {e}")

    return profile

PROFILE_FILE = "profile.json"

def load_profile():
    """Loads user profile from file."""
    if PROFILE_FILE:
        try:
            with open(PROFILE_FILE, "r") as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            logger.error(f"[ERROR] Failed to load profile: {e}")
    return {}

def save_profile(profile):
    try:
        with open(PROFILE_FILE, "w") as f:
            json_data = json.dumps(profile, indent=2)
            logger.info(f"[DEBUG] Saving profile data: {json_data}")
            f.write(json_data)
    except IOError as e:
        logger.error(f"[ERROR] Error saving profile to file: {e}")


def simplify_conversation(conversation):
    """
    Simplifies incoming conversations for AI processing.
    Handles cases where there are fewer than 5 conversations.
    """
    try:
        # Extract user and AI messages
        user_messages = [msg.content for msg in conversation if isinstance(msg, HumanMessage)]
        ai_messages = [msg.content for msg in conversation if isinstance(msg, AIMessage)]

        # Ensure we handle fewer messages gracefully
        max_conversations = min(len(user_messages), len(ai_messages), 5)
        simplified_conversation = [
            {"user": user_messages[-i], "assistant": ai_messages[-i]}
            for i in range(1, max_conversations + 1)
        ][::-1]

        return simplified_conversation
    except Exception as e:
        logger.error(f"[ERROR] Simplifying conversation failed: {e}")
        return []
