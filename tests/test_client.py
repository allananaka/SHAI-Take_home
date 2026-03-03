import uuid

import requests
import json

# The URL of the running FastAPI application
BASE_URL = "http://127.0.0.1:8000"

def run_test(name, condition, error_message):
    """Helper function to run a test and print its status."""
    print(f"  - {name}: ", end="")
    try:
        assert condition, error_message
        print("✅ PASSED")
        return True
    except AssertionError as e:
        print(f"❌ FAILED\n    Reason: {e}")
        return False

def send_chat_message(message: str, history: list = None, conversation_id: str = None):
    """
    Sends a message to the FastAPI chat endpoint and returns the full response.
    """
    url = f"{BASE_URL}/chat"
    id = str(uuid.uuid4())
    print(f"    Request ID: {id}")
    payload = {"message": message, "history": history if history is not None else [], "requestID": id}
    if conversation_id:
        payload["conversation_id"] = conversation_id

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"\n🚨 CRITICAL: Could not connect to the server at {url}.")
        print(f"   Please ensure the FastAPI server is running: `uvicorn app.main:app --reload`")
        print(f"   Error details: {e}")
        return None

def print_response(response):
    """Helper to print the chat response cleanly, handling multi-line output."""
    if not response:
        print("    Response: <None>")
        return

    answer = response.get("answer", "")
    lines = answer.split("\n")
    print(f"    Response: {lines[0]}")
    for line in lines[1:]:
        print(f"              {line}")

def main():
    """
    Runs a series of tests against the chat API to verify its core functionality,
    including FAQ retrieval, context memory, and history management.
    """
    print("🚀 Starting API Test Suite...")
    conversation_history = []
    all_tests_passed = True

    # --- Test 1: Direct FAQ Hit (New Conversation) ---
    print("\n--- Test 1: Direct FAQ Hit (New Conversation) ---")
    print(f"  > Sending: 'What is Vendor Services?'")
    resp1 = send_chat_message("What is Vendor Services?")
    print_response(resp1)
    
    if resp1:
        all_tests_passed &= run_test("Response is not empty", resp1 is not None, "Server returned an empty response.")
        all_tests_passed &= run_test("Memory was not used", resp1.get("memory_used") is False, f"Expected memory_used=False, got {resp1.get('memory_used')}")
        all_tests_passed &= run_test("Source was found", len(resp1.get("sources", [])) > 0, "Expected at least one source, found none.")
        all_tests_passed &= run_test("URL was populated", resp1.get("url") != "", "Expected a URL, but it was empty.")
        conversation_history = resp1.get("history", [])
    else:
        all_tests_passed = False

    # --- Test 2: Follow-up Question (Uses Memory) ---
    print("\n--- Test 2: Follow-up Question (Uses Memory) ---")
    print(f"  > Sending: 'Who is it for?'")
    resp2 = send_chat_message("Who is it for?", history=conversation_history)
    print_response(resp2)

    if resp2:
        all_tests_passed &= run_test("Response is not empty", resp2 is not None, "Server returned an empty response.")
        all_tests_passed &= run_test("Memory was used", resp2.get("memory_used") is True, f"Expected memory_used=True, got {resp2.get('memory_used')}")
        all_tests_passed &= run_test("Answer is not a fallback", "I'm sorry" not in resp2.get("answer", ""), "Received a fallback answer for a valid follow-up.")
        conversation_history = resp2.get("history", [])
    else:
        all_tests_passed = False

    # --- Test 3: New Topic (Resets Context) ---
    print("\n--- Test 3: New Topic (Resets Context) ---")
    print(f"  > Sending: 'Tell me about FHIR'")
    resp3 = send_chat_message("Tell me about FHIR", history=conversation_history)
    print_response(resp3)

    if resp3:
        all_tests_passed &= run_test("Response is not empty", resp3 is not None, "Server returned an empty response.")
        all_tests_passed &= run_test("Memory was not used (new topic)", resp3.get("memory_used") is False, f"Expected memory_used=False, got {resp3.get('memory_used')}")
        conversation_history = resp3.get("history", [])
    else:
        all_tests_passed = False

    # --- Test 4: No FAQ Match but follow-up detected (Clarifying Question) ---
    print("\n--- Test 4: No FAQ Match but follow-up detected (Clarifying Question) ---")
    print(f"  > Sending: 'Tell me more about that.' (with previous history)")
    resp4 = send_chat_message("Tell me more about that.", history=conversation_history)
    print_response(resp4)

    if resp4:
        all_tests_passed &= run_test("Response is not empty", resp4 is not None, "Server returned an empty response.")
        all_tests_passed &= run_test("Memory was used", resp4.get("memory_used") is True, f"Expected memory_used=True, got {resp4.get('memory_used')}")
        all_tests_passed &= run_test(
            "URL is present in response", 
            resp4.get("url", "") != "", 
            f"Expected a non-empty URL in the response, got: '{resp4.get('url', '')}'"
        )
        all_tests_passed &= run_test(
            "At least one source is present in response",
            len(resp4.get("sources", [])) > 0,
            f"Expected at least one source in the response, got: {resp4.get('sources', [])}"
        )
    else:
        all_tests_passed = False

    # --- Test 5: No FAQ Match (Graceful Failure) ---
    print("\n--- Test 5: No FAQ Match (Graceful Failure) ---")
    print(f"  > Sending: 'asdfghjkl qwerty'")
    resp5 = send_chat_message("asdfghjkl qwerty", history=conversation_history)
    print_response(resp5)

    if resp5:
        all_tests_passed &= run_test("Response is not empty", resp5 is not None, "Server returned an empty response.")
        all_tests_passed &= run_test("No sources were found", len(resp5.get("sources", [])) == 0, "Expected zero sources for a non-matching query.")
        all_tests_passed &= run_test("URL is empty", resp5.get("url") == "", "Expected an empty URL for a non-matching query.")
        all_tests_passed &= run_test("Fallback answer was given", "I apologize" in resp5.get("answer", ""), "Did not receive the expected fallback answer.")
    else:
        all_tests_passed = False
    
    # --- Test 6: Empty Input Handling ---
    print("\n--- Test 6: Empty Input Handling ---")
    print(f"  > Sending: ' '")
    resp6 = send_chat_message(" ")
    print_response(resp6)

    if resp6:
        all_tests_passed &= run_test("Response is not empty", resp6 is not None, "Server returned an empty response.")
        all_tests_passed &= run_test("Graceful answer was given", "sent an empty message" in resp6.get("answer", ""), "Did not receive the expected graceful answer for empty input.")
        all_tests_passed &= run_test("No sources were found", len(resp6.get("sources", [])) == 0, "Expected zero sources for empty input.")
        all_tests_passed &= run_test("Memory was not used", resp6.get("memory_used") is False, f"Expected memory_used=False, got {resp6.get('memory_used')}")
    else:
        all_tests_passed = False

    # --- Test 6: Password Reset Handling ---
    print("\n--- Test 7: Not Reinventing steps ---")
    print(f"  > Sending: 'I'm having trouble logging into the Vendor Services website. What do I do?'")
    resp7 = send_chat_message("I'm having trouble logging into the Vendor Services website. What do I do?")
    print_response(resp7)

    if resp7:
        all_tests_passed &= run_test("Response is not empty", resp7 is not None, "Server returned an empty response.")
        all_tests_passed &= run_test("Source was found", len(resp7.get("sources", [])) > 0, "Expected at least one source, found none.")
        all_tests_passed &= run_test("Referenced FAQ instead of own solution", "contact a Vendor Services TS or use the \"Contact\" form" in resp7.get("answer", ""), "Did not receive the expected FAQ-based answer.")
    else:
        all_tests_passed = False

    # --- Test 8: Conversation ID — initial input with no found history (memory not used) ---
    print("\n--- Test 8: Conversation ID — initial input, no history (memory not used) ---")
    new_cid = str(uuid.uuid4())
    print(f"  > Sending first message with new conversation_id and history=[]")
    resp_initial = send_chat_message("What is Vendor Services?", history=[], conversation_id=new_cid)
    print_response(resp_initial)

    if resp_initial:
        all_tests_passed &= run_test("Response is not empty", resp_initial is not None, "Server returned an empty response.")
        all_tests_passed &= run_test("Memory was not used (no prior history)", resp_initial.get("memory_used") is False, f"Expected memory_used=False for first message, got {resp_initial.get('memory_used')}")
    else:
        all_tests_passed = False

    # --- Test 9: Conversation ID — simulate refresh (history persisted, memory used) ---
    print("\n--- Test 9: Conversation ID — simulate refresh (history persisted, memory used) ---")
    fixed_cid = str(uuid.uuid4())
    print(f"  > Sending first message: 'What is Vendor Services?' (conversation_id={fixed_cid[:8]}..., history=[])")
    resp_first = send_chat_message("What is Vendor Services?", history=[], conversation_id=fixed_cid)
    print_response(resp_first)
    print(f"  > Simulating refresh: sending follow-up with same conversation_id, empty history")
    resp_after_refresh = send_chat_message("Who is it for?", history=[], conversation_id=fixed_cid)
    print_response(resp_after_refresh)

    if resp_first and resp_after_refresh:
        all_tests_passed &= run_test("First response is not empty", resp_first is not None, "Server returned an empty response.")
        all_tests_passed &= run_test("After-refresh response is not empty", resp_after_refresh is not None, "Server returned an empty response.")
        all_tests_passed &= run_test("Memory was used after refresh (history restored)", resp_after_refresh.get("memory_used") is True, f"Expected memory_used=True when same conversation_id and empty history, got {resp_after_refresh.get('memory_used')}")
        hist_len = len(resp_after_refresh.get("history", []))
        all_tests_passed &= run_test("History was persisted and returned", hist_len > 1, f"Expected history length > 1, got {hist_len}")
    else:
        all_tests_passed = False

    print("\n--- Test Suite Finished ---")
    if all_tests_passed:
        print("✅ All tests passed successfully!")
    else:
        print("❌ Some tests failed. Please review the output above.")

if __name__ == "__main__":
    main()