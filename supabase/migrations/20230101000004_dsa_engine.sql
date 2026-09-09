-- Phase 6: DSA Engine Schema

CREATE TABLE dsa_problems (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    difficulty TEXT NOT NULL CHECK (difficulty IN ('Easy', 'Medium', 'Hard')),
    starter_code TEXT NOT NULL,
    optimal_time_complexity TEXT,
    optimal_space_complexity TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TABLE dsa_test_cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    problem_id UUID REFERENCES dsa_problems(id) ON DELETE CASCADE,
    input_data TEXT NOT NULL, -- Stored as JSON string
    expected_output TEXT NOT NULL, -- Stored as JSON string
    is_hidden BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TABLE dsa_submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    problem_id UUID REFERENCES dsa_problems(id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('Passed', 'Failed', 'Error', 'Timeout')),
    execution_time_ms INTEGER,
    ai_feedback TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS
ALTER TABLE dsa_problems ENABLE ROW LEVEL SECURITY;
ALTER TABLE dsa_test_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE dsa_submissions ENABLE ROW LEVEL SECURITY;

-- Policies
-- Anyone can view problems and test cases
CREATE POLICY "Anyone can view problems" ON dsa_problems FOR SELECT USING (true);
CREATE POLICY "Anyone can view test cases" ON dsa_test_cases FOR SELECT USING (true);

-- Users can only view and insert their own submissions
CREATE POLICY "Users can view own submissions" ON dsa_submissions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own submissions" ON dsa_submissions FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Insert dummy data
INSERT INTO dsa_problems (id, title, description, difficulty, starter_code, optimal_time_complexity, optimal_space_complexity)
VALUES 
(
    '11111111-1111-1111-1111-111111111111',
    'Two Sum', 
    'Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target. You may assume that each input would have exactly one solution, and you may not use the same element twice. You can return the answer in any order.',
    'Easy',
    'def twoSum(nums, target):
    # Write your code here
    pass',
    'O(n)',
    'O(n)'
);

INSERT INTO dsa_test_cases (problem_id, input_data, expected_output, is_hidden)
VALUES 
('11111111-1111-1111-1111-111111111111', '{"nums": [2, 7, 11, 15], "target": 9}', '[0, 1]', false),
('11111111-1111-1111-1111-111111111111', '{"nums": [3, 2, 4], "target": 6}', '[1, 2]', false),
('11111111-1111-1111-1111-111111111111', '{"nums": [3, 3], "target": 6}', '[0, 1]', true);
