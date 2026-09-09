-- Create interview_sessions table
CREATE TABLE interview_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    resume_id UUID REFERENCES resumes(id) ON DELETE SET NULL,
    target_role TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active', -- active, completed
    overall_score INTEGER,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Create interview_messages table
CREATE TABLE interview_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create interview_evaluations table
CREATE TABLE interview_evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
    category TEXT NOT NULL, -- e.g., 'Technical Depth', 'Communication'
    score INTEGER NOT NULL,
    feedback TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS
ALTER TABLE interview_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_evaluations ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can manage their own interview sessions"
    ON interview_sessions FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage messages for their sessions"
    ON interview_messages FOR ALL USING (
        session_id IN (SELECT id FROM interview_sessions WHERE user_id = auth.uid())
    );

CREATE POLICY "Users can manage evaluations for their sessions"
    ON interview_evaluations FOR ALL USING (
        session_id IN (SELECT id FROM interview_sessions WHERE user_id = auth.uid())
    );
