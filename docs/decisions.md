# Decisions

## Explicit Requirements Followed
- Tech Stack: React, Vite, TS, Tailwind, shadcn/ui, FastAPI, Supabase. (No Next.js)
- Database: Supabase PostgreSQL with pgvector. No MongoDB, Pinecone, Firebase.
- Architecture: Deterministic logic where possible. LLM is not the source of truth for identity/permissions.
- Monorepo structure with frontend, backend, and supabase directories.

## Ambiguities and Implementation Decisions
- The PRD lists "PyMuPDF/pdfplumber" for PDF extraction. We will defer selecting between the two until the resume processing feature is implemented.
- The PRD mentions `Code execution` in later phases. For the MVP backend foundation, we are not adding language runners or containerization yet.
- Frontend React structure defaults to standard client-side SPA with React Router as requested.
- Switched LLM provider from OpenAI to Groq per user request to utilize a free-tier API.
- Auth flow uses Supabase standard email/password or OAuth (deferred details).
