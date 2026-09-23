from langgraph.graph import StateGraph, END
from app.ai.gateway import ai_gateway
from app.ai.stateful_interviewer_models import (
    InterviewState, InterviewStage, InterviewAction, CandidateAnalysis
)
import json

def get_stage_context(state: InterviewState) -> str:
    current_stage = state['current_stage']
    problem = state.get("dsa_problem", {})
    context = f"Problem: {problem.get('title')}\n"
    
    # We selectively include context.
    if current_stage == InterviewStage.APPROACH:
        context += f"Candidate's previous approach attempts (if any): {state.get('candidate_approach')}\n"
    elif current_stage == InterviewStage.COMPLEXITY:
        context += f"Accepted Approach: {state.get('candidate_approach')}\n"
    elif current_stage == InterviewStage.OPTIMIZATION:
        context += f"Accepted Approach: {state.get('candidate_approach')}\n"
        context += f"Current Complexity: {state.get('complexity')}\n"
    elif current_stage == InterviewStage.EDGE_CASES:
        context += f"Accepted Approach: {state.get('candidate_approach')}\n"
        context += f"Complexity: {state.get('complexity')}\n"
    elif current_stage in [InterviewStage.CODING, InterviewStage.DEBUGGING]:
        context += f"Accepted Approach: {state.get('candidate_approach')}\n"
        context += f"Complexity: {state.get('complexity')}\n"
        
    return context

def observe_candidate(state: InterviewState) -> InterviewState:
    if not state.get("latest_user_message"):
        return state

    system_prompt = f"""
    You are an expert technical interviewer's silent observation unit.
    Analyze the candidate's latest response.
    Current Interview Stage: {state['current_stage']}
    
    Output a strictly formatted JSON object matching the CandidateAnalysis schema.
    IMPORTANT RULES:
    1. Base your analysis STRICTLY on what the candidate wrote.
    2. Do NOT invent reasoning they did not provide.
    3. Do NOT decide the next stage.
    4. Provide a concise 'reasoning_summary'.
    5. If they made a mistake, describe it in 'detected_issue'.
    """
    
    stage_context = get_stage_context(state)
    history = "\n".join([f"{m['role']}: {m['content']}" for m in state["messages"][-4:]])
    
    user_prompt = f"{stage_context}\n\nRecent History:\n{history}\n\nCandidate's latest input:\n{state['latest_user_message']}"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    analysis = ai_gateway.generate_structured(messages, CandidateAnalysis)
    return {"analysis": analysis}

def decide_next_action(state: InterviewState) -> InterviewState:
    if not state.get("latest_user_message"):
        return {"current_stage": InterviewStage.APPROACH, "next_action": InterviewAction.PROBE_APPROACH}

    analysis = state["analysis"]
    current_stage = state["current_stage"]
    next_stage = current_stage
    action = InterviewAction.ACKNOWLEDGE
    hints_used = state.get("hints_used", 0)
    mistakes = state.get("mistakes", 0)
    state_metadata = state.get("state_metadata", {})
    if "hint_history" not in state_metadata:
        state_metadata["hint_history"] = []
    if "mistake_history" not in state_metadata:
        state_metadata["mistake_history"] = []

    # Mistake tracking
    is_mistake = False
    if analysis.correctness == "incorrect" or analysis.approach_quality == "incorrect" or analysis.complexity_quality == "incorrect":
        is_mistake = True
    elif current_stage in [InterviewStage.CODING, InterviewStage.DEBUGGING] and "FAILED" in state["latest_user_message"]:
        is_mistake = True
        
    if is_mistake:
        mistakes += 1
        if analysis.detected_issue:
            state_metadata["mistake_history"].append({"stage": current_stage, "issue": analysis.detected_issue})

    # Termination safeguard
    if mistakes >= 5 or hints_used >= 5:
        return {"current_stage": InterviewStage.COMPLETED, "next_action": InterviewAction.END_INTERVIEW, "mistakes": mistakes}

    # Intercept clarifications & hints globally
    if analysis.intent == "clarification" or analysis.asks_clarification:
        return {"current_stage": current_stage, "next_action": InterviewAction.ANSWER_CLARIFICATION, "mistakes": mistakes, "state_metadata": state_metadata}
        
    if analysis.intent == "hint_request" or analysis.requests_hint:
        hints_used += 1
        # Calculate adaptive hint level
        level = 1
        if hints_used == 2: level = 2
        elif hints_used == 3: level = 3
        elif hints_used >= 4: level = 4
        
        state_metadata["hint_history"].append({"level": level, "stage": current_stage})
        # Persist level temporarily in state_metadata to be used by GENERATE
        state_metadata["current_hint_level"] = level
        return {"current_stage": current_stage, "next_action": InterviewAction.PROVIDE_HINT, "hints_used": hints_used, "mistakes": mistakes, "state_metadata": state_metadata}

    candidate_approach = state.get("candidate_approach")
    complexity = state.get("complexity")

    # Stage transitions
    if current_stage in [InterviewStage.QUESTION, InterviewStage.APPROACH]:
        if analysis.approach_quality == "strong":
            next_stage = InterviewStage.COMPLEXITY
            action = InterviewAction.ASK_COMPLEXITY
            candidate_approach = analysis.reasoning_summary
        elif analysis.approach_quality == "partially_correct":
            action = InterviewAction.PROBE_APPROACH
        else: # weak, incorrect
            action = InterviewAction.PROBE_APPROACH
            
    elif current_stage == InterviewStage.COMPLEXITY:
        if analysis.complexity_mentioned:
            state_metadata["complexity_analysis"] = {
                "claimed_time": analysis.claimed_time_complexity,
                "claimed_space": analysis.claimed_space_complexity,
                "correctness": analysis.complexity_correctness,
                "reasoning": analysis.complexity_reasoning
            }
            
        if analysis.complexity_quality in ["optimal", "acceptable"]:
            next_stage = InterviewStage.OPTIMIZATION
            action = InterviewAction.ASK_OPTIMIZATION
            complexity = analysis.reasoning_summary
        elif analysis.complexity_quality == "suboptimal":
            action = InterviewAction.PROBE_COMPLEXITY
        else: # incorrect
            action = InterviewAction.EXPLAIN_AND_RETRY
            
    elif current_stage == InterviewStage.OPTIMIZATION:
        if analysis.approach_quality == "strong":
            next_stage = InterviewStage.EDGE_CASES
            action = InterviewAction.ASK_EDGE_CASE
            candidate_approach = analysis.reasoning_summary # Update approach
        elif analysis.approach_quality in ["partially_correct", "weak"]:
            action = InterviewAction.PROBE_OPTIMIZATION
        else: # Assume they couldn't optimize
            if analysis.intent == "code" or analysis.coding_ready:
                next_stage = InterviewStage.EDGE_CASES
                action = InterviewAction.ASK_EDGE_CASE
            else:
                action = InterviewAction.PROBE_OPTIMIZATION
            
    elif current_stage == InterviewStage.EDGE_CASES:
        if analysis.edge_case_mentioned:
            next_stage = InterviewStage.CODING
            action = InterviewAction.REQUEST_CODE
        else:
            action = InterviewAction.PROBE_EDGE_CASE
            
    elif current_stage == InterviewStage.CODING:
        if (analysis.code_quality == "good" and analysis.correctness == "correct") or "PASSED" in state["latest_user_message"]:
            next_stage = InterviewStage.FOLLOW_UP
            action = InterviewAction.ASK_FOLLOW_UP
        elif analysis.correctness == "incorrect" or "FAILED" in state["latest_user_message"] or analysis.code_quality == "problematic":
            next_stage = InterviewStage.DEBUGGING
            action = InterviewAction.REQUEST_DEBUGGING
        else: # incomplete/unclear
            action = InterviewAction.REQUEST_CODE
            
    elif current_stage == InterviewStage.DEBUGGING:
        if analysis.correctness == "correct" or "PASSED" in state["latest_user_message"]:
            next_stage = InterviewStage.FOLLOW_UP
            action = InterviewAction.ASK_FOLLOW_UP
        else:
            action = InterviewAction.REQUEST_DEBUGGING
            
    elif current_stage == InterviewStage.FOLLOW_UP:
        if analysis.answers_current_question:
            next_stage = InterviewStage.COMPLETED
            action = InterviewAction.END_INTERVIEW
        else:
            action = InterviewAction.ASK_FOLLOW_UP

    return {
        "current_stage": next_stage,
        "next_action": action,
        "candidate_approach": candidate_approach,
        "complexity": complexity,
        "hints_used": hints_used,
        "mistakes": mistakes,
        "state_metadata": state_metadata
    }

def generate_response(state: InterviewState) -> InterviewState:
    action = state["next_action"]
    stage = state["current_stage"]
    analysis = state.get("analysis")
    state_metadata = state.get("state_metadata", {})
    
    system_prompt = f"""
    You are an expert technical interviewer conducting a mock interview for a {state['target_role']} position.
    
    Current Interview Stage: {stage}
    Your required action to execute: {action}
    """
    
    if analysis and analysis.detected_issue:
        system_prompt += f"\nDetected candidate issue/weakness: {analysis.detected_issue}"
        
    system_prompt += """
    
    CRITICAL INSTRUCTIONS:
    1. Do NOT reveal the full solution.
    2. Keep responses brief, realistic, and rigorous.
    3. Do NOT use generic AI praise like 'Great answer!' or 'Excellent!' unless it's genuinely an exceptional response. Challenge weak reasoning.
    """
    
    if action == InterviewAction.PROVIDE_HINT:
        level = state_metadata.get("current_hint_level", 1)
        system_prompt += f"\n4. You must provide a LEVEL {level} hint."
        if level == 1:
            system_prompt += " (Level 1: Gentle conceptual direction. Do not name specific data structures.)"
        elif level == 2:
            system_prompt += " (Level 2: Suggest the relevant data structure or algorithmic technique.)"
        elif level == 3:
            system_prompt += " (Level 3: Provide a strong structural hint or key algorithmic observation.)"
        elif level == 4:
            system_prompt += " (Level 4: Very strong guidance on how to solve it, but stop short of dictating the exact code.)"
            
    if action == InterviewAction.REQUEST_CODE:
        system_prompt += "\nAsk the candidate to implement their agreed-upon approach."
        
    if state.get("dsa_problem"):
        system_prompt += f"\n\nProblem context: {state['dsa_problem'].get('title')} - Optimal: {state['dsa_problem'].get('optimal_time_complexity')}"
        
    messages = [{"role": "system", "content": system_prompt}]
    for msg in state["messages"][-6:]:
        messages.append(msg)
        
    response = ai_gateway.generate_chat(messages)
    return {"interviewer_response": response}

def build_interviewer_graph() -> StateGraph:
    workflow = StateGraph(InterviewState)
    
    workflow.add_node("observe", observe_candidate)
    workflow.add_node("decide", decide_next_action)
    workflow.add_node("generate", generate_response)
    
    workflow.set_entry_point("observe")
    workflow.add_edge("observe", "decide")
    workflow.add_edge("decide", "generate")
    workflow.add_edge("generate", END)
    
    return workflow.compile()

interviewer_app = build_interviewer_graph()
