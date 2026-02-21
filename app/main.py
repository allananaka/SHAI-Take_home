from fastapi import FastAPI
import json
import os
from dotenv import load_dotenv
from .retrieval import FAQRetriever
from .models import ChatRequest, ChatResponse
from .response import build_messages, call_llm, rewrite_query

# Load environment variables from a .env file
load_dotenv()

# Load the FAQ data from the JSON file
FAQ_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "SEED_DATA", "epic_vendor_faq.json")
with open(FAQ_FILE_PATH, 'r') as f:
    faq_data = json.load(f)

# Create a single, pre-computed retriever instance when the app starts.
retriever = FAQRetriever(faq_data)

app = FastAPI()

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # 1. receive user input
    user_message = req.message

    # 2. Rewrite the query to include context from history (e.g., "Who is it for?" -> "Who is Vendor Services for?")
    search_query = rewrite_query(user_message, req.history)

    # 3. Retrieve relevant FAQ using the rewritten query
    relevant_faq = retriever.find_best_match(search_query)
    
    # Prepare for conversation history
    history = req.history
    history.append({"role": "user", "content": user_message})
    history.append({"role": "Edited user", "content": search_query})

    if relevant_faq:
        faq_question = relevant_faq.get("question", "No question found.")
        faq_detailed_answer = relevant_faq.get("answer", "No detailed answer found.")

        # 3. Format the answer using information from the FAQ
        answer = f"{faq_question}\n\n{faq_detailed_answer}"

        history.append({"role": "Matched FAQ", "content": answer})
        
        # 4. Update sources with the FAQ ID
        sources = [f"{faq_question} (ID: {relevant_faq.get('id', 'Unknown ID')})"]
    else:
        # Handle the case where no relevant FAQ was found
        history.append({"role": "Matched FAQ", "content": "No relevant FAQ found."})
        sources = []
        relevant_faq = {}
    
    # 5. Generate the response using the LLM, providing the FAQ content as context
    messages = build_messages(user_message, relevant_faq, history)
    answer = call_llm(messages)
    
    history.append({"role": "assistant", "content": answer})

    # Limit history to the last 5 turns (15 messages) to prevent context overflow (each turn has 3 messages: user, matched FAQ, assistant)
    if len(history) > 20:
        history = history[-20:]

    # 5. Return the response, including the updated history
    return ChatResponse(
        answer=answer,
        sources=sources,
        memory_used=True,
        history=history
    )