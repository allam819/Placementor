# Placement Preparation Platform

An AI-powered, full-stack placement preparation platform built with React, FastAPI, Supabase, and Groq's 120B model.

## ✨ Features

- **DSA Sandbox:** Write and execute code (Python, JS, C++) directly in the browser against test cases.
- **AI Technical Interviews:** Complete a DSA problem with a live AI FAANG interviewer. Features a fully resizable dual-pane workspace (Code Editor & Chat/Description). The AI hints at logic flaws without giving away the answer.
- **Behavioral Interviews:** Upload your resume and practice behavioral questions in a timed environment.
- **Resume Analyzer:** Get instant feedback and ATS scoring on your PDF resume.
- **Learning Tracker:** Keep track of your placement studies. The AI automatically extracts key points from brief topic inputs.

## 🚀 Tech Stack

- **Frontend:** React, Vite, Tailwind CSS (v4), Monaco Editor, React Resizable Panels, React Markdown.
- **Backend:** FastAPI, Python, Uvicorn, subprocess execution for code running.
- **Database:** Supabase (PostgreSQL), with PostgREST constraints and SQL functions.
- **AI / LLM:** Groq API (Llama 3 / gpt-oss-120b).
- **Storage:** Supabase Storage (for Resume PDFs).

## 🛠️ Setup Instructions

### Prerequisites
- Node.js (v18+)
- Python (3.10+)
- Supabase CLI

### 1. Database & Services (Supabase)
```bash
# Start local Supabase instance
supabase start

# Apply migrations
supabase db push
```

### 2. Backend (FastAPI)
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt

# Start backend server
uvicorn main:app --port 8000 --reload
```

### 3. Frontend (React)
```bash
cd frontend
npm install
npm run dev
```

### 4. Environment Variables
Copy `.env.example` to `.env` in the root folder and add your API keys:
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `GROQ_API_KEY`

## 📝 License
MIT
