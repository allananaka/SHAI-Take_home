import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash-lite")

def build_messages(user_input, faq, history=None):
    # We move the FAQ context directly into the user message 
    # since Gemini uses the system_instruction parameter for the "rules"
    context_block = f"""
        FAQ TITLE: {faq.get('question', 'Unknown')}
        SECTION: {faq.get('section', 'General')}
        CONTENT: {faq.get('answer', 'No content provided')}
        SOURCE URL: {faq.get('url', 'N/A')}
    """

    messages = []

    # If you have history, format it as 'user' and 'model' pairs
    if history:
        # History needs to be a list of dicts: {"role": "user"/"model", "parts": ["text"]}
        # For now, let's assume we're adding it as a single context block
        messages.append({
            "role": "user",
            "parts": [f"Previous conversation context: {history}"]
        })
        messages.append({
            "role": "model",
            "parts": ["I have reviewed the history. How can I help with the FAQ?"]
        })

    # The final message combines the FAQ context and the user question
    messages.append({
        "role": "user",
        "parts": [f"CONTEXT:\n{context_block}\n\nUSER QUESTION: {user_input}"]
    })

    return messages

def call_llm(messages, temperature=0.2):
    # System prompt stays here - this is the correct place for it!
    system_prompt = (
        "You are a support assistant. "
        "Answer using the provided FAQ content or the conversation history. "
        "If the FAQ does not contain enough information, ask a clarifying question. "
        "Always cite the source URL when answering."
    )
    
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=system_prompt
    )
    
    try:
        response = model.generate_content(
            messages,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
            )
        )
        return response.text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        raise e

def rewrite_query(user_input, history):
    """
    Uses the LLM to rewrite a follow-up question into a standalone search query
    by incorporating context from the conversation history.
    """
    if not history:
        return user_input

    model = genai.GenerativeModel(MODEL_NAME)
    
    # Format the last few turns of history for context
    history_block = "\n".join([f"{msg.get('role', 'unknown')}: {msg.get('content', '')}" for msg in history[-3:]])
    
    prompt = f"""
    Rewrite the following follow-up question to be a standalone search query.
    Include necessary context from the conversation history (e.g., replace "it" with the specific topic).
    Do NOT answer the question, just rewrite it for a search engine.
    
    History:
    {history_block}
    
    Follow-up Question: {user_input}
    
    Standalone Query:
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error rewriting query: {e}")
        return user_input