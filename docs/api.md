# API Design

## Authentication
Supabase handles authentication.
FastAPI validates the authenticated user. Never trust a `user_id` supplied by the frontend.

## Endpoints

### Resume
- `POST /api/resumes/upload`
- `GET /api/resumes`
- `GET /api/resumes/{id}`
- `DELETE /api/resumes/{id}`

### Resume Analysis
- `POST /api/resume-analysis`
- `GET /api/resume-analysis`
- `GET /api/resume-analysis/{id}`

### Learning
- `POST /api/learning/chat`
- `POST /api/learning`
- `GET /api/learning`
- `GET /api/learning/{id}`
- `PATCH /api/learning/{id}`
- `DELETE /api/learning/{id}`
- `GET /api/learning/recent`
- `POST /api/learning/search`

### Goals
- `POST /api/goals`
- `GET /api/goals`
- `PATCH /api/goals/{id}`
- `DELETE /api/goals/{id}`

### Interviews
- `POST /api/interviews`
- `GET /api/interviews`
- `GET /api/interviews/{id}`
- `POST /api/interviews/{id}/message`
- `POST /api/interviews/{id}/code`
- `POST /api/interviews/{id}/complete`
- `GET /api/interviews/{id}/report`
