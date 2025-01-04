import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import logging

# Load environment variables
load_dotenv()

# Set up the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure the bot token is set
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN is not set in the environment variables.")
    raise RuntimeError("TELEGRAM_BOT_TOKEN is required to run the bot.")

# Initialize FastAPI app
app = FastAPI()

# Set up the bot
application = Application.builder().token(TOKEN).build()

# Import and add handlers
from src.assistant.handlers import start, handle_message, handle_voice_message

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))

# Define webhook endpoint
@app.post("/webhook")
async def webhook(request: Request):
    try:
        # Parse the incoming update
        data = await request.json()
        update = Update.de_json(data, application.bot)

        # Log the update for debugging
        logger.info(f"Received update: {data}")

        # Process the update
        await application.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}

# Define a health check endpoint
@app.get("/")
async def home():
    return {"status": "Bot is running"}

if __name__ == "__main__":
    # Use PORT from environment or default to 5000
    port = int(os.getenv("PORT", 5000))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
