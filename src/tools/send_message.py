# import asyncio
# import json
# import os
# from dotenv import load_dotenv
# from langchain_core.tools import tool
# from telethon import TelegramClient
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
#
# async def send_message(username, message):
#     """Send a message to a selected user asynchronously"""
#     try:
#         if not client.is_connected():
#             logger.info("Connecting to Telegram...")
#             await client.start()
#         if not await client.is_user_authorized():
#             logger.info("Not authorized. Please log in.")
#             await client.send_code_request(PHONE_NUMBER)
#             code = input("Enter the code: ")
#             await client.sign_in(PHONE_NUMBER, code)
#             logger.info("Successfully logged in!")
#
#         # Check if message content is a string
#         if not isinstance(message, str):
#             raise ValueError("The message content must be a string.")
#
#         entity = await client.get_entity(username)
#         await client.send_message(entity, message)
#         return f"Message sent to {username}: {message}"
#     except Exception as e:
#         logger.error(f"Failed to send message: {e}")
#         return f"Failed to send message to {username}: {e}"
#     finally:
#         await client.disconnect()
#
# async def async_send_message_wrapper(username, message):
#     result = await send_message(username, message)
#     return result
#
# @tool
# def sync_send_message(username, message):
#     """Send a message to a specific Telegram user. This tool should only be used with explicit permission and clear instructions to send a message."""
#     global loop
#     try:
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#         result = loop.run_until_complete(async_send_message_wrapper(username, message))
#         return result
#     finally:
#         loop.close()