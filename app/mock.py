from typing import Dict, Optional

# Simulate LLM answer for testing without calling the actual Gemini API
def call_mock_llm(relevant_faq: Optional[Dict], is_follow_up: bool = False) -> str:
    """
    Simulates an LLM response using the retrieved FAQ data.
    This is useful for local testing without a Gemini API key.
    """
    
    if not relevant_faq:
        if is_follow_up:
            return f"I apologize, but I couldn't find any relevant information in the FAQ database for your follow-up question based on our previous conversation."
        else:
            return f"I apologize, but I couldn't find any relevant information in the FAQ database for your query."

    question = relevant_faq.get("question", "your question")
    answer = relevant_faq.get("answer", "Please refer to the source link for more details.")

    # Simulate a conversational wrapper around the FAQ content
    return (
        f"I found some information regarding \"{question}\".\n"
        f"{answer}\n"
        "Is there anything else you'd like to know about this topic?"
    )
    
    
