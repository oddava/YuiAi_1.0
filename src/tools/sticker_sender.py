import json
import random
import requests
import os
from dotenv import load_dotenv
from langchain_core.tools import tool
import asyncio
from telegram import Update
from tenacity import retry_if_exception_type

from src.main import application
from src.tools.youtube_video_downloader import chat_id

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
STICKER_SET_NAME = os.getenv("STICKER_SET_NAME")

# Emotion categorization logic
essential_emotions = {
    "joy": ["😊", "😂", "😁", "😄", "😎", "🥳"],
    "happiness": ["😊", "😂", "😁", "😄", "😎", "🥳"],
    "sadness": ["😢", "😭", "😞", "😔", "😩", "🥺"],
    "anger": ["😡", "😠", "🤬", "👿", "🔥", "🔪"],
    "mad": ["😡", "😠", "🤬", "👿", "🔥", "🔪"],
    "fear": ["😱", "😨", "😰", "😬", "👻"],
    "love": ["❤️", "💖", "💕", "😍", "😘", "💏", "🤗"],
    "surprise": ["😮", "😯", "😲", "🤯", "😳"],
    "disgust": ["🤢", "🤮", "😖", "😷"],
    "neutral": ["😐", "😑", "😶"],
}

# Function to add a sticker set to the bot's list
def add_sticker_set_to_list(sticker_set_name):
    try:
        stickers = get_sticker_set(sticker_set_name, TOKEN)
        categorized_stickers = categorize_stickers_by_emotion(stickers)

        # Merge new stickers with the existing emotion dictionary
        for emotion, new_stickers in categorized_stickers.items():
            if emotion in emotion_dict:
                emotion_dict[emotion].extend(new_stickers)
                emotion_dict[emotion] = list(set(emotion_dict[emotion]))  # Remove duplicates
            else:
                emotion_dict[emotion] = new_stickers

        # Save the updated data to the file
        with open("sticker_set.json", "w") as file:
            json.dump(emotion_dict, file, indent=4)
        print(f"[INFO] Sticker set '{sticker_set_name}' added successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to add sticker set: {e}")

# Function to fetch the sticker set from Telegram
def get_sticker_set(sticker_set_name, bot_token):
    url = f"https://api.telegram.org/bot{bot_token}/getStickerSet"
    response = requests.post(url, json={"name": sticker_set_name})
    if response.status_code == 200:
        sticker_set = response.json()["result"]["stickers"]
        return sticker_set
    else:
        raise Exception("Failed to fetch sticker set.")

# Categorize stickers based on their emoji
def categorize_stickers_by_emotion(stickers):
    emotion_dict = {emotion: [] for emotion in essential_emotions}

    for sticker in stickers:
        emoji = sticker.get("emoji")
        if emoji:
            for emotion, emoji_list in essential_emotions.items():
                if emoji in emoji_list:
                    emotion_dict[emotion].append(sticker["file_id"])

    return emotion_dict

# Load stickers from a file (if available)
def load_stickers_from_file(filename="sticker_set.json"):
    try:
        with open(filename, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print("[INFO] Sticker set not found")
        return
    except Exception as e:
        print(f"[ERROR] Failed to load the sticker pack: {e}")

# Save stickers to a file
def save_stickers_to_file(filename="sticker_set.json"):
    try:
        with open(filename, "w") as file:
            stickers = get_sticker_set(STICKER_SET_NAME, TOKEN)
            sticker_pack = categorize_stickers_by_emotion(stickers)
            json.dump(sticker_pack, file, indent=4)
            print("[INFO] Sticker pack saved")
    except Exception as e:
        print(f"[ERROR] Failed to save sticker set: {e}")

# Initialize emotion dictionary
emotion_dict = load_stickers_from_file()
if not emotion_dict:
    save_stickers_to_file()

# Keep track of already sent stickers
sent_stickers = {}

async def send_sticker_by_emotion(emotion):
    global sent_stickers

    if emotion not in sent_stickers:
        sent_stickers[emotion] = set()

    # Get available stickers excluding already sent ones
    available_stickers = [
        sticker for sticker in emotion_dict.get(emotion, [])
        if sticker not in sent_stickers[emotion]
    ]

    if not available_stickers:
        # Reset the sent stickers for the emotion if all have been used
        sent_stickers[emotion] = set()
        available_stickers = emotion_dict.get(emotion, [])

    if available_stickers:
        # Choose a random sticker and send it
        sticker_id = random.choice(available_stickers)
        url = f"https://api.telegram.org/bot{TOKEN}/sendSticker"

        # Make the request to send the sticker
        try:
            response = requests.post(url, json={"chat_id": chat_id, "sticker": sticker_id})
            # Check the response status
            if response.status_code == 200:
                # Mark the sticker as sent
                sent_stickers[emotion].add(sticker_id)
                return f"(*the sticker has been sent successfully*)"
            else:
                print(f"Failed to send sticker. Status code: {response.status_code}")
        except Exception as e:
            print(f"An error occurred while sending the sticker: {e}")
    else:
        print(f"No stickers available for the emotion: {emotion}")

async def send_sticker_async_wrapper(emotion):
    result = await send_sticker_by_emotion(emotion)
    return result

@tool
def sync_send_sticker(emotion):
    """
    Send a sticker based on the mood or sentinel of your response.

    Parameters:
        emotion (str): One of ["joy", "happiness", "sadness", "anger", "mad", "fear", "love", "surprise", "disgust", "neutral"].
                       Defaults to "neutral" if not provided or invalid.
    """
    return asyncio.run(send_sticker_async_wrapper(emotion))