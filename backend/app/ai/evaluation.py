import datetime
from typing import List, Dict, Any
from app.ai.gateway import ai_gateway
from app.ai.evaluation_models import QualitativeEvaluation, InterviewEvaluationResponse

def calculate_dsa_evaluation(session: dict, chat_history: List[dict]) -> InterviewEvaluationResponse:
    # 1. Parse Objective Data
    state_metadata = session.get("state_metadata") or {}
    hints_used = session.get("hints_used") or 0
    mistakes = session.get("mistakes") or 0
    executions = state_metadata.get("execution", [])
    
    # Calculate execution/coding stats
    tests_passed = 0
    total_tests = 0
    passed_execution = False
    runtime_errors = 0
    
    if executions:
        best_exec = max(executions, key=lambda x: (x.get("passed_tests", 0), -x.get("total_tests", 1)))
        tests_passed = best_exec.get("passed_tests", 0)
        total_tests = best_exec.get("total_tests", 0)
        passed_execution = any(ex.get("status") == "PASSED" for ex in executions)
        runtime_errors = sum(1 for ex in executions if ex.get("status") in ["RUNTIME_ERROR", "TIMEOUT"])
        
    # 2. Deterministic Scoring (0-10)
    
    # Technical Correctness: based on test cases passed
    technical_correctness_score = 0
    if total_tests > 0:
        technical_correctness_score = int((tests_passed / total_tests) * 10)
        
    # Coding Score: penalize for runtime errors, reward for passing
    coding_score = technical_correctness_score
    if runtime_errors > 0:
        coding_score = max(0, coding_score - min(3, runtime_errors))
        
    # Debugging Score: if there were multiple executions and it eventually passed, that's good.
    # If they failed and never passed, low score. If they passed first try, max score.
    if len(executions) <= 1:
        debugging_score = 10 if passed_execution else (5 if total_tests == 0 else 0)
    else:
        if passed_execution:
            debugging_score = 8 # Recovered
        else:
            debugging_score = max(0, 5 - len(executions))
            
    # Complexity Score Calculation
    complexity_analysis = state_metadata.get("complexity_analysis")
    dsa_problem = session.get("dsa_problem", {})
    expected_time = dsa_problem.get("optimal_time_complexity")
    expected_space = dsa_problem.get("optimal_space_complexity")
    
    # We must not fallback to random math. If we have the analysis, use it.
    if complexity_analysis and (expected_time or expected_space):
        claimed_time = (complexity_analysis.get("claimed_time") or "").strip().lower()
        claimed_space = (complexity_analysis.get("claimed_space") or "").strip().lower()
        
        # If candidate correctly guessed expected metadata
        time_correct = (expected_time and claimed_time == expected_time.lower())
        space_correct = (expected_space and claimed_space == expected_space.lower())
        
        # Or if the analysis explicitly says it was correct
        if complexity_analysis.get("correctness") == "correct":
            complexity_score = 10
        elif complexity_analysis.get("correctness") == "partially_correct" or time_correct or space_correct:
            complexity_score = 6
        elif complexity_analysis.get("correctness") == "incorrect":
            complexity_score = 2
        else:
            complexity_score = 5 # Default if mentioned but correctness unknown
    elif complexity_analysis:
        # We have analysis but no expected metadata to verify it easily
        corr = complexity_analysis.get("correctness")
        if corr == "correct": complexity_score = 10
        elif corr == "partially_correct": complexity_score = 6
        elif corr == "incorrect": complexity_score = 2
        else: complexity_score = 5
    else:
        # Not even mentioned/analyzed
        complexity_score = 0
        
    # Edge Cases: Deduce from mistakes
    edge_case_score = max(0, 10 - (mistakes * 2))
    
    # 3. Formulate transcript summary for LLM
    # We only send a compressed summary to avoid hallucination and reduce tokens
    transcript = ""
    for msg in chat_history:
        role = "Interviewer" if msg["role"] == "assistant" else "Candidate"
        transcript += f"{role}: {msg['content']}\n\n"
        
    sys_prompt = f"""
    You are an expert technical interviewer evaluator.
    The objective interview metrics are:
    - Target Role: {session.get('target_role')} ({session.get('difficulty')})
    - Final Stage Reached: {session.get('current_stage')}
    - Hints Used: {hints_used}
    - Mistakes Logged: {mistakes}
    - Execution Passed: {passed_execution}
    - Tests Passed: {tests_passed}/{total_tests}
    
    Analyze the transcript and provide a structured qualitative evaluation.
    Focus on:
    - Strengths and weaknesses (evidence-based)
    - Actionable recommendations
    - Score problem solving (0-10)
    - Score communication (0-10)
    """
    
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": transcript[:8000]} # Limit transcript length just in case
    ]
    
    qual_eval: QualitativeEvaluation = ai_gateway.generate_structured(messages, QualitativeEvaluation)
    
    # 4. Final Outcome & Overall Score
    # Combine objective and qualitative
    overall_score = int(
        (
            qual_eval.problem_solving_score * 0.25 + 
            technical_correctness_score * 0.25 + 
            coding_score * 0.2 + 
            qual_eval.communication_score * 0.15 + 
            debugging_score * 0.15
        ) - (hints_used * 0.5)
    )
    overall_score = max(0, min(100, overall_score * 10)) # Convert to 100-point scale
    
    if passed_execution and overall_score >= 70:
        final_outcome = "PASSED"
    elif overall_score >= 50:
        final_outcome = "NEEDS_IMPROVEMENT"
    else:
        # If they haven't even run code, or didn't reach coding
        stage = session.get('current_stage')
        if stage in ["QUESTION", "APPROACH", "COMPLEXITY", "OPTIMIZATION", "EDGE_CASES", "CODING"] and not passed_execution and total_tests == 0:
            final_outcome = "INCOMPLETE"
        else:
            final_outcome = "NEEDS_IMPROVEMENT"
            
    # Compile the final result
    result = InterviewEvaluationResponse(
        session_id=str(session.get("id")),
        overall_score=overall_score,
        problem_solving_score=qual_eval.problem_solving_score,
        technical_correctness_score=technical_correctness_score,
        complexity_score=complexity_score,
        edge_case_score=edge_case_score,
        coding_score=coding_score,
        debugging_score=debugging_score,
        communication_score=qual_eval.communication_score,
        hints_used=hints_used,
        mistakes=mistakes,
        final_outcome=final_outcome,
        strengths=qual_eval.strengths,
        weaknesses=[w.model_dump() for w in qual_eval.weaknesses],
        key_mistakes=qual_eval.key_mistakes,
        recommendations=qual_eval.recommendations,
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    
    return result
