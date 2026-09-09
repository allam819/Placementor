-- Create resumes table
CREATE TABLE resumes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    parsed_content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create job_descriptions table
CREATE TABLE job_descriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT,
    company TEXT,
    raw_text TEXT NOT NULL,
    structured_requirements JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create resume_analyses table
CREATE TABLE resume_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    resume_id UUID REFERENCES resumes(id) ON DELETE CASCADE,
    job_description_id UUID REFERENCES job_descriptions(id) ON DELETE CASCADE,
    overall_score INTEGER,
    gaps JSONB,
    recommendations JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS
ALTER TABLE resumes ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_descriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE resume_analyses ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can manage their own resumes"
    ON resumes FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage their own job descriptions"
    ON job_descriptions FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage their own resume analyses"
    ON resume_analyses FOR ALL USING (auth.uid() = user_id);

-- Create Storage Bucket for Resumes (if not exists)
INSERT INTO storage.buckets (id, name, public)
VALUES ('resumes', 'resumes', false)
ON CONFLICT (id) DO NOTHING;

-- Storage RLS Policies for resumes bucket
CREATE POLICY "Users can upload their own resumes"
    ON storage.objects FOR INSERT
    WITH CHECK ( bucket_id = 'resumes' AND auth.uid()::text = (storage.foldername(name))[1] );

CREATE POLICY "Users can view their own resumes"
    ON storage.objects FOR SELECT
    USING ( bucket_id = 'resumes' AND auth.uid()::text = (storage.foldername(name))[1] );
