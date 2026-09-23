from typing import TypedDict, List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel

class InterviewStage(str, Enum):
    QUESTION = "QUESTION"
    CLARIFICATION = "CLARIFICATION"
    APPROACH = "APPROACH"
    COMPLEXITY = "COMPLEXITY"
    OPTIMIZATION = "OPTIMIZATION"
    EDGE_CASES = "EDGE_CASES"
    CODING = "CODING"
    TESTING = "TESTING"
    DEBUGGING = "DEBUGGING"
    FOLLOW_UP = "FOLLOW_UP"
    EVALUATION = "EVALUATION"
    COMPLETED = "COMPLETED"

class InterviewAction(str, Enum):
    ANSWER_CLARIFICATION = "ANSWER_CLARIFICATION"
    ACKNOWLEDGE = "ACKNOWLEDGE"
    PROBE_APPROACH = "PROBE_APPROACH"
    PROBE_COMPLEXITY = "PROBE_COMPLEXITY"
    PROBE_OPTIMIZATION = "PROBE_OPTIMIZATION"
    PROBE_EDGE_CASE = "PROBE_EDGE_CASE"
    EXPLAIN_AND_RETRY = "EXPLAIN_AND_RETRY"
    ASK_COMPLEXITY = "ASK_COMPLEXITY"
    ASK_OPTIMIZATION = "ASK_OPTIMIZATION"
    ASK_EDGE_CASE = "ASK_EDGE_CASE"
    REQUEST_CODE = "REQUEST_CODE"
    REQUEST_DEBUGGING = "REQUEST_DEBUGGING"
    PROVIDE_HINT = "PROVIDE_HINT"
    ASK_FOLLOW_UP = "ASK_FOLLOW_UP"
    END_INTERVIEW = "END_INTERVIEW"

class CandidateAnalysis(BaseModel):
    intent: str  # clarification, approach, complexity, optimization, edge_case, code, debugging, follow_up, hint_request, unrelated, unclear
    approach_quality: str  # strong, partially_correct, weak, incorrect, unknown
    correctness: str  # correct, partially_correct, incorrect, unknown
    complexity_quality: str  # optimal, acceptable, suboptimal, incorrect, unknown
    code_quality: str  # good, acceptable, problematic, unknown
    
    answers_current_question: bool
    asks_clarification: bool
    requests_hint: bool
    complexity_mentioned: bool
    edge_case_mentioned: bool
    coding_ready: bool
    
    claimed_time_complexity: Optional[str] = None
    claimed_space_complexity: Optional[str] = None
    complexity_correctness: Optional[str] = None # correct, partially_correct, incorrect, unknown
    complexity_reasoning: Optional[str] = None
    
    reasoning_summary: str  # concise explanation of what the candidate actually said
    detected_issue: Optional[str]  # concise description of mistake/weakness
    relevant_points: List[str]

class InterviewState(TypedDict):
    session_id: str
    target_role: str
    difficulty: str
    resume_text: str
    dsa_problem: Optional[Dict[str, Any]]
    
    # History
    messages: List[Dict[str, str]]
    
    # State tracking
    current_stage: InterviewStage
    candidate_approach: Optional[str]
    complexity: Optional[str]
    hints_used: int
    mistakes: int
    state_metadata: Dict[str, Any]
    
    # Transient state for the current loop
    latest_user_message: str
    analysis: Optional[CandidateAnalysis]
    next_action: Optional[InterviewAction]
    interviewer_response: Optional[str]

