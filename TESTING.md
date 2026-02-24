# TESTING.md

This document describes how I tested the Epic Vendor Services FAQ Support Copilot backend API.

## Overview

Testing focuses on the **core workflow requirements**:
- FAQ retrieval + source grounding (sources + URL)
- Short-term conversation memory (follow-ups use memory; new topics reset memory)
- Domain-correct support behavior (access/password questions route to official support paths)
- Reliability basics (empty input + retrieval misses handled gracefully)

The test suite is implemented as a Python script that makes HTTP requests to the running FastAPI server and asserts on the JSON response fields.

## How to Run

1. Start the FastAPI server (in one terminal):
```bash
uvicorn app.main:app --reload
```

2. Run the test script (in another terminal):
```bash
python3 "test_client.py"
```

## Testing Strategy Overview:

Tests are written as an integration-style API test suite using Python and requests.
Each test sends a real HTTP request to the backend and asserts on the JSON response.

The tests validate:
 - FAQ retrieval and source grounding
 - Short-term conversation memory
 - Context reset on topic change
 - Clarifying behavior when information is ambiguous
 - Graceful handling of empty input and retrieval misses
 - Domain-correct routing for access/login issues

This project supports a mock LLM mode for local development and portability.

When the mock LLM is enabled:
 - Responses are deterministic by design
 - Tests assert on specific response text and known output patterns
 - This allows reliable validation of control flow, routing, and memory behavior

With a real LLM enabled, responses would be less deterministic (due to paraphrasing and rewording). In that case, these tests would be adapted to assert on behavioral properties (e.g., presence of a clarifying question, correct routing, grounding metadata) rather than exact wording

## Test Cases:

### Test 1 — Direct FAQ Hit (New Conversation)
Input: 
"What is Vendor Services?"

Validates:
 - API returns a non-empty response
 - memory_used == False (new conversation)
 - At least one FAQ source is returned
 - A source URL is populated
 - Conversation history is initialized

### Test 2 — Follow-up Question (Uses Memory)
Input:
"Who is it for?"

Validates:
 - API returns a non-empty response
 - memory_used == True (follow-up detected)
 - Answer is not a generic fallback
 - Conversation history is updated

### Test 3 — New Topic (Resets Context)
Input:
"Tell me about FHIR" (with existing history)

Validates:
 - API returns a non-empty response
 - memory_used == False (not treated as follow-up)
 - Conversation history is reset or reduced, indicating a context change

### Test 4 — Follow-up With No Matching FAQ (Clarifying Question)
Input:
"Tell me more about that." (with previous history)

Validates:
 - API returns a non-empty response
 - memory_used == True
 - No FAQ sources are returned
 - Source URL is empty
 - Response indicates follow-up handling / clarification behavior

### Test 5 — No FAQ Match (Graceful Failure)
Input:
"asdfghjkl qwerty"

Validates:
 - API returns a non-empty response
 - No sources are returned
 - Source URL is empty
 - A fallback response is provided instead of an error

### Test 6 — Empty Input Handling
Input:
" " (whitespace-only message)

Validates:
 - API returns a non-empty response
 - A graceful empty-input message is returned
 - No sources are returned
 - memory_used == False

### Test 7 — Access / Login Support Routing
Input:
"I'm having trouble logging into the Vendor Services website. What do I do?"

Validates:
 - API returns a non-empty response
 - At least one FAQ source is referenced
 - Response routes the user to the official support path
 - The system does not invent password reset steps

## Scope Tradeoffs & Design Notes
 - Input schema validation (incorrect types, malformed requests) is handled by FastAPI + Pydantic and by frontend constraints.
 - Tests intentionally focus on application logic, which is the highest-risk portion of the system.
 - The mock LLM enables fast, deterministic testing without external API keys and ensures local portability.