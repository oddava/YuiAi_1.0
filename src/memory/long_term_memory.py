import traceback
import uuid
from datetime import datetime
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from torch.nn.functional import cosine_similarity
import logging

# Set up the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load model globally to avoid repeated initialization
model = SentenceTransformer('sentence-transformers/paraphrase-MiniLM-L6-v2')

def get_embedding(text):
    """
    Converts a text input to an embedding using the model.
    Handles multiple text types and ensures a single string input.
    """
    try:
        if isinstance(text, list):
            text = " ".join(text) if all(isinstance(i, str) for i in text) else text[0]
        if not isinstance(text, str):
            raise ValueError(f"Invalid text input: {text}")
        return model.encode(text)
    except Exception as e:
        logger.info(f"[ERROR] Failed to encode text: {text}, Error: {e}")
        return None

def calculate_utility_score(text, keywords=None):
    """
    Calculates a utility score based on text length and the presence of keywords.
    Length score is capped at 1, keyword score is weighted.
    """
    length_score = min(len(text) / 100, 1)
    keyword_score = (
        sum(1 for word in (keywords or []) if word.lower() in text.lower()) / len(keywords)
        if keywords else 0
    )
    return 0.7 * length_score + 0.3 * keyword_score

def is_valid_embedding(embedding):
    """
    Checks if an embedding is valid (non-None, numpy array, and not empty).
    """
    return embedding is not None and isinstance(embedding, np.ndarray) and embedding.size > 0

def store_memory(query, response, collection, keywords=None):
    """
    Stores a query-response pair in memory with metadata, ensuring no duplicate or similar entries.
    """
    if not collection:
        logger.info(f"[ERROR] Collection is None. Cannot store memory.")
        return

    def validate_and_get_embedding(text):
        embedding = get_embedding(text)
        if not is_valid_embedding(embedding):
            raise ValueError(f"Invalid embedding for text: {text}")
        return embedding

    def compute_similarity(embedding1, embedding2):
        return cosine_similarity(
            torch.tensor(embedding1).unsqueeze(0),
            torch.tensor(embedding2).unsqueeze(0)
        ).item()

    def prepare_metadata(text, t_type):
        return {
            "timestamp": datetime.now().isoformat(),
            "type": t_type,
            "utility_score": calculate_utility_score(text, keywords),
        }

    try:
        # Check for existing similar memories
        existing_results = collection.query(query_texts=[query], n_results=1)
        if existing_results.get('documents') and existing_results['documents'][0]:
            stored_query = existing_results['documents'][0][0]
            stored_query_embedding = validate_and_get_embedding(stored_query)
            query_embedding = validate_and_get_embedding(query)

            if compute_similarity(query_embedding, stored_query_embedding) >= 0.5:
                logger.info(f"[INFO] Similar memory already exists. Skipping storage.")
                return
        else:
            logger.info(f"[INFO] No similar memory found. Proceeding with storage.")

        # Validate embeddings for query and response
        query_embedding = validate_and_get_embedding(query)
        response_embedding = validate_and_get_embedding(response)

        # Store data in the collection
        collection.add(
            documents=[query, response],
            metadatas=[prepare_metadata(query, "user_query"), prepare_metadata(response, "yui_response")],
            embeddings=[query_embedding.tolist(), response_embedding.tolist()],
            ids=[str(uuid.uuid4()), str(uuid.uuid4())]
        )
        logger.info(f"[INFO] Memory stored successfully.")

    except Exception as e:
        logger.info(f"[ERROR] Failed to store memory: {e}")
        traceback.print_exc()


def format_memory_concise(results):
    """
    Format memory results concisely for display or further processing.
    Handles cases where metadata is missing or None.
    """
    formatted_memory = []

    for metadata in results.get("metadatas", [])[0]:
        if metadata:
            timestamp = metadata.get("timestamp", "Unknown")
            entry_type = metadata.get("type", "Unknown")
            utility_score = metadata.get("utility_score", "Unknown")
            formatted_memory.append(f"Timestamp: {timestamp}, Type: {entry_type}, Utility Score: {utility_score}")
        else:
            formatted_memory.append("Missing metadata entry.")

    return "\n".join(formatted_memory)