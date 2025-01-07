import asyncio
import os
from dotenv import load_dotenv
from langchain_core.tools import tool
from telethon import TelegramClient, errors, functions
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
client = TelegramClient("telethon_session", API_ID, API_HASH)

async def fetch_telegram_entities(entity_type, count):
    valid_types = {"user", "bot", "channel", "group", "chat", "all"}
    if entity_type not in valid_types:
        raise ValueError(f"Invalid entity type: {entity_type}. Valid types are {valid_types}.")

    try:
        await client.start()

        if not client.is_connected():
            raise ConnectionError("Client failed to connect.")

        dialogs = await client.get_dialogs(limit=None)
        print(f"Fetched {len(dialogs)} dialogs.")

        formatted_entities = []
        for dialog in dialogs:
            entity = dialog.entity
            entity_type_actual = None

            if hasattr(entity, "bot") and entity.bot:
                entity_type_actual = "bot"
            elif hasattr(entity, "megagroup") and not entity.megagroup:
                entity_type_actual = "channel"
            elif hasattr(entity, "megagroup") and entity.megagroup:
                entity_type_actual = "group"
            elif hasattr(entity, "title"):
                entity_type_actual = "chat"
            elif hasattr(entity, "first_name"):
                entity_type_actual = "user"

            if entity_type == "all" or entity_type == entity_type_actual:
                formatted_entities.append({
                    "id": entity.id,
                    "username": getattr(entity, "username", None),
                    "first_name": getattr(entity, "first_name", None),
                    "last_name": getattr(entity, "last_name", None),
                    "title": getattr(entity, "title", None),
                    "type": entity_type_actual,
                })

        print(f"Filtered entities: {formatted_entities}")
        return formatted_entities[:count]

    except errors.UnauthorizedError:
        print("Unauthorized access. Please check your API credentials.")
        return ""
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return ""
    finally:
        await client.disconnect()


@tool
def sync_fetch_telegram_entities(entity_type, count):
    """
    A tool to fetch a list of Telegram entities based on type, use with caution

    Parameters:
        entity_type (str): Specifies the entity type ("user", "bot", "channel", "group", "chat", or "all").
        count (int): The number of results to return.

    Returns:
        list: A list of dictionaries with formatted entity data.

    Raises:
        ValueError: If an invalid entity type is provided.
        Exception: For other unexpected errors.
    """
    try:
        result = asyncio.run(fetch_telegram_entities(entity_type, count))
        if not result:
            return ""

        return result
    except ValueError as ve:
        print(f"Validation error: {ve}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []
