from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from .auth import verify_user, get_supabase_client
from supabase import Client
from app.ai.learning_extraction import extract_learning_activity
from app.ai.embeddings import generate_embedding
import json

router = APIRouter()

class ChatInput(BaseModel):
    message: str

class SearchQuery(BaseModel):
    query: str
    match_threshold: float = 0.5
    match_count: int = 5

@router.post("/chat")
async def process_learning_chat(chat_input: ChatInput, user = Depends(verify_user)):
    supabase: Client = get_supabase_client()
    
    # 1. Extract structured data using Groq
    try:
        extracted = extract_learning_activity(chat_input.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse learning activity: {str(e)}")
        
    try:
        # 2. Generate embedding for semantic search
        embedding_text = f"{extracted.title} {extracted.topic} {' '.join(extracted.subtopics)} {extracted.description}"
        embedding = generate_embedding(embedding_text)
        
        # 3. Save to Supabase
        data = {
            "user_id": user.user.id,
            "type": extracted.type,
            "title": extracted.title,
            "description": extracted.description,
            "content": extracted.content,
            "topic": extracted.topic,
            "subtopics": extracted.subtopics,
            "embedding": embedding
        }
        
        res = supabase.table("learning_activities").insert(data).execute()
        if not res.data:
            raise Exception("Failed to save learning activity (no data returned)")
            
        return {"message": "Learning recorded successfully", "data": res.data[0]}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database or Embedding Error: {str(e)}")

@router.get("/recent")
async def get_recent_learning(user = Depends(verify_user)):
    supabase: Client = get_supabase_client()
    res = supabase.table("learning_activities")\
        .select("id, title, type, topic, created_at")\
        .eq("user_id", user.user.id)\
        .order("created_at", desc=True)\
        .limit(10)\
        .execute()
    return res.data

@router.get("/{activity_id}")
async def get_learning_detail(activity_id: str, user = Depends(verify_user)):
    supabase: Client = get_supabase_client()
    res = supabase.table("learning_activities")\
        .select("*")\
        .eq("id", activity_id)\
        .eq("user_id", user.user.id)\
        .execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Activity not found")
    return res.data[0]

@router.post("/search")
async def search_learning(search_query: SearchQuery, user = Depends(verify_user)):
    supabase: Client = get_supabase_client()
    query_embedding = generate_embedding(search_query.query)
    
    res = supabase.rpc("match_learning_activities", {
        "query_embedding": query_embedding,
        "match_threshold": search_query.match_threshold,
        "match_count": search_query.match_count,
        "p_user_id": user.user.id
    }).execute()
    
    return res.data
