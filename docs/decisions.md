# Decisions

## Explicit Requirements Followed
- Tech Stack: React, Vite, TS, Tailwind, shadcn/ui, FastAPI, Supabase. (No Next.js)
- Database: Supabase PostgreSQL with pgvector. No MongoDB, Pinecone, Firebase.
- Architecture: Deterministic logic where possible. LLM is not the source of truth for identity/permissions.
- Monorepo structure with frontend, backend, and supabase directories.

## Ambiguities and Implementation Decisions
- The PRD lists "PyMuPDF/pdfplumber" for PDF extraction. We will defer selecting between the two until the resume processing feature is implemented.
- Frontend React structure defaults to standard client-side SPA with React Router as requested.
- Auth flow uses Supabase standard email/password or OAuth (deferred details).

## Post-Audit Decisions
- **AI Gateway Integration**: Groq continues to be the active AI provider, but all direct SDK instantiations have been abstracted behind an `AIProvider` gateway (`backend/app/ai/gateway.py`). This strictly isolates the provider.
- **Deterministic Resume Scoring**: The AI is strictly barred from computing overall percentage match scores for resumes. Instead, the AI maps text to requirements, and a deterministic mathematical Python function calculates the final score based on PRD-defined weights.
- **Learning Hallucination Policy**: Strict prompts have been added to prevent the AI from generating unsolicited technical notes. The AI treats the user's input as the absolute limit of the knowledge logged.
- **Code Execution Security**: Raw subprocess execution of candidate code inside the FastAPI process is deemed too insecure for production. It has been temporarily disabled. A secure isolation boundary (e.g. Docker container) is required before re-enabling it.
- **Frontend API Architecture**: Hardcoded backend URLs have been stripped. The application now correctly uses a centralized fetch client pointing to `VITE_API_BASE_URL` to ensure environment portability.
- **Tesseract OCR OCR**: Hardcoded OS-specific paths have been removed. OCR uses standard environment resolutions or skips gracefully if unavailable.
- **Stateful AI Interviewer**: The interviewer was redesigned from a stateless chat loop into a stateful LangGraph orchestrator. The LLM acts as an observer/interpreter and response generator, but a deterministic Python state machine controls interview stage progression. This ensures the interview reliably advances through structured stages (APPROACH → COMPLEXITY → CODING) rather than behaving unpredictably.

### Removing Host Subprocess Execution
* **Context**: The DSA code execution previously used host-level \subprocess\ which allowed untrusted candidate code to execute directly on the FastAPI server, exposing environment secrets, filesystem, and network.
* **Decision**: We fully disabled host execution and implemented an isolated Docker-based execution service.
* **Architecture**: The \CodeExecutionService\ dynamically maps requests to short-lived Python containers using \subprocess.run(['docker', 'run', ...])\. The container is strictly constrained (no network, 256MB memory, 1 CPU limit, read-only base). Execution results are extracted securely via temporary host mounts that are wiped immediately.
* **Interviewer Integration**: The frontend is forbidden from dictating execution success. Execution runs strictly in \POST /api/interviews/execute\, which produces an immutable \ExecutionResult\. This trusted result is piped sequentially into the \LangGraph\ state machine to inform transitions without LLM hallucinations.
* **Fallback**: If Docker is unavailable locally, the system returns \SANDBOX_UNAVAILABLE\. We explicitly refused a \subprocess\ fallback to maintain zero tolerance for dangerous host evaluation.


### Post-Interview Evaluation Engine
* **Context**: We need to evaluate the candidate across problem-solving, code execution, communication, etc. Relying entirely on an LLM to generate scores leads to hallucinations, especially regarding whether tests passed or failed.
* **Decision**: We implemented a hybrid deterministic + qualitative evaluation engine.
* **Architecture**: 
  - **Objective metrics** (hints_used, mistakes, execution status, tests_passed) are securely pulled from the backend state (the single source of truth).
  - **Deterministic scoring**: Technical correctness and coding scores are calculated mathematically via test-case ratios and execution errors.
  - **Qualitative analysis**: The LLM (via structured output) strictly grades communication, problem-solving reasoning, strengths, weaknesses, and key mistakes.
  - **Final Outcome**: Determined absolutely by the deterministic math logic (e.g., overall score > 70 AND passed execution = PASSED) rather than LLM opinion.
* **Persistence**: Results are permanently attached to the \interview_sessions\ row via a JSONB \evaluation_data\ column. Repeated views do not trigger LLM re-evaluation.

