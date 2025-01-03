import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.ext import ContextTypes
from telegram.request import HTTPXRequest
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from src.assistant.handlers import start, handle_message, handle_voice_message
import logging

# Load environment variables
load_dotenv()

# Set up the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Set up the bot
request = HTTPXRequest(connect_timeout=10, read_timeout=10)
application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).request(request).build()

# Add handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))

# Define webhook endpoint
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"status": "ok"}

# Health check endpoint
@app.get("/")
async def home():
    return {"status": "Bot is running"}
