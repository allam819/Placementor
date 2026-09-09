-- Phase 7: DSA Interviews Integration

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS interview_mode TEXT DEFAULT 'general' CHECK (interview_mode IN ('general', 'dsa')),
ADD COLUMN IF NOT EXISTS dsa_problem_id UUID REFERENCES dsa_problems(id) ON DELETE SET NULL;

-- Notify postgrest to reload schema cache
NOTIFY pgrst, 'reload schema';
