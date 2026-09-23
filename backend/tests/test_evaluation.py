import pytest
from app.ai.evaluation import calculate_dsa_evaluation
from app.ai.evaluation_models import QualitativeEvaluation, InterviewEvaluationResponse, Weakness
from unittest.mock import patch

@patch("app.ai.evaluation.ai_gateway")
def test_successful_evaluation(mock_ai_gateway):
    # Mock LLM response
    mock_ai_gateway.generate_structured.return_value = QualitativeEvaluation(
        strengths=["Good communication"],
        weaknesses=[Weakness(topic="Hash Maps", issue="Syntax error initially", severity="low")],
        key_mistakes=["Forgot edge case"],
        recommendations=["Practice edge cases"],
        problem_solving_score=8,
        communication_score=9
    )
    
    session = {
        "id": "123",
        "target_role": "SWE",
        "difficulty": "medium",
        "current_stage": "FOLLOW_UP",
        "hints_used": 0,
        "mistakes": 1,
        "state_metadata": {
            "execution": [
                {"status": "PASSED", "passed_tests": 3, "total_tests": 3, "execution_time_ms": 100}
            ]
        }
    }
    
    chat_history = []
    
    result = calculate_dsa_evaluation(session, chat_history)
    
    assert isinstance(result, InterviewEvaluationResponse)
    assert result.final_outcome == "PASSED"
    assert result.overall_score >= 70
    assert result.technical_correctness_score == 10
    assert result.hints_used == 0
    assert result.mistakes == 1

@patch("app.ai.evaluation.ai_gateway")
def test_failed_coding_evaluation(mock_ai_gateway):
    mock_ai_gateway.generate_structured.return_value = QualitativeEvaluation(
        strengths=[],
        weaknesses=[],
        key_mistakes=[],
        recommendations=[],
        problem_solving_score=4,
        communication_score=5
    )
    
    session = {
        "id": "123",
        "target_role": "SWE",
        "difficulty": "medium",
        "current_stage": "DEBUGGING",
        "hints_used": 2,
        "mistakes": 3,
        "state_metadata": {
            "execution": [
                {"status": "FAILED", "passed_tests": 1, "total_tests": 3, "execution_time_ms": 100}
            ]
        }
    }
    
    chat_history = []
    result = calculate_dsa_evaluation(session, chat_history)
    
    assert result.final_outcome == "NEEDS_IMPROVEMENT"
    assert result.technical_correctness_score == 3
    assert result.hints_used == 2
    assert result.mistakes == 3
    assert result.debugging_score <= 5

@patch("app.ai.evaluation.ai_gateway")
def test_debugging_recovery(mock_ai_gateway):
    mock_ai_gateway.generate_structured.return_value = QualitativeEvaluation(
        strengths=[],
        weaknesses=[],
        key_mistakes=[],
        recommendations=[],
        problem_solving_score=7,
        communication_score=7
    )
    
    session = {
        "id": "123",
        "target_role": "SWE",
        "difficulty": "medium",
        "current_stage": "FOLLOW_UP",
        "hints_used": 1,
        "mistakes": 1,
        "state_metadata": {
            "execution": [
                {"status": "FAILED", "passed_tests": 1, "total_tests": 3, "execution_time_ms": 100},
                {"status": "PASSED", "passed_tests": 3, "total_tests": 3, "execution_time_ms": 100}
            ]
        }
    }
    
    chat_history = []
    result = calculate_dsa_evaluation(session, chat_history)
    
    assert result.final_outcome == "PASSED"
    assert result.technical_correctness_score == 10
    assert result.debugging_score == 8  # Recovered score

def test_invalid_score_rejected():
    from pydantic import ValidationError
    try:
        QualitativeEvaluation(
            strengths=[], weaknesses=[], key_mistakes=[], recommendations=[],
            problem_solving_score=15, # Invalid
            communication_score=5
        )
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass

@patch("app.ai.evaluation.ai_gateway")
def test_complexity_scoring(mock_ai_gateway):
    mock_ai_gateway.generate_structured.return_value = QualitativeEvaluation(
        strengths=[], weaknesses=[], key_mistakes=[], recommendations=[],
        problem_solving_score=5, communication_score=5
    )
    
    session = {
        "id": "123",
        "target_role": "SWE",
        "dsa_problem": {
            "optimal_time_complexity": "O(N)",
            "optimal_space_complexity": "O(1)"
        },
        "state_metadata": {
            "complexity_analysis": {
                "claimed_time": "O(N)",
                "claimed_space": "O(1)",
                "correctness": "unknown"
            }
        }
    }
    
    result = calculate_dsa_evaluation(session, [])
    assert result.complexity_score == 6  # matches expected time

    session["state_metadata"]["complexity_analysis"]["claimed_time"] = "O(N^2)"
    session["state_metadata"]["complexity_analysis"]["claimed_space"] = "O(N)"
    result2 = calculate_dsa_evaluation(session, [])
    assert result2.complexity_score == 5 # unknown correctness, didn't match -> default 5

    session["state_metadata"]["complexity_analysis"]["correctness"] = "correct"
    result3 = calculate_dsa_evaluation(session, [])
    assert result3.complexity_score == 10 # explicitly correct
