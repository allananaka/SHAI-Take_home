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
    history: list[dict] = []

class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    memory_used: bool
    history: list[dict]

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # 1. receive user input
    user_message = req.message

    # 2. retrieve relevant FAQ using the pre-computed retriever instance
    # We use ONLY the most recent user_message for retrieval to get the best factual match.
    relevant_faq = retriever.find_best_match(user_message)
    
    # Prepare for conversation history
    history = req.history
    history.append({"role": "user", "content": user_message})

    if relevant_faq:
        faq_question = relevant_faq.get("question", "No question found.")
        faq_detailed_answer = relevant_faq.get("answer", "No detailed answer found.")

        # 3. Format the answer using information from the FAQ
        answer = f"{faq_question}\n\n{faq_detailed_answer}"
        
        # 4. Update sources with the FAQ ID
        sources = [f"{faq_question} (ID: {relevant_faq.get('id', 'Unknown ID')})"]

        # THIS IS WHERE YOUR FUTURE LLM CALL WOULD GO
        # You would pass the `history` and the `faq_detailed_answer` to the LLM.
        # For now, we use the formatted answer directly.
        
        history.append({"role": "assistant", "content": answer})

        # 5. Return the response, including the updated history
        return ChatResponse(
            answer=answer,
            sources=sources,
            memory_used=True,
            history=history
        )
    else:
        # Handle the case where no relevant FAQ was found
        no_answer_response = "I'm sorry, I couldn't find a relevant answer in my knowledge base. Please try rephrasing your question."
        history.append({"role": "assistant", "content": no_answer_response})

        return ChatResponse(
            answer=no_answer_response,
            sources=[],
            memory_used=False,
            history=history
        )