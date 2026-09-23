from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.ai.gateway import ai_gateway

class EvaluationCategory(BaseModel):
    category: str
    score: int
    feedback: str

class InterviewEvaluation(BaseModel):
    overall_score: int
    categories: List[EvaluationCategory]

def generate_interview_question(resume_text: str, target_role: str, difficulty: str, chat_history: List[dict] = None, mode: str = "general", dsa_problem: dict = None) -> str:
    """
    Generates the next interview question. If chat_history is empty, it generates the first question.
    """
    if chat_history is None:
        chat_history = []
        
    if mode == "dsa" and dsa_problem:
        system_prompt = f"""
        You are an expert, highly rigorous technical interviewer conducting a Data Structures & Algorithms mock interview for a {target_role} position.
        The difficulty level is {difficulty}.
        
        The candidate's resume text (for context):
        {resume_text}
        
        You have assigned the candidate the following problem:
        Title: {dsa_problem.get('title')}
        Optimal Time: {dsa_problem.get('optimal_time_complexity')}
        
        CRITICAL INTERVIEWING INSTRUCTIONS:
        1. If this is the start of the interview (no history), simply greet the candidate, mention the problem title, and ask them how they would approach it conceptually before writing any code. DO NOT copy and paste the problem description back to them (they can already read it on their screen).
        2. Keep your responses extremely conversational, brief, and polished. Do not use robotic markdown like "**Problem Statement**". Just talk to them like a human interviewer.
        3. If they provide code or test results (which will appear as SYSTEM NOTIFICATIONS), evaluate it. DO NOT WRITE CODE FOR THEM.
        4. If their code fails, ask probing questions to help them find the bug instead of telling them the answer.
        5. If their code passes, ask them to analyze the time/space complexity or challenge them to optimize it further if it doesn't meet the optimal bounds.
        6. Maintain a professional, rigorous, and demanding FAANG-level tone.
        """
    else:
        system_prompt = f"""
        You are an expert, highly rigorous technical interviewer conducting a mock interview for a {target_role} position.
        The difficulty level is {difficulty}.
        
        The candidate's resume text is:
        {resume_text}
        
        CRITICAL INTERVIEWING INSTRUCTIONS:
        1. Ask ONE clear, specific question at a time.
        2. If this is the start of the interview, introduce yourself briefly and ask a challenging first question based on their resume.
        3. If there is chat history, DO NOT just move on to the next topic automatically. Evaluate their previous answer silently.
        4. If their answer is superficial, generic, or incomplete, you MUST push back. Ask probing cross-questions, challenge their logic, ask "why did you choose that approach?", or ask them to explain edge cases.
        5. Do not provide the answer to your own question. Do not be overly polite or validating.
        6. Maintain a professional, rigorous, and demanding tone appropriate for a difficult technical interview.
        """
        
    messages = [{"role": "system", "content": system_prompt}]
    
    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    return ai_gateway.generate_chat(messages)

def evaluate_interview(chat_history: List[dict]) -> InterviewEvaluation:
    """
    Evaluates the entire interview transcript and returns structured feedback.
    """
    system_prompt = """
    You are an expert technical interviewer. The interview has concluded. 
    Analyze the transcript and provide a structured JSON evaluation.
    
    Categories should include things like Technical Depth, Communication, Problem Solving.
    """
    
    transcript = "Transcript:\n"
    for msg in chat_history:
        role = "Interviewer" if msg["role"] == "assistant" else "Candidate"
        transcript += f"{role}: {msg['content']}\n\n"
        
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": transcript}
    ]
    
    return ai_gateway.generate_structured(messages, InterviewEvaluation)
