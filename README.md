# Placementor - AI Placement Preparation Platform

An AI-powered, full-stack placement preparation platform built with React, FastAPI, Supabase, and Groq's high-speed LLMs. Designed to simulate FAANG-level technical interviews with strict, stateful AI agents and deterministic problem curation.

## 🚀 Key Features

### 🤖 Stateful Agentic AI Interviewer
*   **LangGraph-Powered State Machine:** Operates on an "Observe -> Decide -> Generate" loop, allowing the AI interviewer to intelligently transition between interview stages (Questioning, Code Execution, Debugging, Evaluation).
*   **Comprehensive Evaluation:** Automatically scores candidates across 7 distinct dimensions (Correctness, Time/Space Complexity, Communication, Debugging) with 100% deterministic stage transitions.
*   **Zero Hallucination Focus:** Powered by Groq for sub-800ms natural language generation, keeping the mock interview hyper-responsive and strictly aligned with the target problem.

### 🧠 Adaptive DSA Selection Engine
*   **Deterministic Recommendation:** Eliminates random problem selection. Uses a sophisticated Python/PostgreSQL scoring algorithm to process unstructured candidate history.
*   **Multi-Dimensional Profiling:** Analyzes over 5 data dimensions (recurring interview weaknesses, resume skill gaps, learning activity, recency penalties, and current difficulty level) to assign the most mathematically optimal algorithm problem for continuous progression.

### 🛡️ Secure Remote Code Execution (RCE) Sandbox
*   **Dockerized Compilation:** Safely executes and evaluates untrusted Python/C++/JS submissions against dynamic hidden test cases in real-time.
*   **Strict Isolation:** Enforces hard CPU and memory resource limits to prevent malicious payloads or memory leaks.

### 🎨 Modern Workspace & UI
*   **Split-Pane IDE:** Built with React, Tailwind CSS v4, and Monaco Editor. Features fully resizable, drag-and-drop dual panes for seamless coding and chatting.
*   **UX Polish:** Clean, responsive design featuring intuitive dashboard analytics, persistent learning trackers, and rich markdown parsing.

## 🛠️ Tech Stack

- **Frontend:** React, TypeScript, Vite, Tailwind CSS (v4), Monaco Editor, React Resizable Panels.
- **Backend:** FastAPI, Python, LangGraph, Docker.
- **Database:** Supabase (PostgreSQL), Supabase Auth, Row Level Security (RLS).
- **AI / LLM:** Groq API (Llama 3 70B / 120B).

## 💻 Setup Instructions

### Prerequisites
- Node.js (v18+)
- Python (3.10+)
- Docker Desktop (Required for the RCE Sandbox)
- Supabase CLI

### 1. Database Setup (Supabase)
```bash
# Start local Supabase instance
supabase start

# Apply migrations
supabase db push
```

### 2. Backend Environment (FastAPI)
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt

# Start backend server
uvicorn main:app --port 8000 --reload
```

### 3. Frontend Environment (React)
```bash
cd frontend
npm install
npm run dev
```

### 4. Environment Variables
Create `.env` files in both `frontend` and `backend` directories matching the `.env.example` configurations, supplying:
- `VITE_SUPABASE_URL` / `SUPABASE_URL`
- `VITE_SUPABASE_PUBLISHABLE_KEY`
- `SUPABASE_SECRET_KEY`
- `GROQ_API_KEY`

## 📝 License
MIT License
