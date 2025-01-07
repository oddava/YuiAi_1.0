import json
from langchain_core.messages import HumanMessage, AIMessage
from src.agents.utils import llm, llm_for_check
import logging
from typing import Dict

# Set up the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_profile(profile: Dict, conversation):
    """
    Update the user's profile based on recent conversation.
    Handles malformed responses gracefully.
    """
    if not isinstance(profile, dict):
        profile = {}

    prompt = (
        "### User Profile Update Task ###\n\n"
        "#### Current User Profile ####\n"
        f"{json.dumps(profile, indent=2)}\n\n"
        "#### Recent Conversation ####\n"
        f"{json.dumps(conversation, indent=2)}\n\n"
        "#### Instructions ####\n"
        "Analyze the 'Current User Profile' and the 'Recent Conversation' to update the profile. Follow these strict rules:\n\n"
        "1. **Analysis Rules**:\n"
        "   - Only modify or add attributes explicitly mentioned in the 'Recent Conversation'.\n"
        "   - Retain all attributes from the 'Current User Profile' that are not explicitly referenced in the 'Recent Conversation'.\n"
        "   - Do not infer or guess any information. Use only explicit details.\n\n"
        "2. **Attribute Types**:\n"
        "   - For single-value fields, use strings (e.g., \"name\": \"John Doe\").\n"
        "   - For multi-value fields, use lists of strings (e.g., \"interests\": [\"reading\", \"traveling\"]).\n"
        "   - For location fields, use a dictionary structure (e.g., \"location\": {\"city\": \"New York\", \"state\": \"NY\", \"country\": \"USA\"}).\n"
        "   - Preserve data types of all existing attributes in the profile.\n\n"
        "3. **Format Rules**:\n"
        "   - Your response must be **strictly valid JSON**.\n"
        "   - Do not include any text, comments, or explanations outside the JSON object.\n"
        "   - Ensure proper JSON syntax (e.g., double quotes around keys and values, no trailing commas).\n\n"
        "4. **Output Rules**:\n"
        "   - If updates are made, return the updated profile as a valid JSON object.\n"
        "   - If no changes are needed, return the original profile exactly as it is, as a valid JSON object.\n"
        "   - Do not output anything other than the JSON object.\n\n"
        "#### Examples ####\n\n"
        "1. **With Updates**:\n"
        "{\n"
        "  \"name\": \"John Doe\",\n"
        "  \"interests\": [\"reading\", \"traveling\", \"coding\"],\n"
        "  \"location\": {\"city\": \"San Francisco\", \"state\": \"CA\", \"country\": \"USA\"}\n"
        "}\n\n"
        "2. **Without Updates**:\n"
        "{\n"
        "  \"name\": \"John Doe\",\n"
        "  \"interests\": [\"reading\", \"traveling\"],\n"
        "  \"location\": {\"city\": \"New York\", \"state\": \"NY\", \"country\": \"USA\"}\n"
        "}\n\n"
        "### Task ###\n"
        "Return only the updated or original profile as valid JSON."
    )

    try:
        response = llm_for_check.invoke([HumanMessage(content=prompt)]).content
        logger.debug(f"[DEBUG] Raw LLM Response: {response}")

        # Ensure the response is valid JSON
        response = response.strip()
        print(f"[DEBUG]Updated Profile: {response}")
        if not response.startswith("{") or not response.endswith("}"):
            raise ValueError("LLM response is not valid JSON.")

        updated_profile = json.loads(response)

        if not isinstance(updated_profile, dict):
            raise ValueError("LLM response did not return a valid profile dictionary.")

        return updated_profile

    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON response: {e}. Response: {response}")
    except Exception as e:
        logger.error(f"Error updating profile: {e}")

    # Fallback: Return the original profile if any error occurs
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