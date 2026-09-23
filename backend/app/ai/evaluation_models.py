from pydantic import BaseModel, Field
from typing import List, Optional

class Weakness(BaseModel):
    topic: str = Field(description="The core topic, e.g., 'Hash Maps', 'Time Complexity'")
    issue: str = Field(description="Specific issue observed")
    severity: str = Field(description="'high', 'medium', or 'low'")

class QualitativeEvaluation(BaseModel):
    strengths: List[str] = Field(description="List of observed strengths")
    weaknesses: List[Weakness] = Field(description="List of structured weaknesses for future learning tracking")
    key_mistakes: List[str] = Field(description="List of critical mistakes made during the interview")
    recommendations: List[str] = Field(description="Actionable recommendations for improvement")
    problem_solving_score: int = Field(ge=0, le=10, description="Qualitative score for problem-solving ability (0-10)")
    communication_score: int = Field(ge=0, le=10, description="Qualitative score for communication clarity (0-10)")

class InterviewEvaluationResponse(BaseModel):
    session_id: str
    overall_score: int
    problem_solving_score: int
    technical_correctness_score: int
    complexity_score: int
    edge_case_score: int
    coding_score: int
    debugging_score: int
    communication_score: int
    hints_used: int
    mistakes: int
    final_outcome: str
    strengths: List[str]
    weaknesses: List[dict]
    key_mistakes: List[str]
    recommendations: List[str]
    created_at: str
