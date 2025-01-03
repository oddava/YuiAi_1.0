# import asyncio
# import os
# from dotenv import load_dotenv
# from langchain_core.tools import tool
# from telethon import TelegramClient, errors
# import logging
#
# load_dotenv()
#
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
#
# API_ID = os.getenv("API_ID")
# API_HASH = os.getenv("API_HASH")
# PHONE_NUMBER = os.getenv("PHONE_NUMBER")
#
# client = TelegramClient("session_name", API_ID, API_HASH)
# async def fetch_telegram_entities(entity_type, count):
#     valid_types = {"user", "bot", "channel", "group", "chat", "all"}
#     if entity_type not in valid_types:
#         raise ValueError(f"Invalid entity type: {entity_type}. Valid types are {valid_types}.")
#
#     try:
#         await client.start()
#
#         # Fetch dialogs (chats, channels, and groups the user is part of)
#         dialogs = await client.get_dialogs(limit=None)  # Fetch all available dialogs
#         formatted_entities = []
#
#         for dialog in dialogs:
#             entity = dialog.entity
#             entity_type_actual = None
#
#             if hasattr(entity, "bot") and entity.bot:
#                 entity_type_actual = "bot"
#             elif hasattr(entity, "megagroup") and not entity.megagroup:
#                 entity_type_actual = "channel"
#             elif hasattr(entity, "megagroup") and entity.megagroup:
#                 entity_type_actual = "group"
#             elif hasattr(entity, "title"):
#                 entity_type_actual = "chat"
#             elif hasattr(entity, "first_name"):
#                 entity_type_actual = "user"
#
#             if entity_type == "all" or entity_type == entity_type_actual:
#                 formatted_entities.append({
#                     "id": entity.id,
#                     "username": getattr(entity, "username", None),
#                     "first_name": getattr(entity, "first_name", None),
#                     "last_name": getattr(entity, "last_name", None),
#                     "title": getattr(entity, "title", None),  # For channels/groups/chats
#                     "type": entity_type_actual,
#                 })
#
#         # Limit the number of results
#         return formatted_entities[:count]
#
#     except errors.UnauthorizedError:
#         print("Unauthorized access. Please check your API credentials.")
#         return []
#     except Exception as e:
#         print(f"An unexpected error occurred: {e}")
#         return []
#     finally:
#         await client.disconnect()
#
# @tool
# def sync_fetch_entities(entity_type, count):
#     """
#     A tool to fetch a list of Telegram entities based on type, use with caution
#
#     Parameters:
#         entity_type (str): Specifies the entity type ("user", "bot", "channel", "group", "chat", or "all").
#         count (int): The number of results to return.
#
#     Returns:
#         list: A list of dictionaries with formatted entity data.
#
#     Raises:
#         ValueError: If an invalid entity type is provided.
#         Exception: For other unexpected errors.
#     """
#     try:
#         result = asyncio.run(fetch_telegram_entities(entity_type, count))
#         return result
#     except ValueError as ve:
#         print(f"Validation error: {ve}")
#         return []
#     except Exception as e:
#         print(f"An unexpected error occurred: {e}")
#         return []