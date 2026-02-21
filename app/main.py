from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import json
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

from .retrieval import FAQRetriever
from .models import ChatRequest, ChatResponse
from .response import build_messages, call_llm, rewrite_query
from .utils import is_follow_up_question

# Load the FAQ data from the JSON file
FAQ_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "SEED_DATA", "epic_vendor_faq.json")
with open(FAQ_FILE_PATH, 'r') as f:
    faq_data = json.load(f)

# Create a single, pre-computed retriever instance when the app starts.
retriever = FAQRetriever(faq_data)

# Define a constant for the maximum history length
MAX_HISTORY_LENGTH = 20

app = FastAPI()

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    # Extract the user's message and conversation history from the request
    user_message = req.message
    history = req.history
    memory_used = bool(history)
    
    # Determine if the input is a follow-up before doing anything else.
    is_follow_up = is_follow_up_question(user_message, history)
    
    # If it is not a follow-up, we treat it as a new conversation, so memory is not used for generation.
    if not is_follow_up:
        memory_used = False

    history.append({"role": "user", "content": user_message})

    if is_follow_up:
        # If it's a follow-up, rewrite it to be a standalone query for better searching.
        try:
            search_query = rewrite_query(user_message, history[:-1])
        except Exception:
            # Fallback: If rewrite fails (LLM error), use the original message.
            search_query = user_message
            
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
        sources = [faq_question]
        
        # Generate a conversational answer using the LLM with the FAQ as context.
        # Only include history if it is a follow-up; otherwise, treat it as a fresh query.
        messages = build_messages(user_message, relevant_faq, history if is_follow_up else None)
        
        try:
            answer = call_llm(messages)
        except Exception:
            # Fallback: If LLM generation fails, provide a safe fallback using the retrieved data.
            answer = f"I found a relevant FAQ, but I'm having trouble generating a conversational response right now. \n\n**Question:** {faq_question}\n**Answer:** {relevant_faq.get('answer', 'Please check the source link.')}"

        # If it's not a follow-up, we can clear the history to avoid confusion in future interactions.
        if not is_follow_up:
            # Reset history to keep only the current turn (User, Edited User, Matched FAQ)
            history = history[-3:]
    else:
        # --- Case 2: No relevant FAQ was found. ---
        history.append({"role": "Matched FAQ", "content": "No relevant FAQ found."})
        
        # Fallback for when no FAQ is found
        answer = "I'm sorry, I'm not sure how to help with that. Could you please rephrase your question or ask about a new topic?"
    
    history.append({"role": "assistant", "content": answer})

    # Limit history to prevent context overflow.
    if len(history) > MAX_HISTORY_LENGTH:
        history = history[-MAX_HISTORY_LENGTH:]

    return ChatResponse(
        answer=answer,
        sources=sources,
        url=relevant_faq.get("url", "") if relevant_faq else "",
        memory_used=memory_used,
        history=history
    )

# Mount the parent directory to serve index.html, styles.css, and app.js
# We place this at the end to ensure specific routes like /chat are matched first.
app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "frontend"), html=True), name="static")