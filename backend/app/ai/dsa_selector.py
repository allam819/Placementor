import logging
from typing import Dict, Any
from supabase import Client

logger = logging.getLogger(__name__)

class DSASelector:
    def __init__(self, supabase: Client, user_id: str):
        self.supabase = supabase
        self.user_id = user_id
        
    def get_candidate_signals(self) -> Dict[str, Any]:
        signals = {
            "weaknesses": {},
            "resume_gaps": [],
            "recent_problems": [],
            "learning": [],
            "difficulty_level": "Medium"
        }
        
        # 1. Fetch past interviews for weaknesses and recent problems
        try:
            interviews_res = self.supabase.table("interview_sessions").select(
                "id, problem_id, evaluation_data, status, created_at, state_metadata"
            ).eq("user_id", self.user_id).order("created_at", desc=True).execute()
        except Exception as e:
            # Fallback if evaluation_data column is missing
            interviews_res = self.supabase.table("interview_sessions").select(
                "id, problem_id, status, created_at, state_metadata"
            ).eq("user_id", self.user_id).order("created_at", desc=True).execute()
            
        interviews = interviews_res.data or []
        
        weaknesses_count = {}
        recent_problems = set()
        
        for idx, iv in enumerate(interviews):
            pid = iv.get("problem_id")
            if pid:
                recent_problems.add(pid)
                
            if iv.get("status") == "completed":
                eval_data = iv.get("evaluation_data")
                if not eval_data and iv.get("state_metadata"):
                    eval_data = iv.get("state_metadata", {}).get("evaluation_data")
                eval_data = eval_data or {}
                
                # Extract weaknesses
                weaknesses = eval_data.get("weaknesses", [])
                for w in weaknesses:
                    topic = w.get("topic", "").lower().strip()
                    if topic:
                        weaknesses_count[topic] = weaknesses_count.get(topic, 0) + 1
        
        signals["weaknesses"] = weaknesses_count
        signals["recent_problems"] = list(recent_problems)
        
        # Determine difficulty based on performance.
        # Simple heuristic: average score of last 3 interviews.
        recent_evals = []
        for iv in interviews:
            if iv.get("status") == "completed":
                ed = iv.get("evaluation_data") or (iv.get("state_metadata") or {}).get("evaluation_data") or {}
                sc = ed.get("overall_score")
                if sc is not None:
                    recent_evals.append(sc)
            if len(recent_evals) == 3:
                break
                
        if recent_evals:
            avg_score = sum(recent_evals) / len(recent_evals)
            if avg_score >= 80:
                signals["difficulty_level"] = "Hard"
            elif avg_score >= 50:
                signals["difficulty_level"] = "Medium"
            else:
                signals["difficulty_level"] = "Easy"
        else:
            signals["difficulty_level"] = "Medium" # Default cold start
            
        # 2. Fetch Resume Gaps
        try:
            resume_res = self.supabase.table("resume_analyses").select(
                "gaps, preparation_recommendations"
            ).eq("user_id", self.user_id).order("created_at", desc=True).limit(1).execute()
        except Exception:
            try:
                # Fallback if preparation_recommendations doesn't exist
                resume_res = self.supabase.table("resume_analyses").select(
                    "gaps"
                ).eq("user_id", self.user_id).order("created_at", desc=True).limit(1).execute()
            except Exception:
                resume_res = type('obj', (object,), {'data': []})
            
        if hasattr(resume_res, 'data') and resume_res.data:
            r = resume_res.data[0]
            prep_recs = r.get("preparation_recommendations") or []
            signals["resume_gaps"] = [p.get("topic", "").lower().strip() for p in prep_recs]
            # Fallback to general gaps string
            gaps = r.get("gaps") or []
            for g in gaps:
                if isinstance(g, str):
                    signals["resume_gaps"].append(g.lower().strip())
            
        # 3. Fetch Learning Recommendations
        try:
            learning_res = self.supabase.table("learning_activities").select("topic").eq("user_id", self.user_id).execute()
            signals["learning"] = [l.get("topic", "").lower().strip() for l in learning_res.data or []]
        except Exception:
            pass
            
        return signals

    def recommend_problem(self, available_problems=None) -> Dict[str, Any]:
        signals = self.get_candidate_signals()
        
        # Fetch available problems
        if available_problems is None:
            probs_res = self.supabase.table("dsa_problems").select("*").execute()
            problems = probs_res.data or []
        else:
            problems = available_problems
        
        if not problems:
            return None
            
        scored_problems = []
        for p in problems:
            score = 0
            reasons = []
            
            p_id = p.get("id")
            title = (p.get("title") or "").lower()
            desc = (p.get("description") or "").lower()
            diff = (p.get("difficulty") or "Medium").lower()
            
            # Simple keyword matching to approximate topics from title/description
            matched_topics = set()
            for topic, count in signals["weaknesses"].items():
                if len(topic) > 3 and (topic in title or topic in desc):
                    score += min(count, 3) * 3
                    reasons.append(f"Recurring weakness: {topic.title()}")
                    matched_topics.add(topic)
                    
            for gap in signals["resume_gaps"]:
                if len(gap) > 3 and (gap in title or gap in desc):
                    score += 3
                    reasons.append(f"Resume preparation gap: {gap.title()}")
                    matched_topics.add(gap)
                    
            for l in signals["learning"]:
                if len(l) > 3 and (l in title or l in desc):
                    score += 1
                    reasons.append(f"Recent learning topic: {l.title()}")
                    matched_topics.add(l)
                    
            if diff == signals["difficulty_level"].lower():
                score += 1
                reasons.append(f"Appropriate difficulty: {signals['difficulty_level']}")
                
            if p_id in signals["recent_problems"]:
                score -= 5
                reasons.append("Recently attempted penalty")
                
            scored_problems.append({
                "problem": p,
                "score": score,
                "reasons": list(set(reasons))
            })
            
        # Sort by score descending
        scored_problems.sort(key=lambda x: x["score"], reverse=True)
        
        best = scored_problems[0]
        
        if not best["reasons"]:
            best["reasons"] = ["General available problem (Cold start)"]
            
        return {
            "problem": best["problem"],
            "score": best["score"],
            "reasons": best["reasons"]
        }
