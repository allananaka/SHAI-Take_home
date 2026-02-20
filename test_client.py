import requests
import json

def send_chat_message(message: str):
    """
    Sends a message to the FastAPI chat endpoint and prints the response.
    """
    # The URL of your running FastAPI application
    url = "http://127.0.0.1:8000/chat"

    # The data payload, matching the ChatRequest Pydantic model
    payload = {"message": message}

    print(f"Sending message: '{message}'")
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        print("Success! Server responded with:")
        print(response.json())
    else:
        print(f"Error: Received status code {response.status_code}")
        print("Response body:", response.text)

if __name__ == "__main__":
    send_chat_message("What is FHIR?")
    send_chat_message("Tell me about Vendor Services.")
    send_chat_message("Who uses the website?")
    send_chat_message("What is open epic?")
    send_chat_message("I need help with my account.")