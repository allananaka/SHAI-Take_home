from fastapi import FastAPI
import json
import os
from dotenv import load_dotenv
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load environment variables from a .env file
load_dotenv()

from .retrieval import FAQRetriever
from .models import ChatRequest, ChatResponse
from .response import build_messages, call_llm, rewrite_query

# Load the FAQ data from the JSON file
FAQ_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "SEED_DATA", "epic_vendor_faq.json")
with open(FAQ_FILE_PATH, 'r') as f:
    faq_data = json.load(f)

# Create a single, pre-computed retriever instance when the app starts.
retriever = FAQRetriever(faq_data)

app = FastAPI()

def is_follow_up_question(user_input: str, history: List[Dict], threshold: float = 0.2) -> bool:
    """
    Checks if the user input is a semantic follow-up to the conversation history.

    This function uses TF-IDF to vectorize the user's input and the entire
    conversation history. It then calculates the cosine similarity between them.

    Args:
        user_input: The user's latest message.
        history: A list of previous messages in the conversation (user and bot).
        threshold: The similarity score above which the input is considered a follow-up.
                   This value may require tuning based on observed performance.

    Returns:
        True if the similarity score is above the threshold, False otherwise.
    """
    # If there's no history, it cannot be a follow-up.
    if not history:
        return False

    # --- New Heuristic ---
    # Short inputs with pronouns are very likely follow-ups. This handles cases
    # like "Who is it for?"
    words = user_input.lower().split()
    # A set of common pronouns and context-dependent words
    contextual_words = {'it', 'they', 'them', 'that', 'those', 'this', 'his', 'her', 'their'}
    # Check if the sentence is short and contains any of these words.
    if len(words) <= 6 and any(word.strip(".,?!") in contextual_words for word in words):
        return True
    # --- End Heuristic ---

    # Join the list of historical messages into a single string.
    history_text = " ".join([msg.get("content", "") for msg in history])

    # Create a TF-IDF Vectorizer.
    vectorizer = TfidfVectorizer()

    # Generate TF-IDF vectors for the history and the new user input.
    # The fit_transform method creates a vocabulary and transforms the texts in one step.
    try:
        tfidf_matrix = vectorizer.fit_transform([history_text, user_input])
    except ValueError:
        # This can happen if the vocabulary is empty (e.g., all stop words).
        return False

    # Calculate the cosine similarity between the history vector and the input vector.
    # The result is a 2x2 matrix; the value at [0, 1] is the one we need.
    similarity_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

    # Return True if the similarity score exceeds our defined threshold.
    return similarity_score > threshold

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    user_message = req.message
    history = req.history
    memory_used = bool(history)
    
    # Determine if the input is a follow-up before doing anything else.
    is_follow_up = is_follow_up_question(user_message, history)

    history.append({"role": "user", "content": user_message})

    if is_follow_up:
        # If it's a follow-up, rewrite it to be a standalone query for better searching.
        search_query = rewrite_query(user_message, history[:-1])
        history.append({"role": "Edited user", "content": search_query})
    else:
        # If it's a new topic, use the message directly. No rewrite needed.
        search_query = user_message
        history.append({"role": "Edited user", "content": "No rewrite needed"})

    # Now, retrieve the FAQ using the determined search_query.
    relevant_faq = retriever.find_best_match(search_query)
    
    answer = ""
    sources = []

    if relevant_faq:
        # --- Case 1: A relevant FAQ was found. ---
        faq_question = relevant_faq.get("question", "No question found.")
        history.append({"role": "Matched FAQ", "content": f"Found: {faq_question}"})
        sources = [f"{faq_question} (ID: {relevant_faq.get('id', 'Unknown ID')})"]
        
        # Generate a conversational answer using the LLM with the FAQ as context.
        messages = build_messages(user_message, relevant_faq, history)
        answer = call_llm(messages)
    else:
        # --- Case 2: No relevant FAQ was found. ---
        history.append({"role": "Matched FAQ", "content": "No relevant FAQ found."})
        
        # Fallback for when no FAQ is found
        answer = "I'm sorry, I'm not sure how to help with that. Could you please rephrase your question or ask about a new topic?"
    
    history.append({"role": "assistant", "content": answer})

    # Limit history to prevent context overflow.
    if len(history) > 20:
        history = history[-20:]

    return ChatResponse(
        answer=answer,
        sources=sources,
        memory_used=memory_used,
        history=history
    )