-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create learning_activities table
CREATE TABLE learning_activities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    content JSONB, -- store specific fields based on type (concept, problem, etc.)
    topic TEXT,
    subtopics TEXT[],
    source_url TEXT,
    date_learned DATE NOT NULL DEFAULT CURRENT_DATE,
    embedding vector(384), -- sentence-transformers all-MiniLM-L6-v2 uses 384 dims
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS
ALTER TABLE learning_activities ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own learning activities"
    ON learning_activities FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own learning activities"
    ON learning_activities FOR INSERT
    WITH CHECK (auth.uid() = user_id);
    
CREATE POLICY "Users can update their own learning activities"
    ON learning_activities FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own learning activities"
    ON learning_activities FOR DELETE
    USING (auth.uid() = user_id);

-- Create goals table
CREATE TABLE goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    goal_type TEXT,
    target_date DATE,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Enable RLS
ALTER TABLE goals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own goals"
    ON goals FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own goals"
    ON goals FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own goals"
    ON goals FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own goals"
    ON goals FOR DELETE
    USING (auth.uid() = user_id);

-- Function to search learning activities using pgvector cosine distance
CREATE OR REPLACE FUNCTION match_learning_activities (
  query_embedding vector(384),
  match_threshold float,
  match_count int,
  p_user_id uuid
)
RETURNS TABLE (
  id uuid,
  title text,
  type text,
  topic text,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    id,
    title,
    type,
    topic,
    1 - (learning_activities.embedding <=> query_embedding) AS similarity
  FROM learning_activities
  WHERE 1 - (learning_activities.embedding <=> query_embedding) > match_threshold
    AND user_id = p_user_id
  ORDER BY similarity DESC
  LIMIT match_count;
$$;
