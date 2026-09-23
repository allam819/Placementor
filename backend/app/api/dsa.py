from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from supabase import Client
from .auth import verify_user, get_supabase_client
import tempfile
import json
import time
import os
from app.ai.gateway import ai_gateway

router = APIRouter()

class CodeSubmission(BaseModel):
    problem_id: str
    code: str
    language: str = "python"

class HintRequest(BaseModel):
    problem_id: str
    code: str
    error_message: str | None = None
    chat_history: List[dict] = []

class GenerateProblemRequest(BaseModel):
    difficulty: str

class TestCase(BaseModel):
    input_data: str
    expected_output: str
    is_hidden: bool

class GeneratedProblem(BaseModel):
    title: str
    description: str
    optimal_time_complexity: str
    optimal_space_complexity: str
    starter_code: Dict[str, str]
    test_cases: List[TestCase]

@router.get("/problems")
def get_problems(user = Depends(verify_user)):
    supabase: Client = get_supabase_client()
    res = supabase.table("dsa_problems").select("id, title, difficulty").order("created_at", desc=True).execute()
    problems = res.data
    
    # Fetch user's passed submissions to mark solved problems
    subs = supabase.table("dsa_submissions").select("problem_id").eq("user_id", user.user.id).eq("status", "Passed").execute()
    solved_ids = {s["problem_id"] for s in subs.data}
    
    for p in problems:
        p["solved"] = p["id"] in solved_ids
        
    return problems

@router.delete("/problems/{problem_id}")
def delete_problem(problem_id: str, user = Depends(verify_user)):
    supabase: Client = get_supabase_client()
    supabase.table("dsa_problems").delete().eq("id", problem_id).execute()
    return {"status": "deleted"}

@router.post("/generate")
def generate_problem(req: GenerateProblemRequest, user = Depends(verify_user)):
    sys_prompt = f"""
    You are an expert technical interviewer. Generate a completely random, unique {req.difficulty}-level Data Structures & Algorithms problem.
    Do not generate 'Two Sum' or overused problems.
    Write a beautiful, naturally flowing Markdown description of the problem. DO NOT use robotic headers like '**Problem:**' or '**Input:**'. Introduce the problem organically, describe the constraints smoothly, and provide clear code-block examples.
    
    You MUST output valid JSON conforming exactly to this schema:
    {{
      "title": "String",
      "description": "String (Markdown)",
      "optimal_time_complexity": "String (e.g. O(N))",
      "optimal_space_complexity": "String (e.g. O(1))",
      "starter_code": {{"python": "def function_name(args):\\n    pass"}},
      "test_cases": [
        {{
          "input_data": "{{\\"arg1\\": [1, 2], \\"arg2\\": 3}}",
          "expected_output": "\\"[1, 2, 3]\\"",
          "is_hidden": false
        }}
      ]
    }}
    
    Important for test_cases: input_data must be a JSON object mapping argument names to values. expected_output must be a valid JSON string (e.g. "[1, 2]" or "42"). Generate exactly 3 test cases.
    """
    
    messages = [{"role": "system", "content": sys_prompt}]
    
    try:
        data = ai_gateway.generate_structured(messages, GeneratedProblem)
        supabase: Client = get_supabase_client()
        
        prob_res = supabase.table("dsa_problems").insert({
            "title": data.title,
            "description": data.description,
            "difficulty": req.difficulty,
            "optimal_time_complexity": data.optimal_time_complexity,
            "optimal_space_complexity": data.optimal_space_complexity,
            "starter_code": json.dumps(data.starter_code)
        }).execute()
        
        prob_id = prob_res.data[0]["id"]
        
        for tc in data.test_cases:
            supabase.table("dsa_test_cases").insert({
                "problem_id": prob_id,
                "input_data": tc.input_data,
                "expected_output": tc.expected_output,
                "is_hidden": tc.is_hidden
            }).execute()
            
        return prob_res.data[0]
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate problem: {str(e)}")

@router.get("/problems/{problem_id}")
async def get_problem_details(problem_id: str):
    supabase: Client = get_supabase_client()
    res = supabase.table("dsa_problems").select("*").eq("id", problem_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Problem not found")
        
    tests_res = supabase.table("dsa_test_cases").select("input_data, expected_output, is_hidden").eq("problem_id", problem_id).execute()
    
    data = res.data[0]
    data["test_cases"] = tests_res.data
    return data

@router.post("/submit")
def submit_code(sub: CodeSubmission, user = Depends(verify_user)):
    supabase: Client = get_supabase_client()
    
    # Fetch test cases
    tests_res = supabase.table("dsa_test_cases").select("input_data, expected_output").eq("problem_id", sub.problem_id).execute()
    if not tests_res.data:
        raise HTTPException(status_code=404, detail="Test cases not found")
        
    start_time = time.time()
    
    # SECURITY PATCH: Live code execution using raw subprocess is disabled.
    # It must be isolated in a secure sandbox (e.g., Docker/gVisor/Judge0) before enabling.
    status = "Error"
    feedback = "[SECURITY: Disabled] Live code execution is temporarily disabled on the host machine to prevent arbitrary code execution vulnerabilities. A secure containerized execution environment is pending implementation."
    
    exec_time_ms = int((time.time() - start_time) * 1000)
    
    # Log submission
    supabase.table("dsa_submissions").insert({
        "user_id": user.user.id,
        "problem_id": sub.problem_id,
        "code": sub.code,
        "status": status,
        "execution_time_ms": exec_time_ms,
        "ai_feedback": feedback
    }).execute()
    
    return {
        "status": status,
        "feedback": feedback,
        "execution_time_ms": exec_time_ms
    }

@router.post("/hint")
def get_ai_hint(req: HintRequest, user = Depends(verify_user)):
    supabase: Client = get_supabase_client()
    prob_res = supabase.table("dsa_problems").select("title, description, optimal_time_complexity").eq("id", req.problem_id).execute()
    prob = prob_res.data[0]
    
    sys_prompt = f"""
    You are an expert, friendly FAANG interviewer mentoring a candidate solving '{prob["title"]}'.
    
    Their current code:
    {req.code}
    
    Their execution error (if any):
    {req.error_message}
    
    CRITICAL INSTRUCTIONS:
    1. NEVER repeat the problem statement or write robotic markdown headers like '**Problem:**'.
    2. DO NOT GIVE THE DIRECT ANSWER OR FULL CODE.
    3. Keep your response extremely brief, conversational, and direct (max 2-3 short paragraphs).
    4. If their code fails, gently point out a logical flaw or syntax error.
    5. End with a guiding question to nudge them toward the optimal O({prob["optimal_time_complexity"]}) solution.
    """
    
    messages = [{"role": "system", "content": sys_prompt}]
    
    # Add chat history
    for msg in req.chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    completion = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages
    )
    
    return {"hint": completion.choices[0].message.content}
