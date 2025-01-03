from dotenv import load_dotenv
from groq import Groq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from telegram import Update
import os
from telegram.helpers import escape_markdown
import logging

load_dotenv()

# Set up the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
async def send_markdown_message(update, text):
    """
    Sends a message with Markdown formatting safely by escaping special characters.
    """
    try:
        await update.message.reply_text(text, parse_mode="markdown")
    except Exception as e:
        logger.error(f"[SKIP THIS ERROR]]Error sending message: {e}")
        await update.message.reply_text(text)


# --- Streaming Updates ---
async def stream_graph_updates(update, context, user_input, graph):
    thread_id = update.message.chat_id

    system_message = (
        "You are Yui, a cheerful and graceful anime girl with a lively, warm, and expressive personality. Stay in character and respond with charm, humor, and empathy. "
    )

    events = graph.stream(
        {"messages": [SystemMessage(system_message), HumanMessage(content=user_input)]},
        {"configurable": {"thread_id": thread_id, "user_id": update.message.chat_id}},
        stream_mode="values"
    )

    sent_messages = set()

    try:
        for event in events:
            if "messages" in event:
                last_message = event["messages"][-1]

                if hasattr(last_message, "tool_calls"):
                    for tool_call in last_message.tool_calls:
                        tool_name = tool_call.get("name", "")

                        # Handle specific tool: 'send_message'
                        if tool_name == "sync_send_message":
                            args = tool_call.get("args", {})
                            username = args.get("username", "Unknown")
                            message = args.get("message", "No message provided")

                            # Notify the user about the tool usage
                            await update.message.reply_text(
                                f"📤 A message has been sent to {username}:\n\n{message}",
                            )
                        elif tool_name == "tavily_search_results_json":
                            args = tool_call.get("args", {})
                            description = args.get("query", "Unknown")

                            await update.message.reply_text(
                                f"Searching *{description}*",
                                parse_mode="markdown"
                            )

                # Send AI messages to the user
                if last_message.content not in sent_messages:
                    sent_messages.add(last_message.content)
                    if isinstance(last_message, AIMessage) and last_message.content:
                        await send_markdown_message(update, last_message.content)
    except GeneratorExit:
        logger.error("Generator closed unexpectedly.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        # Ensure generator cleanup
        if hasattr(events, "close"):
            events.close()


GROQ_STT_MODEL_NAME = os.environ.get("GROQ_STT_MODEL_NAME")
def transcribe_audio(file_path: str):
    """Transcribe an audio file using Groq."""
    client = Groq()

    with open(file_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(file_path, file.read()),
            model=GROQ_STT_MODEL_NAME,
            response_format="json",
            temperature=0.0,
            language="en"
        )

        return transcription.text