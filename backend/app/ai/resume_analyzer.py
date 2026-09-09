import os
import json
from groq import Groq
from pydantic import BaseModel
from typing import List, Optional, Any

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

class StructuredJD(BaseModel):
    title: Optional[str] = "Unknown Role"
    company: Optional[str] = "Unknown Company"
    hard_requirements: List[Any] = []
    soft_skills: List[Any] = []
    tools_and_tech: Any = []

class AnalysisResult(BaseModel):
    overall_score: int = 0
    gaps: List[Any] = []
    recommendations: List[Any] = []

def structure_job_description(raw_jd: str) -> StructuredJD:
    system_prompt = """
    You are an expert technical recruiter. Extract the following from the raw job description:
    - title
    - company
    - hard_requirements
    - soft_skills
    - tools_and_tech
    
    Return a strictly formatted JSON object matching those keys.
    """
    
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": raw_jd}
        ],
        model="openai/gpt-oss-120b",
        response_format={"type": "json_object"}
    )
    
    return StructuredJD(**json.loads(response.choices[0].message.content))

def analyze_resume(parsed_resume: str, structured_jd: StructuredJD) -> AnalysisResult:
    system_prompt = """
    You are an expert technical resume reviewer. Compare the candidate's resume against the structured job description.
    
    Output a JSON object with:
    - overall_score: an integer from 0 to 100 representing the match percentage.
    - gaps: a list of strings detailing required skills or experiences missing from the resume.
    - recommendations: a list of strings providing actionable advice to rewrite specific bullet points.
    """
    
    user_prompt = f"""
    Job Description:
    {structured_jd.model_dump_json()}
    
    Resume:
    {parsed_resume}
    """
    
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        model="openai/gpt-oss-120b",
        response_format={"type": "json_object"}
    )
    
    return AnalysisResult(**json.loads(response.choices[0].message.content))
