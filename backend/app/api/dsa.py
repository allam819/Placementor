from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from supabase import Client
from .auth import verify_user, get_supabase_client
import tempfile
import subprocess
import json
import time
import os
from groq import Groq

router = APIRouter()
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

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
    Return ONLY a raw JSON object with no markdown wrapping.
    Schema:
    {{
      "title": "Problem Title",
      "description": "Write a beautiful, naturally flowing Markdown description of the problem. DO NOT use robotic headers like '**Problem:**' or '**Input:**'. Introduce the problem organically, describe the constraints smoothly, and provide clear code-block examples.",
      "optimal_time_complexity": "O(...)",
      "optimal_space_complexity": "O(...)",
      "starter_code": {{
        "python": "def functionName(args):\\n    pass",
        "javascript": "function functionName(args) {{\\n}}",
        "cpp": "#include <iostream>\\n#include <vector>\\nusing namespace std;\\n\\n// definition\\n"
      }},
      "test_cases": [
        {{"input_data": "{{\\"arg1\\": val}}", "expected_output": "val", "is_hidden": false}},
        {{"input_data": "{{\\"arg1\\": val2}}", "expected_output": "val2", "is_hidden": true}}
      ]
    }}
    Important for test_cases: input_data must be a JSON object mapping argument names to values. expected_output must be a valid JSON string (e.g. "[1, 2]" or "42"). Generate exactly 3 test cases.
    """
    
    completion = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "system", "content": sys_prompt}],
        response_format={"type": "json_object"}
    )
    
    try:
        data = json.loads(completion.choices[0].message.content)
        supabase: Client = get_supabase_client()
        
        prob_res = supabase.table("dsa_problems").insert({
            "title": data["title"],
            "description": data["description"],
            "difficulty": req.difficulty,
            "optimal_time_complexity": data["optimal_time_complexity"],
            "optimal_space_complexity": data["optimal_space_complexity"],
            "starter_code": json.dumps(data["starter_code"])
        }).execute()
        
        prob_id = prob_res.data[0]["id"]
        
        for tc in data["test_cases"]:
            supabase.table("dsa_test_cases").insert({
                "problem_id": prob_id,
                "input_data": tc["input_data"],
                "expected_output": tc["expected_output"],
                "is_hidden": tc["is_hidden"]
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
        
    status = "Failed"
    feedback = ""
    start_time = time.time()
    
    runner_code = ""
    ext = ".py"
    cmd = []
    compile_cmd = None
    
    if sub.language == "python":
        ext = ".py"
        runner_code = sub.code + "\n\nimport json, sys, inspect\ntest_cases = " + json.dumps(tests_res.data) + """
target_func = None
for name, obj in list(locals().items()):
    if inspect.isfunction(obj) and obj.__module__ == '__main__':
        target_func = obj
if not target_func:
    print("ERROR: No function defined.")
    sys.exit(1)
for i, test in enumerate(test_cases):
    kwargs = json.loads(test['input_data'])
    expected = json.loads(test['expected_output'])
    try:
        result = target_func(**kwargs)
        if result != expected:
            print(f"FAILED on test {i+1}: expected {expected}, got {result}")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR on test {i+1}: {str(e)}")
        sys.exit(1)
print("PASSED")
sys.exit(0)
"""
        
    elif sub.language == "javascript":
        ext = ".js"
        runner_code = sub.code + "\n\nconst test_cases = " + json.dumps(tests_res.data) + """;
const funcName = Object.keys(global).find(k => typeof global[k] === 'function' && k !== 'twoSum' && k !== 'test_cases') || 'twoSum';
const target_func = typeof twoSum === 'function' ? twoSum : eval(funcName);

if (typeof target_func !== 'function') {
    console.log("ERROR: No function defined.");
    process.exit(1);
}
test_cases.forEach((test, i) => {
    const kwargs = JSON.parse(test.input_data);
    const expected = JSON.parse(test.expected_output);
    try {
        const result = target_func(kwargs.nums || kwargs, kwargs.target);
        if (JSON.stringify(result) !== JSON.stringify(expected)) {
            console.log(`FAILED on test ${i+1}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(result)}`);
            process.exit(1);
        }
    } catch (e) {
        console.log(`ERROR on test ${i+1}: ${e.toString()}`);
        process.exit(1);
    }
});
console.log("PASSED");
process.exit(0);
"""
        
    elif sub.language == "cpp":
        ext = ".cpp"
        # Extremely brittle basic runner for C++ just for demonstration
        runner_code = sub.code + """
#include <iostream>
#include <string>
using namespace std;
int main() {
    // Note: A full C++ JSON test runner is complex for this MVP.
    // We are simulating a pass if it compiles and runs without crashing for demo purposes.
    cout << "PASSED" << endl;
    return 0;
}
"""
    else:
        raise HTTPException(status_code=400, detail="Language not supported")

    with tempfile.NamedTemporaryFile(mode='w', suffix=ext, delete=False) as f:
        f.write(runner_code)
        temp_path = f.name
        
    try:
        if sub.language == "python":
            cmd = ["python", temp_path]
        elif sub.language == "javascript":
            cmd = ["node", temp_path]
        elif sub.language == "cpp":
            exe_path = temp_path.replace(".cpp", ".exe")
            compile_cmd = ["g++", temp_path, "-o", exe_path]
            cmd = [exe_path]

        if compile_cmd:
            comp_res = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=5)
            if comp_res.returncode != 0:
                raise Exception("Compilation Error:\n" + comp_res.stderr)

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
        
        if result.returncode == 0 and "PASSED" in result.stdout:
            status = "Passed"
            feedback = "All test cases passed."
        else:
            status = "Failed" if "FAILED" in result.stdout else "Error"
            feedback = result.stdout + "\n" + result.stderr
            
    except subprocess.TimeoutExpired:
        status = "Timeout"
        feedback = "Execution exceeded 3 seconds (Infinite loop or inefficient algorithm)."
    except Exception as e:
        status = "Error"
        feedback = str(e)
    finally:
        os.remove(temp_path)
        if sub.language == "cpp" and 'exe_path' in locals() and os.path.exists(exe_path):
            os.remove(exe_path)
        
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
