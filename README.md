# Epic Vendor Services FAQ Support Copilot

## 1. Project Overview
This project implements a source-grounded support chatbot for Epic Vendor Services FAQs, using short-term conversation memory and a local mock LLM for portability.

---

## 2. Features
- Source-grounded FAQ responses
- Short-term conversation memory
- Clarifying questions for ambiguous input
- Graceful handling of empty input and retrieval misses

---

## 3. Tech Stack

### Backend: FastAPI, Uvicorn, Pydantic
- Chosen for **fast local setup**, supporting the project requirement of quick local portability.
- FastAPI and Uvicorn made it easy to stand up a clean, lightweight REST API entirely in Python.
- Pydantic enforces **explicit request/response contracts** between the frontend and backend, reducing ambiguity and improving reliability during development and testing.

---

### Retrieval / Search: TF-IDF Vectorizer + Cosine Similarity (scikit-learn)
- TF-IDF provides a more meaningful similarity measure than simple word-count or keyword matching by accounting for term importance across the dataset.
- Well-suited for a **small, curated FAQ dataset**, where interpretability and determinism are important.
- Avoids the additional complexity and infrastructure overhead of embeddings while still producing reliable matches.
- Given more time, embeddings would be a natural next step for improved semantic retrieval.

---

### LLM: Google Gemini (with Mock LLM)
- Gemini was selected as a **high-quality, modern LLM** that could be easily integrated when real LLM responses are desired.
- A mock LLM is provided to support **local development, deterministic testing, and portability** without requiring API keys.
- This approach separates system logic (retrieval, routing, memory) from text generation concerns.

---

### Frontend: HTML, CSS, JavaScript
- A lightweight frontend stack was chosen to **minimize setup complexity** and avoid build tooling.
- Allowed focus to remain on backend logic and system behavior while still providing a functional chat UI.
- Sufficient to demonstrate core functionality, API integration, and end-to-end behavior.

---

### Testing: Python + requests
- Using Python and `requests` allows tests to interact with the backend **exactly as a real client would**.
- Enables end-to-end validation of retrieval, memory usage, grounding metadata, and error handling.
- Simple, portable, and easy to run as part of local development without additional frameworks.

---

## 4. Project Structure

app/
  main.py
  mock.py
  models.py
  response.py
  retrieval.py
  utils.py
frontend/
  index.html
  style.css
  script.js
SEED_DATA/
  epic_vendor_faq.json
tests/
  test_client.py
.env
AIUSAGE.md
README.md
TESTING.md

## 5. Local Setup Instructions

### Prerequisites
- Python 3.11 or higher

### Installation

1. **Create and activate a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   # Mac/Linux
   source venv/bin/activate
   # Windows
   venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Set up Environment Variables**:
   - Create a file named `.env` in the root directory.
   ```bash
    cp .env.example .env
    ```

## 6. Running the Application

1. **Start the Backend Server**:
   ```bash
   python3 -m uvicorn app.main:app --reload
   ```
   Press Ctrl + C to stop the server

2. **Launch the Frontend**:
   - Open your web browser and navigate to `http://127.0.0.1:8000`.

## 7. Running Tests
To verify the system logic and API behavior, ensure the backend is running, then execute:
```bash
python3 "tests/test_client.py"
```
Testing outlined in TESTING.md

## 8. Mock LLM vs. Real LLM

By default, this project uses a **mock LLM** during local development and testing.

The mock LLM produces **deterministic, controlled outputs**, which makes it possible to reliably test core system behavior—such as FAQ retrieval, source grounding, memory usage, and clarifying questions without depending on an external LLM API. This improves reproducibility, simplifies debugging, and avoids variability in test results caused by nondeterministic language generation.

In a real-world deployment, a **real LLM (e.g., Google Gemini)** can be enabled to provide more natural, conversational, and user-authentic responses. Importantly, switching to a real LLM does **not change the underlying system logic**: retrieval, memory handling, routing decisions, and grounding behavior remain the same. The LLM is used purely to enhance response phrasing and conversational quality.

Tests are written against the mock LLM’s deterministic outputs to ensure consistent validation of system functionality, independent of LLM variability. However, system was also designed with real LLM use in mind.

## 9. Tradeoffs and Future Work

This project prioritizes correctness, clarity, and local portability within a limited take-home timeline. The following tradeoffs were made intentionally, along with potential areas for future improvement.

### Retrieval Approach
- **Tradeoff:** The system uses TF-IDF vectors with cosine similarity instead of embedding-based semantic retrieval.
- **Rationale:** TF-IDF is simple, deterministic, easy to debug, and well-suited for a small, curated FAQ dataset.
- **Future Work:** Replacing or augmenting TF-IDF with embeddings could improve semantic understanding, especially for paraphrased queries, follow-up question interpretation, and more nuanced FAQ matching.

---

### Frontend Scope
- **Tradeoff:** The frontend UI is intentionally minimal.
- **Rationale:** Effort was focused on backend logic, retrieval correctness, memory behavior, and domain-specific routing rather than UI polish.
- **Future Work:** The UI could be expanded with improved styling, richer interaction patterns, and clearer visual indicators for memory usage and source grounding.

---

### FAQ Matching & Follow-up Detection
- **Tradeoff:** Thresholds for FAQ matching and follow-up detection are based on simple similarity heuristics.
- **Rationale:** This keeps behavior transparent and predictable while meeting core requirements.
- **Future Work:**
  - Refine similarity thresholds using empirical tuning or validation data.
  - If multiple FAQs score similarly, introduce a clarifying question to disambiguate between them rather than selecting one automatically.

---

### Conversation History Management
- **Tradeoff:** Conversation history length is limited to balance correctness and performance.
- **Rationale:** Longer histories can improve follow-up understanding but may introduce irrelevant context or reduce efficiency.
- **Future Work:** Evaluate more refined strategies for history management, such as relevance-based trimming or turn summarization.

---
