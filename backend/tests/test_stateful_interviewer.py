import pytest
from app.ai.stateful_interviewer import decide_next_action
from app.ai.stateful_interviewer_models import InterviewState, InterviewStage, InterviewAction, CandidateAnalysis

def get_base_state(stage: InterviewStage, analysis: CandidateAnalysis, hints=0, mistakes=0) -> InterviewState:
    return {
        "session_id": "test",
        "target_role": "SWE",
        "difficulty": "Medium",
        "resume_text": "...",
        "dsa_problem": None,
        "messages": [],
        "current_stage": stage,
        "candidate_approach": None,
        "complexity": None,
        "hints_used": hints,
        "mistakes": mistakes,
        "state_metadata": {},
        "latest_user_message": "User input",
        "analysis": analysis,
        "next_action": None,
        "interviewer_response": None
    }

def get_analysis(**kwargs):
    default = {
        "intent": "approach",
        "approach_quality": "unknown",
        "correctness": "unknown",
        "complexity_quality": "unknown",
        "code_quality": "unknown",
        "answers_current_question": True,
        "asks_clarification": False,
        "requests_hint": False,
        "complexity_mentioned": False,
        "edge_case_mentioned": False,
        "coding_ready": False,
        "reasoning_summary": "Summary",
        "detected_issue": None,
        "relevant_points": []
    }
    default.update(kwargs)
    return CandidateAnalysis(**default)

def test_clarification_does_not_advance():
    a = get_analysis(intent="clarification", asks_clarification=True)
    state = get_base_state(InterviewStage.APPROACH, a)
    res = decide_next_action(state)
    assert res["current_stage"] == InterviewStage.APPROACH
    assert res["next_action"] == InterviewAction.ANSWER_CLARIFICATION

def test_weak_approach_does_not_advance():
    a = get_analysis(intent="approach", approach_quality="weak")
    state = get_base_state(InterviewStage.APPROACH, a)
    res = decide_next_action(state)
    assert res["current_stage"] == InterviewStage.APPROACH
    assert res["next_action"] == InterviewAction.PROBE_APPROACH

def test_partially_correct_approach_does_not_advance():
    a = get_analysis(intent="approach", approach_quality="partially_correct")
    state = get_base_state(InterviewStage.APPROACH, a)
    res = decide_next_action(state)
    assert res["current_stage"] == InterviewStage.APPROACH
    assert res["next_action"] == InterviewAction.PROBE_APPROACH

def test_strong_approach_advances():
    a = get_analysis(intent="approach", approach_quality="strong")
    state = get_base_state(InterviewStage.APPROACH, a)
    res = decide_next_action(state)
    assert res["current_stage"] == InterviewStage.COMPLEXITY
    assert res["next_action"] == InterviewAction.ASK_COMPLEXITY

def test_suboptimal_complexity_does_not_advance():
    a = get_analysis(intent="complexity", complexity_quality="suboptimal")
    state = get_base_state(InterviewStage.COMPLEXITY, a)
    res = decide_next_action(state)
    assert res["current_stage"] == InterviewStage.COMPLEXITY
    assert res["next_action"] == InterviewAction.PROBE_COMPLEXITY

def test_optimal_complexity_advances():
    a = get_analysis(intent="complexity", complexity_quality="optimal")
    state = get_base_state(InterviewStage.COMPLEXITY, a)
    res = decide_next_action(state)
    assert res["current_stage"] == InterviewStage.OPTIMIZATION
    assert res["next_action"] == InterviewAction.ASK_OPTIMIZATION

def test_hint_increments_hints_used():
    a = get_analysis(intent="hint_request", requests_hint=True)
    state = get_base_state(InterviewStage.OPTIMIZATION, a, hints=0)
    res = decide_next_action(state)
    assert res["current_stage"] == InterviewStage.OPTIMIZATION
    assert res["next_action"] == InterviewAction.PROVIDE_HINT
    assert res["hints_used"] == 1
    assert res["state_metadata"]["current_hint_level"] == 1

def test_mistake_increments():
    a = get_analysis(intent="complexity", complexity_quality="incorrect", detected_issue="Forgot inner loop")
    state = get_base_state(InterviewStage.COMPLEXITY, a, mistakes=0)
    res = decide_next_action(state)
    assert res["mistakes"] == 1
    assert len(res["state_metadata"]["mistake_history"]) == 1
    assert res["state_metadata"]["mistake_history"][0]["issue"] == "Forgot inner loop"

def test_coding_success():
    a = get_analysis(intent="code", code_quality="good", correctness="correct")
    state = get_base_state(InterviewStage.CODING, a)
    res = decide_next_action(state)
    assert res["current_stage"] == InterviewStage.FOLLOW_UP
    assert res["next_action"] == InterviewAction.ASK_FOLLOW_UP

def test_coding_failure():
    a = get_analysis(intent="code", code_quality="problematic", correctness="incorrect")
    state = get_base_state(InterviewStage.CODING, a)
    res = decide_next_action(state)
    assert res["current_stage"] == InterviewStage.DEBUGGING
    assert res["next_action"] == InterviewAction.REQUEST_DEBUGGING

def test_debugging_success():
    a = get_analysis(intent="code", correctness="correct")
    state = get_base_state(InterviewStage.DEBUGGING, a)
    res = decide_next_action(state)
    assert res["current_stage"] == InterviewStage.FOLLOW_UP

def test_termination_max_hints():
    a = get_analysis(intent="hint_request", requests_hint=True)
    # Give them 5 hints already so it triggers the safeguard immediately
    state = get_base_state(InterviewStage.APPROACH, a, hints=5)
    res = decide_next_action(state)
    assert res["current_stage"] == InterviewStage.COMPLETED
    assert res["next_action"] == InterviewAction.END_INTERVIEW

def test_termination_max_mistakes():
    a = get_analysis(intent="approach", approach_quality="incorrect")
    # Give them 4 mistakes already
    state = get_base_state(InterviewStage.APPROACH, a, mistakes=4)
    res = decide_next_action(state)
    assert res["current_stage"] == InterviewStage.COMPLETED
    assert res["next_action"] == InterviewAction.END_INTERVIEW
