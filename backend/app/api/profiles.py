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
