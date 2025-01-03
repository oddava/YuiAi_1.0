import yt_dlp
import os
import asyncio
from dotenv import load_dotenv
from telegram import Update, InputFile
from langchain_core.tools import tool

load_dotenv()

chat_id = os.getenv("CHAT_ID")
# Configure yt-dlp options
YDL_OPTIONS = {
    'format': 'bestvideo[height<=1080]+bestaudio/best',  # Download up to 1080p or best available quality
    'outtmpl': 'downloads/%(title)s.%(ext)s',  # Save videos in 'downloads' folder
    'quiet': True  # Suppress verbose output
}

# Ensure the downloads folder exists
os.makedirs("downloads", exist_ok=True)

# Asynchronous download function
async def download_video_async(video_url: str):
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(video_url, download=True)
        video_path = f"downloads/{info['title']}.{info['ext']}"
        return video_path, info["title"]
    except Exception as e:
        raise RuntimeError(f"Failed to download video: {e}")

# Telegram integration
async def send_downloaded_video(update: Update, video_url: str):
    """
    Download a YouTube video and send it to the user.
    """
    try:
        await update.message.reply_text(f"Downloading video from: {video_url}...")
        video_path, video_title = await download_video_async(video_url)
        with open(video_path, 'rb') as video_file:
            await update.message.reply_video(InputFile(video_file), caption=f"Here's your video: {video_title}")
    except Exception as e:
        await update.message.reply_text(f"Failed to download video: {e}")

async def youtube_download_tool(video_url: str):
    """
    A YouTube downloader tool to download and send a video to a Telegram user.

    Parameters:
    - video_url: URL of the YouTube video to download.
    """
    from telegram import Bot

    bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    try:
        video_path, video_title = await download_video_async(video_url)
        with open(video_path, 'rb') as video_file:
            await bot.send_video(chat_id=chat_id, video=InputFile(video_file), caption=f"Here's your video: {video_title}")
    except Exception as e:
        await bot.send_message(chat_id=chat_id, text=f"Failed to download video: {e}")

@tool
def sync_youtube_download_tool(video_url: str):
    """
    A wrapper for the asynchronous youtube_download_tool.
    """
    return asyncio.run(youtube_download_tool(video_url))