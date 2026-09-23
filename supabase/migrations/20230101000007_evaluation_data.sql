ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS evaluation_data JSONB;
NOTIFY pgrst, 'reload schema';
