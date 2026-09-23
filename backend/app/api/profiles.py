from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from .auth import verify_user, get_supabase_client
from supabase import Client

router = APIRouter()

class ProfileUpdate(BaseModel):
    name: str
    target_role: str | None = None
    target_company: str | None = None

@router.get("/")
async def get_profile(user = Depends(verify_user)):
    supabase: Client = get_supabase_client()
    try:
        res = supabase.table("profiles").select("*").eq("user_id", user.user.id).execute()
        if not res.data:
            return {} # Return empty profile instead of 404 to avoid crashing frontend
        return res.data[0]
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {} # Return empty profile if table doesn't exist yet

@router.post("/")
async def create_or_update_profile(profile: ProfileUpdate, user = Depends(verify_user)):
    supabase: Client = get_supabase_client()
    
    data = {
        "user_id": user.user.id,
        "name": profile.name,
        "target_role": profile.target_role,
        "target_company": profile.target_company
    }
    
    # Supabase UPSERT
    res = supabase.table("profiles").upsert(data, on_conflict="user_id").execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to update profile")
    return res.data[0]

@router.get("/preparation")
async def get_preparation_profile(user = Depends(verify_user)):
    supabase: Client = get_supabase_client()
    user_id = user.user.id

    # 1. Fetch Profile
    profile_res = supabase.table("profiles").select("target_role, target_company").eq("user_id", user_id).execute()
    target_role = profile_res.data[0].get("target_role") if profile_res.data else None
    target_company = profile_res.data[0].get("target_company") if profile_res.data else None
    
    if not target_role:
        # fallback to latest JD title
        jd_res = supabase.table("job_descriptions").select("title, company").eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()
        target_role = jd_res.data[0].get("title") if jd_res.data else None
        if not target_company:
            target_company = jd_res.data[0].get("company") if jd_res.data else None

    # 2. Fetch Resume Profile
    try:
        resume_res = supabase.table("resume_analyses").select("id, overall_score, gaps, recommendations, preparation_recommendations").eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()
    except Exception as e:
        if "42703" in str(e):
            resume_res = supabase.table("resume_analyses").select("id, overall_score, gaps, recommendations").eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()
        else:
            raise
    
    resume_profile = None
    if resume_res.data:
        r = resume_res.data[0]
        
        # Fallback for preparation_recommendations if they aren't structured yet
        prep_recs = r.get("preparation_recommendations") or []
        if not prep_recs and r.get("recommendations"):
            # Map legacy string recommendations to structured format
            for rec_str in r.get("recommendations"):
                if isinstance(rec_str, str):
                    prep_recs.append({
                        "topic": rec_str[:50] + ("..." if len(rec_str) > 50 else ""),
                        "recommendation_type": "LEARN_NEW",
                        "severity": "MEDIUM",
                        "reason": rec_str,
                        "gap_type": "MISSING_SKILL"
                    })
                elif isinstance(rec_str, dict):
                    prep_recs.append(rec_str) # In case we saved structured data inside recommendations
        
        resume_profile = {
            "latest_resume_score": r.get("overall_score"),
            "latest_resume_analysis_id": r.get("id"),
            "major_resume_gaps": r.get("gaps") or [],
            "preparation_recommendations": prep_recs
        }

    # 3. Fetch Learning Profile
    learning_res = supabase.table("learning_activities").select("id, topic, created_at").eq("user_id", user_id).order("created_at", desc=True).execute()
    
    recently_learned = []
    topics_learned = set()
    for act in (learning_res.data or [])[:5]:
        recently_learned.append({"id": act["id"], "topic": act["topic"], "created_at": act["created_at"]})
    for act in (learning_res.data or []):
        if act.get("topic"):
            topics_learned.add(act["topic"].lower())

    learning_profile = {
        "total_learning_activities": len(learning_res.data or []),
        "recent_topics": recently_learned,
        "recently_learned": recently_learned,
        "topics_needing_revision": [] # populated below
    }

    # 4. Fetch Interview Profile
    try:
        interviews_res = supabase.table("interview_sessions").select("id, evaluation_data, status").eq("user_id", user_id).eq("status", "completed").order("completed_at", desc=True).execute()
        interviews = interviews_res.data or []
    except Exception as e:
        if "42703" in str(e):
            try:
                interviews_res = supabase.table("interview_sessions").select("id, status, state_metadata").eq("user_id", user_id).eq("status", "completed").order("completed_at", desc=True).execute()
                interviews = interviews_res.data or []
            except Exception as inner_e:
                if "42703" in str(inner_e):
                    interviews_res = supabase.table("interview_sessions").select("id, status").eq("user_id", user_id).eq("status", "completed").order("completed_at", desc=True).execute()
                    interviews = interviews_res.data or []
                else:
                    raise
        else:
            raise
    total_interviews = len(interviews)
    latest_score = None
    avg_score = None
    recurring_weaknesses = {}
    total_hints = 0
    total_mistakes = 0

    if total_interviews > 0:
        latest_eval = interviews[0].get("evaluation_data") or {}
        latest_score = latest_eval.get("overall_score")
        
        score_sum = 0
        scored_interviews = 0
        for idx, iv in enumerate(interviews):
            eval_data = iv.get("evaluation_data")
            if not eval_data and iv.get("state_metadata"):
                eval_data = iv.get("state_metadata", {}).get("evaluation_data")
            eval_data = eval_data or {}
            
            sc = eval_data.get("overall_score")
            if sc is not None:
                score_sum += sc
                scored_interviews += 1
                
            total_hints += eval_data.get("technical_score_details", {}).get("hints_used", 0)
            total_mistakes += eval_data.get("technical_score_details", {}).get("mistakes_made", 0)
            
            weaknesses = eval_data.get("weaknesses") or []
            for w in weaknesses:
                topic = w.get("topic", "")
                severity = w.get("severity", "LOW").upper()
                norm_topic = topic.strip().lower()
                if not norm_topic:
                    continue
                if norm_topic not in recurring_weaknesses:
                    recurring_weaknesses[norm_topic] = {
                        "topic": topic,
                        "occurrences": 1,
                        "severity": severity,
                        "is_recent": (idx == 0)
                    }
                else:
                    recurring_weaknesses[norm_topic]["occurrences"] += 1
                    if severity == "HIGH":
                        recurring_weaknesses[norm_topic]["severity"] = "HIGH"
                    elif severity == "MEDIUM" and recurring_weaknesses[norm_topic]["severity"] == "LOW":
                        recurring_weaknesses[norm_topic]["severity"] = "MEDIUM"

        if scored_interviews > 0:
            avg_score = round(score_sum / scored_interviews, 1)

    interview_profile = {
        "total_completed_interviews": total_interviews,
        "latest_interview_score": latest_score,
        "average_interview_score": avg_score,
        "interview_weaknesses": list(recurring_weaknesses.values()),
        "total_hints_used": total_hints,
        "total_mistakes": total_mistakes
    }

    # 5. Unified Next Actions Engine
    unified_actions = {}
    
    if resume_profile:
        for rec in resume_profile.get("preparation_recommendations", []):
            topic = rec.get("topic", "")
            norm = topic.strip().lower()
            if not norm:
                continue
            unified_actions[norm] = {
                "topic": topic,
                "action": rec.get("recommendation_type", "LEARN_NEW"),
                "source": "RESUME",
                "severity": rec.get("severity", "MEDIUM").upper(),
                "reason": rec.get("reason"),
                "occurrences": 1
            }
            
    for w in recurring_weaknesses.values():
        norm = w["topic"].strip().lower()
        if norm in unified_actions:
            unified_actions[norm]["source"] = "MULTIPLE"
            unified_actions[norm]["occurrences"] += w["occurrences"]
            if w["severity"] == "HIGH":
                unified_actions[norm]["severity"] = "HIGH"
        else:
            action_type = "REVISE_EXISTING" if norm in topics_learned else "LEARN_NEW"
            unified_actions[norm] = {
                "topic": w["topic"],
                "action": action_type,
                "source": "INTERVIEW",
                "severity": w["severity"].upper(),
                "reason": "Identified as a weakness in interviews",
                "occurrences": w["occurrences"]
            }
            
    high_priority = []
    medium_priority = []
    low_priority = []
    
    for action in unified_actions.values():
        if action["severity"] == "HIGH" or action["source"] == "MULTIPLE" or action["occurrences"] >= 2:
            action["priority"] = "HIGH"
            high_priority.append(action)
        elif action["severity"] == "MEDIUM":
            action["priority"] = "MEDIUM"
            medium_priority.append(action)
        else:
            action["priority"] = "LOW"
            low_priority.append(action)
            
    high_priority.sort(key=lambda x: x["occurrences"], reverse=True)
    medium_priority.sort(key=lambda x: x["occurrences"], reverse=True)
    low_priority.sort(key=lambda x: x["occurrences"], reverse=True)
    
    next_actions = (high_priority + medium_priority + low_priority)[:5]
    
    for action in unified_actions.values():
        if action["action"] == "REVISE_EXISTING":
            learning_profile["topics_needing_revision"].append(action["topic"])

    return {
        "user_id": user_id,
        "target_role": target_role,
        "target_company": target_company,
        "resume": resume_profile,
        "learning": learning_profile,
        "interview": interview_profile,
        "preparation": {
            "high_priority_items": high_priority,
            "medium_priority_items": medium_priority,
            "low_priority_items": low_priority,
            "next_recommended_actions": next_actions
        }
    }
