from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_groq import ChatGroq
import os
import chromadb
from chromadb import Settings
import logging

from src.tools.fetch_entities import sync_fetch_telegram_entities
# from src.tools.send_message import sync_send_message
from src.tools.sticker_sender import sync_send_sticker

# Set up the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
WORKER_LLM_NAME = os.getenv("WORKER_LLM_NAME")
CHAT_LLM_NAME = os.getenv("CHAT_LLM_NAME")
PERSIST_DIR = os.getenv("PERSIST_DIR")
STICKER_SET_NAME = os.getenv("STICKER_SET_NAME")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

client = chromadb.PersistentClient(path=PERSIST_DIR, settings=Settings(anonymized_telemetry=False))
collection = client.get_or_create_collection(name="assistant_memory")

llm = ChatGroq(groq_api_key=GROQ_API_KEY, model_name=CHAT_LLM_NAME)
tavily_search = TavilySearchResults(max_results=3)

tools = [tavily_search, sync_send_sticker, sync_fetch_telegram_entities]
llm_with_tools = llm.bind_tools(tools)
llm_for_check = ChatGroq(groq_api_key=GROQ_API_KEY, model_name=WORKER_LLM_NAME)

def get_relevant_memory(query: str, n_results: int):
    # Query memory database
    relevant_memory = collection.query(query_texts=[query], n_results=n_results)
    relevant_memory = format_memory(relevant_memory)

    return {"relevant_memory": relevant_memory}

def format_memory(raw_memory):
    """
    Simplifies raw memory data into a concise, AI-friendly format.
    """
    if not raw_memory or "documents" not in raw_memory or not raw_memory["documents"]:
        return "[ERROR] Invalid memory data."

    documents = raw_memory["documents"][0]
    metadatas = raw_memory.get("metadatas", [[]])[0]

    relevant_memory = []
    for doc, meta in zip(documents, metadatas):
        relevant_memory.append({
            "content": doc,
            "timestamp": meta.get("timestamp", "Unknown"),
            "type": meta.get("type", "Unknown"),
            "utility_score": meta.get("utility_score", 0)
        })

    return relevant_memory