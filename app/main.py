from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
import json
import logging
import os
import uuid
from dotenv import load_dotenv
load_dotenv()
from .retrieval import FAQRetriever
from .models import ChatRequest, ChatResponse
from .response import build_messages, call_llm, rewrite_query
from .utils import is_follow_up_question, trim_history_to_last_n_turns
from .mock import call_mock_llm

# In-memory store: conversation_id -> history list
conversation_histories: dict[str, list[dict]] = {}

USE_MOCK_GEMINI = os.getenv("USE_MOCK_GEMINI", "false").lower() == "true"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
def chat(request: Request, req: ChatRequest) -> ChatResponse:
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    user_message = req.message
    # Resolve history: use stored history for this conversation_id if present, else request history
    conversation_id = (req.conversation_id or "").strip()
    logger.info("request_id=%s Current conversation_histories store: %s", request_id, conversation_histories)
    
    if conversation_id and conversation_id in conversation_histories:
        history = list(conversation_histories[conversation_id])
        logger.info("request_id=%s History recovered for conversation_id=%s", request_id, conversation_id)
    else:
        history = list(req.history) if req.history else []
        if conversation_id:
            logger.info("request_id=%s No history found for conversation_id=%s; creating new history", request_id, conversation_id)
        else:
            logger.info("request_id=%s No conversation_id provided; starting fresh history", request_id)
    logger.info("request_id=%s Received input: message=%s", request_id, (user_message or "")[:500] or "(empty)")

    # Handle empty or whitespace-only input gracefully.
    if not user_message or not user_message.strip():
        logger.info("request_id=%s Sending answer: (empty message response)", request_id)
        return ChatResponse(
            answer="It looks like you sent an empty message. Please type a question to get started.",
            sources=[],
            url="",
            memory_used=False,
            history=history  # Return original history
        )
    
    # Determine if the input is a follow-up before doing anything else.
    is_follow_up = is_follow_up_question(user_message, history)
    
    # The `memory_used` flag should reflect if this is a follow-up turn.
    # If it's not a follow-up, we are starting a new context, so memory from the prior turn is not used.
    memory_used = bool(history)
    

    history.append({"role": "user", "content": user_message})

    if is_follow_up and not USE_MOCK_GEMINI:
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
        if USE_MOCK_GEMINI:
            history.append({"role": "Edited user", "content": "No rewrite needed (mock mode)"})
        else:
            history.append({"role": "Edited user", "content": "No rewrite needed"})

    # Now, retrieve the FAQ using the determined search_query.
    relevant_faq = retriever.find_best_match(search_query)
    
    answer = ""
    sources = []
    if relevant_faq:
        # If there is a relevant FAQ, try the real LLM first, fallback to mock LLM if it fails
        faq_question = relevant_faq.get("question", "No question found.")
        history.append({"role": "Matched FAQ", "content": f"Found: {faq_question}"})
        sources = [faq_question]
        messages = build_messages(user_message, relevant_faq, history if is_follow_up else None)
        try:
            answer = call_llm(messages)
            logger.info("request_id=%s LLM call succeeded (FAQ match).", request_id)
        except Exception:
            # Fall back to deterministic mock LLM
            logger.info("request_id=%s LLM call failed, falling back to mock LLM (FAQ match).", request_id)
            answer = call_mock_llm(relevant_faq, is_follow_up=is_follow_up)
    else:
        # No relevant FAQ found -- try LLM fallback, else use our canned response, else fallback to mock LLM
        history.append({"role": "Matched FAQ", "content": "No relevant FAQ found."})
        try:
            answer = call_llm([
                {"role": "user", "parts": [{"text": user_message}]}
            ])
            logger.info("request_id=%s LLM call succeeded (no FAQ match).", request_id)
        except Exception:
            # Fallback: canned not-found answer
            logger.info("request_id=%s LLM call failed, falling back to mock LLM (no FAQ match).", request_id)
            answer = "I'm sorry, I'm not sure how to help with that. Could you please rephrase your question or ask about a new topic?"
            # As a final fallback, call mock LLM with None
            try:
                answer = call_mock_llm(None, is_follow_up=is_follow_up)
            except Exception:
                pass  # if even this fails, use canned above
        sources = []    
    
    faq_url = relevant_faq.get("url", "") if relevant_faq else ""
    history.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
        "url": faq_url,
    })

    # Keep only the last 5 user/assistant turns.
    history = trim_history_to_last_n_turns(history, n=5)

    logger.info("request_id=%s conversation_id=%s", request_id, conversation_id)
    if conversation_id:
        conversation_histories[conversation_id] = history

    logger.info("request_id=%s Sending answer: %s", request_id, (answer or "")[:500] or "(empty)")
    return ChatResponse(
        answer=answer,
        sources=sources,
        url=faq_url,
        memory_used=memory_used,
        history=history
    )

# Mount the parent directory to serve index.html, styles.css, and app.js
# We place this at the end to ensure specific routes like /chat are matched first.
app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "frontend"), html=True), name="static")