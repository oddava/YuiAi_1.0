from dotenv import load_dotenv
from telegram.ext import ContextTypes
from telegram import Update
from src.assistant.helper_functions import stream_graph_updates, transcribe_audio
from src.assistant.workflow import graph
import os

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

# Initialize the bot and the Telegram handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your chatbot assistant. Type something to start.")