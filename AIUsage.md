# AI_USAGE.md

This document describes how AI tools were used during the development of the Epic Vendor Services FAQ Support Copilot.

AI usage was **intentional and focused on accelerating development**, while all architectural, algorithmic, and design decisions were made by me.

---

## High-Level Role of AI

AI was used as a **supporting tool**, similar to documentation, Stack Overflow, or a senior engineer to bounce ideas off of. It helped reduce friction in development, but it did **not** replace independent problem-solving or system design.

I retained full ownership over:
- system architecture
- data modeling
- retrieval and memory logic
- API behavior and control flow
- testing strategy and tradeoffs

---

## How AI Was Used

### 1. Problem Scoping & Approach Definition
At the beginning of the project, I used AI to:
- brainstorm possible approaches to the problem
- discuss tradeoffs between different designs (e.g., simple retrieval vs. embeddings, mock LLM vs. real LLM)

From these discussions, I selected and refined the final approach myself, prioritizing correctness, clarity, and alignment with the assignment requirements.

---

### 2. Stack & Tooling Research
AI was used to:
- evaluate possible backend frameworks and libraries
- compare options based on setup time and local portability
- sanity-check technology choices for a short take-home timeline

---

### 3. Code Authoring & Implementation Support

During implementation, AI was used for **targeted code generation and implementation assistance**, primarily to accelerate development of small, self-contained pieces of functionality.

Specifically, AI helped:
- generate short code snippets and scaffolding for common patterns
- reference library APIs and example usage
- speed up implementation of boilerplate or repetitive sections

All generated code was **reviewed, adapted, and integrated manually**. I was responsible for:
- deciding *what* to implement and *how* it should behave
- designing the retrieval flow, memory handling, routing logic, and response schema
- ensuring correctness, readability, and consistency across the codebase
 
---

### 4. Debugging Support
AI was used to help:
- reason about bugs and unexpected behavior
- interpret error messages
- sanity-check logic during debugging

---

### 5. Frontend Code Assistance
The frontend was an area where I intentionally deprioritized polish in favor of functionality. AI was used more heavily here to:
- generate basic UI scaffolding
- speed up layout and styling
- ensure the frontend could effectively demonstrate backend functionality

The frontend code was reviewed and adapted to fit the backend API and project goals.

---

### 6. Testing & Documentation Assistance
AI was used to:
- help structure test cases
- refine documentation wording and formatting
- ensure clarity and completeness in README and TESTING documentation

Test logic, assertions, and coverage decisions were made by me.

---

## What AI Was *Not* Used For

AI was **not** used to:
- blindly generate large portions of backend logic
- make architectural decisions without review
- copy/paste solutions from external sources
- fabricate system behavior or requirements

All core system behavior reflects my own understanding and implementation.

---