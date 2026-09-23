-- Extend interview sessions with structured state tracking
ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS current_stage TEXT DEFAULT 'QUESTION',
ADD COLUMN IF NOT EXISTS candidate_approach TEXT,
ADD COLUMN IF NOT EXISTS complexity TEXT,
ADD COLUMN IF NOT EXISTS hints_used INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS mistakes INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS state_metadata JSONB DEFAULT '{}'::jsonb;

ALTER TABLE interview_messages
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

-- Notify postgrest to reload schema cache
NOTIFY pgrst, 'reload schema';
