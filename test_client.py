import requests
import json

def send_chat_message(message: str, history: list = []):
    """
    Sends a message to the FastAPI chat endpoint and prints the response.
    """
    # The URL of your running FastAPI application
    url = "http://127.0.0.1:8000/chat"

    # The data payload, matching the ChatRequest Pydantic model
    payload = {"message": message, "history": history}

    print(f"Sending message: '{message}'")
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        response_data = response.json()
        print("Success! Server responded with:")
        print(json.dumps(response_data, indent=2))
        
        # Update local history with the full history returned by the server
        return response_data["history"]
    else:
        print(f"Error: Received status code {response.status_code}")
        print("Response body:", response.text)

if __name__ == "__main__":
    # Simulate a multi-turn conversation
    print("--- Turn 1 ---")
    conversation_history = send_chat_message("What is Vendor Services?")

    print("\n--- Turn 2 (Follow-up) ---")
    # This follow-up question is vague, but the LLM would use the history to understand it.
    # Our retrieval will likely match "Who uses the Vendor Services website?"
    conversation_history = send_chat_message("Who is it for?", history=conversation_history)

    print("\n--- Turn 3 (New Topic) ---")
    conversation_history = send_chat_message("Tell me about FHIR", history=conversation_history)