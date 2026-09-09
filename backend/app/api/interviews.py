from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from supabase import Client
from .auth import verify_user, get_supabase_client
from app.ai.interview_bot import generate_interview_question, evaluate_interview

router = APIRouter()

class StartInterviewRequest(BaseModel):
    resume_id: str
    target_role: str
    difficulty: str
    mode: str = "general"

class ChatMessageRequest(BaseModel):
    session_id: str
    content: str
    current_code: str | None = None
    execution_results: str | None = None

class EndInterviewRequest(BaseModel):
    session_id: str

@router.post("/start")
async def start_interview(req: StartInterviewRequest, user = Depends(verify_user)):
    supabase: Client = get_supabase_client()
    
    # Fetch Resume
    resume_res = supabase.table("resumes").select("parsed_content").eq("id", req.resume_id).eq("user_id", user.user.id).execute()
    if not resume_res.data:
        raise HTTPException(status_code=404, detail="Resume not found")
        
    resume_text = resume_res.data[0]["parsed_content"]
    
    dsa_problem_id = None
    dsa_problem_context = None
    
    if req.mode == "dsa":
        # Generate DSA Problem
        from .dsa import generate_problem, GenerateProblemRequest
        
        # Map interview difficulty to LeetCode-style difficulty for the DB constraint
        diff_map = {
            "beginner": "Easy",
            "intermediate": "Medium",
            "advanced": "Hard",
            "expert": "Hard"
        }
        mapped_difficulty = diff_map.get(req.difficulty.lower(), "Medium")
        
        try:
            prob = generate_problem(GenerateProblemRequest(difficulty=mapped_difficulty), user)
            dsa_problem_id = prob["id"]
            dsa_problem_context = prob
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate DSA problem: {str(e)}")
    
    # Create Session
    session_data = {
        "user_id": user.user.id,
        "resume_id": req.resume_id,
        "target_role": req.target_role,
        "difficulty": req.difficulty,
        "status": "active",
        "interview_mode": req.mode,
        "dsa_problem_id": dsa_problem_id
    }
    
    try:
        session_res = supabase.table("interview_sessions").insert(session_data).execute()
        session_id = session_res.data[0]["id"]
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database error (Did you run the SQL migration?): {str(e)}")
    
    # Generate First Question
    try:
        first_q = generate_interview_question(resume_text, req.target_role, req.difficulty, [], mode=req.mode, dsa_problem=dsa_problem_context)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")
        
    # Save first message
    msg_data = {
        "session_id": session_id,
        "role": "assistant",
        "content": first_q
    }
    supabase.table("interview_messages").insert(msg_data).execute()
    
    return {
        "session_id": session_id,
        "message": first_q,
        "dsa_problem_id": dsa_problem_id
    }

@router.post("/chat")
async def chat_interview(req: ChatMessageRequest, user = Depends(verify_user)):
    supabase: Client = get_supabase_client()
    
    # Fetch Session details
    session_res = supabase.table("interview_sessions").select("*, resumes(parsed_content)").eq("id", req.session_id).eq("user_id", user.user.id).execute()
    if not session_res.data:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = session_res.data[0]
    resume_text = session["resumes"]["parsed_content"]
    
    # Inject code execution context if present
    content = req.content
    if session.get("interview_mode") == "dsa":
        if req.execution_results:
            content += f"\n\n[SYSTEM NOTIFICATION: The candidate just ran their code. Result: {req.execution_results}]"
        elif req.current_code:
            content += f"\n\n[SYSTEM NOTIFICATION: The candidate's current code is:\n{req.current_code}]"
            
    # Save User Message
    user_msg_data = {
        "session_id": req.session_id,
        "role": "user",
        "content": content
    }
    supabase.table("interview_messages").insert(user_msg_data).execute()
    
    # Fetch Chat History
    history_res = supabase.table("interview_messages").select("role, content").eq("session_id", req.session_id).order("created_at").execute()
    chat_history = history_res.data
    
    dsa_problem_context = None
    if session.get("dsa_problem_id"):
        prob_res = supabase.table("dsa_problems").select("*").eq("id", session["dsa_problem_id"]).execute()
        if prob_res.data:
            dsa_problem_context = prob_res.data[0]
    
    # Generate Next Question
    try:
        next_q = generate_interview_question(
            resume_text, 
            session["target_role"], 
            session["difficulty"], 
            chat_history,
            mode=session.get("interview_mode", "general"),
            dsa_problem=dsa_problem_context
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")
        
    # Save AI Message
    ai_msg_data = {
        "session_id": req.session_id,
        "role": "assistant",
        "content": next_q
    }
    supabase.table("interview_messages").insert(ai_msg_data).execute()
    
    return {"message": next_q}

@router.post("/evaluate")
async def evaluate_session(req: EndInterviewRequest, user = Depends(verify_user)):
    supabase: Client = get_supabase_client()
    
    # Verify
    session_res = supabase.table("interview_sessions").select("id").eq("id", req.session_id).eq("user_id", user.user.id).execute()
    if not session_res.data:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Mark completed
    import datetime
    supabase.table("interview_sessions").update({"status": "completed", "completed_at": datetime.datetime.utcnow().isoformat()}).eq("id", req.session_id).execute()
    
    # Fetch Chat History
    history_res = supabase.table("interview_messages").select("role, content").eq("session_id", req.session_id).order("created_at").execute()
    chat_history = history_res.data
    
    # Evaluate
    try:
        evaluation = evaluate_interview(chat_history)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Evaluation Error: {str(e)}")
        
    # Update Session overall score
    supabase.table("interview_sessions").update({"overall_score": evaluation.overall_score}).eq("id", req.session_id).execute()
    
    # Insert categories
    cat_data = []
    for cat in evaluation.categories:
        cat_data.append({
            "session_id": req.session_id,
            "category": cat.category,
            "score": cat.score,
            "feedback": cat.feedback
        })
        
    if cat_data:
        supabase.table("interview_evaluations").insert(cat_data).execute()
        
    return evaluation.model_dump()
