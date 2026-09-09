# Database Schema

## Core Tables (MVP)

- `profiles`: id, user_id, name, target_role, target_company, created_at, updated_at
- `resumes`: id, user_id, file_path, file_name, parsed_content, created_at, updated_at
- `job_descriptions`: id, user_id, title, company, raw_text, structured_requirements, created_at
- `resume_analyses`: id, user_id, resume_id, job_description_id, overall_score, category_scores, requirements_mapping, gaps, recommendations, created_at
- `learning_activities`: id, user_id, type, title, description, content, topic, subtopics, source_url, date_learned, embedding (pgvector), created_at, updated_at
- `goals`: id, user_id, title, description, goal_type, target_date, status, created_at, completed_at
- `interview_sessions`: id, user_id, type, difficulty, resume_id, target_role, status, score, evaluation, started_at, completed_at
- `interview_messages`: id, session_id, role, content, metadata, created_at
- `interview_questions`: id, session_id, question, question_type, topic, difficulty, created_at
- `interview_evaluations`: id, session_id, category, score, feedback, created_at

## Infrastructure
- Supabase PostgreSQL
- pgvector for semantic search (learning search)
- Row Level Security (RLS) is required. Every user-owned record must be scoped to the authenticated user.
