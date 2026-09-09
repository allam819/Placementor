import os
import json
from groq import Groq
from pydantic import BaseModel
from typing import List, Optional

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

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
    
    Extract the following fields and return ONLY a valid JSON object:
    - type: one of ['concept', 'problem', 'resource', 'note']
    - title: A concise title of what was learned
    - description: A brief summary
    - topic: Broad topic (e.g., 'DBMS', 'DSA', 'System Design')
    - subtopics: List of specific subtopics. YOU MUST GENERATE AT LEAST 2-3 RELEVANT TAGS EVEN IF THE INPUT IS BRIEF.
    - content: A dictionary with additional details based on the type.
        - If concept: {"quick_notes": ["...", "..."]}
        - If problem: {"approach": "...", "time_complexity": "...", "space_complexity": "..."}
        
    CRITICAL INSTRUCTION: If the user's input is very short (e.g. "DNS in computer networks"), you MUST act as an educator and auto-generate helpful educational notes in the `content` field and auto-generate related tags in `subtopics`. Do not leave them empty!
    
    Ensure the output is strictly valid JSON without markdown wrapping.
    """
    
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        model="openai/gpt-oss-120b",
        response_format={"type": "json_object"}
    )
    
    content = response.choices[0].message.content
    data = json.loads(content)
    return ExtractedLearning(**data)
