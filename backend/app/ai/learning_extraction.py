from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.ai.gateway import ai_gateway

class ExtractedLearning(BaseModel):
    type: str = "note" # 'concept', 'problem', 'resource', 'note'
    title: str = "Untitled Learning"
    description: str = ""
    topic: str = "General"
    subtopics: List[str] = []
    content: dict = {} # any additional structured info

def extract_learning_activity(user_input: str) -> ExtractedLearning:
    system_prompt = """
    You are an AI assistant that extracts structured learning activities from user natural language input.
    The user is a software engineering student preparing for placements.
    
    Extract the following fields and return ONLY a valid JSON object matching the requested schema:
    - type: one of ['concept', 'problem', 'resource', 'note']
    - title: A concise title of what was learned based ONLY on the user's input
    - description: A brief summary based ONLY on the user's input
    - topic: Broad topic (e.g., 'DBMS', 'DSA', 'System Design')
    - subtopics: List of specific subtopics mentioned.
    - content: A dictionary with additional details based on the type.
    
    CRITICAL ANTI-HALLUCINATION INSTRUCTION: 
    Do NOT invent or fabricate educational content, concepts, or technical depth that the user did not explicitly state. 
    If the user's input is very short (e.g. "I learned DNS"), simply record it as a short note. 
    Do not auto-generate deep technical notes (like "recursive resolution", "caching", etc.) unless the user mentioned them.
    Preserve the user's statement exactly as the limit of the knowledge.
    """
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]
    
    return ai_gateway.generate_structured(messages, ExtractedLearning)
