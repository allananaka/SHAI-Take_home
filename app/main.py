from fastapi import FastAPI
from pydantic import BaseModel
import json
import os
from .retrieval import FAQRetriever

# Load the FAQ data from the JSON file
FAQ_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "SEED_DATA", "epic_vendor_faq.json")
with open(FAQ_FILE_PATH, 'r') as f:
    faq_data = json.load(f)

# Create a single, pre-computed retriever instance when the app starts.
retriever = FAQRetriever(faq_data)

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    memory_used: bool

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # 1. receive user input
    user_message = req.message

    # 2. retrieve relevant FAQ using the pre-computed retriever instance
    relevant_faq = retriever.find_best_match(user_message)
    
    if relevant_faq:
        faq_question = relevant_faq.get("question", "No question found.")
        faq_detailed_answer = relevant_faq.get("answer", "No detailed answer found.")

        # 3. Format the answer using information from the FAQ
        answer = f"{faq_question}\n\n{faq_detailed_answer}"
        
        # 4. Update sources with the FAQ ID
        sources = [f"{faq_question} (ID: {relevant_faq.get('id', 'Unknown ID')})"]

        # 5. Return the formatted response
        return ChatResponse(
            answer=answer,
            sources=sources,
            memory_used=True
        )
    else:
        # Handle the case where no relevant FAQ was found
        return ChatResponse(
            answer="I'm sorry, I couldn't find a relevant answer in my knowledge base. Please try rephrasing your question.",
            sources=[],
            memory_used=False
        )