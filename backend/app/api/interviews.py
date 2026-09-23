from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from supabase import Client
from .auth import verify_user, get_supabase_client
from app.ai.stateful_interviewer import interviewer_app
from app.ai.stateful_interviewer_models import InterviewStage, InterviewState
from app.execution import CodeExecutionService, ExecutionRequest, TestCaseRequest

router = APIRouter()

class StartInterviewRequest(BaseModel):
    resume_id: str
    target_role: str
    difficulty: str
    mode: str = "general"
    problem_id: Optional[str] = None
    selection_mode: Optional[str] = "manual"

class ChatMessageRequest(BaseModel):
    session_id: str
    content: str

class EndInterviewRequest(BaseModel):
    session_id: str

class ExecuteInterviewCodeRequest(BaseModel):
    session_id: str
    code: str
    language: str = "python"

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
        if req.problem_id:
            try:
                prob_res = supabase.table("dsa_problems").select("*").eq("id", req.problem_id).execute()
                if prob_res.data:
                    dsa_problem_id = prob_res.data[0]["id"]
                    dsa_problem_context = prob_res.data[0]
                else:
                    raise HTTPException(status_code=404, detail="Selected problem not found")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Database error fetching problem: {str(e)}")
        else:
            from .dsa import generate_problem, GenerateProblemRequest
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
        "dsa_problem_id": dsa_problem_id,
        "current_stage": "QUESTION",
        "state_metadata": {
            "selection_mode": req.selection_mode
        }
    }
    
    try:
        session_res = supabase.table("interview_sessions").insert(session_data).execute()
        session_id = session_res.data[0]["id"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    # Generate First Question via LangGraph
    initial_state = {
        "session_id": session_id,
        "target_role": req.target_role,
        "difficulty": req.difficulty,
        "resume_text": resume_text,
        "dsa_problem": dsa_problem_context,
        "messages": [],
        "current_stage": InterviewStage.QUESTION,
        "candidate_approach": None,
        "complexity": None,
        "hints_used": 0,
        "mistakes": 0,
        "latest_user_message": ""
    }
    
    try:
        final_state = interviewer_app.invoke(initial_state)
        first_q = final_state["interviewer_response"]
        
        # Persist new state
        supabase.table("interview_sessions").update({
            "current_stage": final_state.get("current_stage", "QUESTION"),
            "state_metadata": {"next_action": final_state.get("next_action")}
        }).eq("id", session_id).execute()
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")
        
    # Save AI message
    msg_data = {
        "session_id": session_id,
        "role": "assistant",
        "content": first_q,
        "metadata": {"stage": final_state.get("current_stage"), "action": final_state.get("next_action")}
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
    
    session_res = supabase.table("interview_sessions").select("*, resumes(parsed_content)").eq("id", req.session_id).eq("user_id", user.user.id).execute()
    if not session_res.data:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = session_res.data[0]
    resume_text = session["resumes"]["parsed_content"]
    
    content = req.content
            
    # Save User Message
    user_msg_data = {
        "session_id": req.session_id,
        "role": "user",
        "content": content
    }
    supabase.table("interview_messages").insert(user_msg_data).execute()
    
    # Fetch History
    history_res = supabase.table("interview_messages").select("role, content").eq("session_id", req.session_id).order("created_at").execute()
    chat_history = [{"role": m["role"], "content": m["content"]} for m in history_res.data]
    
    dsa_problem_context = None
    if session.get("dsa_problem_id"):
        prob_res = supabase.table("dsa_problems").select("*").eq("id", session["dsa_problem_id"]).execute()
        if prob_res.data:
            dsa_problem_context = prob_res.data[0]
            
    # LangGraph state construction
    current_state = {
        "session_id": req.session_id,
        "target_role": session["target_role"],
        "difficulty": session["difficulty"],
        "resume_text": resume_text,
        "dsa_problem": dsa_problem_context,
        "messages": chat_history,
        "current_stage": InterviewStage(session.get("current_stage") or "QUESTION"),
        "candidate_approach": session.get("candidate_approach"),
        "complexity": session.get("complexity"),
        "hints_used": session.get("hints_used", 0),
        "mistakes": session.get("mistakes", 0),
        "state_metadata": session.get("state_metadata") or {},
        "latest_user_message": content
    }
    
    # Invoke state machine
    try:
        final_state = interviewer_app.invoke(current_state)
        next_q = final_state["interviewer_response"]
        
        # Persist updated state safely
        update_data = {
            "current_stage": final_state.get("current_stage"),
            "hints_used": final_state.get("hints_used", current_state["hints_used"]),
            "mistakes": final_state.get("mistakes", current_state["mistakes"]),
            "state_metadata": final_state.get("state_metadata", current_state["state_metadata"])
        }
        update_data["state_metadata"]["next_action"] = final_state.get("next_action")
        
        if final_state.get("candidate_approach"):
            update_data["candidate_approach"] = final_state["candidate_approach"]
        if final_state.get("complexity"):
            update_data["complexity"] = final_state["complexity"]
            
        try:
            supabase.table("interview_sessions").update(update_data).eq("id", req.session_id).execute()
        except Exception as e:
            if "42703" in str(e):
                # Columns don't exist. Ignore state persistence for now to prevent crashing.
                pass
            else:
                raise
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI/State Error: {str(e)}")
        
    # Save AI Message
    ai_msg_data = {
        "session_id": req.session_id,
        "role": "assistant",
        "content": next_q,
        "metadata": {"stage": final_state.get("current_stage"), "action": final_state.get("next_action")}
    }
    supabase.table("interview_messages").insert(ai_msg_data).execute()
    
    return {"message": next_q}

@router.post("/evaluate")
async def evaluate_session(req: EndInterviewRequest, user = Depends(verify_user)):
    supabase: Client = get_supabase_client()
    
    session_res = supabase.table("interview_sessions").select("*").eq("id", req.session_id).eq("user_id", user.user.id).execute()
    if not session_res.data:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = session_res.data[0]
    
    # If already evaluated, return the persisted evaluation
    if session.get("evaluation_data"):
        return session["evaluation_data"]
        
    import datetime
    supabase.table("interview_sessions").update({"status": "completed", "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}).eq("id", req.session_id).execute()
    
    history_res = supabase.table("interview_messages").select("role, content").eq("session_id", req.session_id).order("created_at").execute()
    chat_history = history_res.data
    
    # Fetch problem metadata for accurate complexity scoring
    if session.get("dsa_problem_id"):
        prob_res = supabase.table("dsa_problems").select("*").eq("id", session["dsa_problem_id"]).execute()
        if prob_res.data:
            session["dsa_problem"] = prob_res.data[0]
            
    try:
        from app.ai.evaluation import calculate_dsa_evaluation
        evaluation = calculate_dsa_evaluation(session, chat_history)
        eval_dict = evaluation.model_dump()
        
        # Process Learning Recommendations
        learning_recommendations = []
        for w in evaluation.weaknesses:
            from app.ai.embeddings import generate_embedding
            try:
                # Semantic search for related learning
                search_query = f"{w['topic']} {w['issue']}"
                query_embedding = generate_embedding(search_query)
                
                # Check DB for matches
                match_res = supabase.rpc("match_learning_activities", {
                    "query_embedding": query_embedding,
                    "match_threshold": 0.6,
                    "match_count": 3,
                    "p_user_id": user.user.id
                }).execute()
                
                matches = match_res.data or []
                related_ids = [m["id"] for m in matches]
                
                rec = {
                    "topic": w["topic"],
                    "issue": w["issue"],
                    "severity": w["severity"],
                    "related_learning_ids": related_ids,
                    "recommendation_type": "REVISE_EXISTING" if related_ids else "LEARN_NEW"
                }
                learning_recommendations.append(rec)
            except Exception as e:
                import logging
                logging.error(f"Failed to fetch learning recommendation for weakness: {e}")
                rec = {
                    "topic": w["topic"],
                    "issue": w["issue"],
                    "severity": w["severity"],
                    "related_learning_ids": [],
                    "recommendation_type": "LEARN_NEW"
                }
                learning_recommendations.append(rec)
                
        eval_dict["learning_recommendations"] = learning_recommendations
        
        # Persist to database
        try:
            supabase.table("interview_sessions").update({
                "overall_score": evaluation.overall_score,
                "evaluation_data": eval_dict
            }).eq("id", req.session_id).execute()
        except Exception as e:
            if "42703" in str(e):
                supabase.table("interview_sessions").update({
                    "overall_score": evaluation.overall_score,
                    "state_metadata": {"evaluation_data": eval_dict} # Save in state_metadata instead!
                }).eq("id", req.session_id).execute()
            else:
                raise
        
        return eval_dict
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Evaluation Error: {str(e)}")

@router.get("/{session_id}/evaluation")
async def get_evaluation(session_id: str, user = Depends(verify_user)):
    supabase: Client = get_supabase_client()
    try:
        session_res = supabase.table("interview_sessions").select("evaluation_data, user_id").eq("id", session_id).execute()
    except Exception as e:
        if "42703" in str(e):
            try:
                session_res = supabase.table("interview_sessions").select("state_metadata, user_id").eq("id", session_id).execute()
            except Exception as inner_e:
                if "42703" in str(inner_e):
                    session_res = supabase.table("interview_sessions").select("user_id").eq("id", session_id).execute()
                else:
                    raise
        else:
            raise
    
    if not session_res.data:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session_res.data[0]["user_id"] != user.user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    eval_data = session_res.data[0].get("evaluation_data")
    if not eval_data and session_res.data[0].get("state_metadata"):
        eval_data = session_res.data[0].get("state_metadata", {}).get("evaluation_data")
        
    if not eval_data:
        raise HTTPException(status_code=404, detail="Evaluation not found for this session")
        
    return eval_data

@router.post("/execute")
async def execute_code(req: ExecuteInterviewCodeRequest, user = Depends(verify_user)):
    supabase: Client = get_supabase_client()
    
    session_res = supabase.table("interview_sessions").select("*, resumes(parsed_content)").eq("id", req.session_id).eq("user_id", user.user.id).execute()
    if not session_res.data:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = session_res.data[0]
    resume_text = session["resumes"]["parsed_content"]
    
    if session.get("interview_mode") != "dsa" or not session.get("dsa_problem_id"):
        raise HTTPException(status_code=400, detail="Not a DSA session")
        
    tests_res = supabase.table("dsa_test_cases").select("id, input_data, expected_output, is_hidden").eq("problem_id", session["dsa_problem_id"]).execute()
    test_cases = [TestCaseRequest(**t) for t in tests_res.data]
    
    exec_req = ExecutionRequest(
        language=req.language,
        source_code=req.code,
        test_cases=test_cases
    )
    
    exec_res = CodeExecutionService.execute(exec_req)
    
    if exec_res.status == "SANDBOX_UNAVAILABLE":
        raise HTTPException(status_code=503, detail="SANDBOX_UNAVAILABLE")
        
    passed_count = sum(1 for t in exec_res.test_results if t.passed)
    total_count = len(exec_res.test_results)
    
    status_str = "PASSED" if exec_res.status == "PASSED" else "FAILED"
    sys_content = f"[SYSTEM NOTIFICATION: The candidate executed code. Status: {exec_res.status}. Passed {passed_count}/{total_count} tests."
    if exec_res.stderr:
        sys_content += f" Error: {exec_res.stderr}"
    sys_content += "]"
    
    user_msg_data = {
        "session_id": req.session_id,
        "role": "user",
        "content": sys_content
    }
    supabase.table("interview_messages").insert(user_msg_data).execute()
    
    history_res = supabase.table("interview_messages").select("role, content").eq("session_id", req.session_id).order("created_at").execute()
    chat_history = [{"role": m["role"], "content": m["content"]} for m in history_res.data]
    
    dsa_problem_context = None
    prob_res = supabase.table("dsa_problems").select("*").eq("id", session["dsa_problem_id"]).execute()
    if prob_res.data:
        dsa_problem_context = prob_res.data[0]
        
    current_state = {
        "session_id": req.session_id,
        "target_role": session["target_role"],
        "difficulty": session["difficulty"],
        "resume_text": resume_text,
        "dsa_problem": dsa_problem_context,
        "messages": chat_history,
        "current_stage": InterviewStage(session.get("current_stage") or "QUESTION"),
        "candidate_approach": session.get("candidate_approach"),
        "complexity": session.get("complexity"),
        "hints_used": session.get("hints_used", 0),
        "mistakes": session.get("mistakes", 0),
        "state_metadata": session.get("state_metadata") or {},
        "latest_user_message": sys_content
    }
    
    if "execution" not in current_state["state_metadata"]:
        current_state["state_metadata"]["execution"] = []
    current_state["state_metadata"]["execution"].append({
        "status": exec_res.status,
        "passed_tests": passed_count,
        "total_tests": total_count,
        "execution_time_ms": exec_res.execution_time_ms
    })
    
    try:
        final_state = interviewer_app.invoke(current_state)
        next_q = final_state["interviewer_response"]
        
        update_data = {
            "current_stage": final_state.get("current_stage"),
            "hints_used": final_state.get("hints_used", current_state["hints_used"]),
            "mistakes": final_state.get("mistakes", current_state["mistakes"]),
            "state_metadata": final_state.get("state_metadata", current_state["state_metadata"])
        }
        update_data["state_metadata"]["next_action"] = final_state.get("next_action")
        
        if final_state.get("candidate_approach"):
            update_data["candidate_approach"] = final_state["candidate_approach"]
        if final_state.get("complexity"):
            update_data["complexity"] = final_state["complexity"]
            
        try:
            supabase.table("interview_sessions").update(update_data).eq("id", req.session_id).execute()
        except Exception as e:
            if "42703" in str(e):
                # Columns don't exist. Ignore state persistence for now to prevent crashing.
                pass
            else:
                raise
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI/State Error: {str(e)}")
        
    ai_msg_data = {
        "session_id": req.session_id,
        "role": "assistant",
        "content": next_q,
        "metadata": {"stage": final_state.get("current_stage"), "action": final_state.get("next_action")}
    }
    supabase.table("interview_messages").insert(ai_msg_data).execute()
    
    return {
        "execution_result": exec_res.model_dump(),
        "interviewer_response": next_q
    }



@router.get("/recommend-dsa")
async def recommend_dsa_problem(user = Depends(verify_user)):
    from app.ai.dsa_selector import DSASelector
    supabase: Client = get_supabase_client()
    selector = DSASelector(supabase, user.user.id)
    recommendation = selector.recommend_problem()
    if not recommendation:
        raise HTTPException(status_code=404, detail="No suitable problems found in database")
    return recommendation
