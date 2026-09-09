from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from .auth import verify_user, get_supabase_client
from supabase import Client

router = APIRouter()

class GoalCreate(BaseModel):
    title: str
    description: str | None = None
    goal_type: str = "daily" # e.g. daily, long-term

class GoalUpdate(BaseModel):
    status: str # pending, completed, cancelled

@router.get("/")
async def get_goals(user = Depends(verify_user)):
    supabase: Client = get_supabase_client()
    res = supabase.table("goals")\
        .select("*")\
        .eq("user_id", user.user.id)\
        .order("created_at", desc=True)\
        .execute()
    return res.data

@router.post("/")
async def create_goal(goal: GoalCreate, user = Depends(verify_user)):
    supabase: Client = get_supabase_client()
    data = {
        "user_id": user.user.id,
        "title": goal.title,
        "description": goal.description,
        "goal_type": goal.goal_type
    }
    res = supabase.table("goals").insert(data).execute()
    return res.data[0]

@router.patch("/{goal_id}")
async def update_goal_status(goal_id: str, goal_update: GoalUpdate, user = Depends(verify_user)):
    supabase: Client = get_supabase_client()
    update_data = {"status": goal_update.status}
    if goal_update.status == "completed":
        update_data["completed_at"] = "now()"
        
    res = supabase.table("goals")\
        .update(update_data)\
        .eq("id", goal_id)\
        .eq("user_id", user.user.id)\
        .execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Goal not found")
    return res.data[0]
