from dotenv import load_dotenv
from telegram.ext import ContextTypes
from telegram import Update
from src.assistant.helper_functions import stream_graph_updates, transcribe_audio
from src.assistant.workflow import graph
import os

from src.memory.profile_memory import load_profile
from src.tools.sticker_sender import load_stickers_from_file, save_stickers_to_file, send_sticker_by_emotion, \
    essential_emotions, add_sticker_set_to_list

# Initialize emotion dictionary
emotion_dict = load_stickers_from_file()
if not emotion_dict:
    save_stickers_to_file()

load_dotenv()
thinking_msg = os.getenv("THINKING_MSG")

# Function to handle incoming messages from Telegram
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()

    loader = await update.message.reply_text(thinking_msg)
    # Stream the updates to the conversation
    await stream_graph_updates(update, context, user_input, graph)

    await loader.delete()

async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming voice messages."""
    global file_path
    thinking_message = await update.message.reply_text(thinking_msg)
    try:
        # Get file information from the voice message
        voice_file = await context.bot.get_file(update.message.voice.file_id)
        file_path = "voice_message.ogg"

        # Download the voice file
        await voice_file.download_to_drive(file_path)

        # Transcribe the audio file (synchronous call)
        transcription = transcribe_audio(file_path)

        # Send the transcription back to the user
        await thinking_message.edit_text(f"Yui heard: <i>{transcription}</i>", parse_mode='HTML')

        # Get bot's response (await this since it's asynchronous)
        await stream_graph_updates(update, context, transcription.strip(), graph)

    except Exception as e:
        await update.message.reply_text(f"Oops, something went wrong:\n{e}")
    finally:
        # Clean up the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)

async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sticker = update.message.sticker
    if not sticker:
        return

    sticker_set_name = sticker.set_name
    emoji = sticker.emoji

    if sticker_set_name:
        # Check if the sticker set is already in the list
        existing_stickers = emotion_dict.get(sticker_set_name, None)
        if not existing_stickers:
            # Add new sticker set
            add_sticker_set_to_list(sticker_set_name)

        # Respond based on the emoji's categorized emotion
        emotion = next(
            (emo for emo, emoji_list in essential_emotions.items() if emoji in emoji_list),
            "neutral",
        )
        await send_sticker_by_emotion(emotion)
        await stream_graph_updates(update, context, f"*received a sticker: sentiment: {emotion}*", graph)

    else:
        await update.message.reply_text("Couldn't process this sticker set.")

# async def handle_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     # summary = state.get("summary", "")
#     # relevant_memory = state.get("relevant_memory", "")
#     profile_memory = load_profile()
#
#     await update.message.reply_text(f"\n\nProfile Memory: {profile_memory}", parse_mode='HTML')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Welcome back, {update.message.from_user.first_name}!")