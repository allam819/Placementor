from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from app.ai.gateway import ai_gateway

class StructuredJD(BaseModel):
    title: Optional[str] = "Unknown Role"
    company: Optional[str] = "Unknown Company"
    hard_requirements: List[str] = []
    soft_skills: List[str] = []
    tools_and_tech: List[str] = []

class EvidenceMapping(BaseModel):
    requirement: str
    evidence: str
    status: str # 'Strong Match', 'Partial Match', 'Mentioned but weak evidence', 'Not demonstrated', 'Missing'

class ExtractedResumeEvidence(BaseModel):
    evidence_mapping: List[EvidenceMapping] = []
    gaps: List[str] = []
    recommendations: List[str] = []

class PreparationRecommendation(BaseModel):
    topic: str
    gap_type: str # MISSING_SKILL, MISSING_EVIDENCE
    severity: str # HIGH, MEDIUM, LOW
    reason: str
    recommendation_type: str # LEARN_NEW, REVISE_EXISTING, STRENGTHEN_EVIDENCE
    related_learning_ids: List[str] = []

class AnalysisResult(BaseModel):
    overall_score: int = 0
    gaps: List[str] = []
    recommendations: List[str] = []
    category_scores: Dict[str, int] = {}
    preparation_recommendations: List[PreparationRecommendation] = []

def structure_job_description(raw_jd: str) -> StructuredJD:
    system_prompt = """
    You are an expert technical recruiter. Extract the following from the raw job description:
    - title
    - company
    - hard_requirements (list of strings)
    - soft_skills (list of strings)
    - tools_and_tech (list of strings)
    
    Return a strictly formatted JSON object matching those keys.
    """
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": raw_jd}
    ]
    
    return ai_gateway.generate_structured(messages, StructuredJD)

def extract_resume_evidence(parsed_resume: str, structured_jd: StructuredJD) -> ExtractedResumeEvidence:
    system_prompt = """
    You are an expert technical resume reviewer. Compare the candidate's resume against the structured job description.
    
    For every requirement in the job description (hard_requirements, tools_and_tech), map it to evidence found in the resume.
    
    Output a JSON object with:
    - evidence_mapping: A list of objects with 'requirement', 'evidence' (exact quote or summary from resume), and 'status' ('Strong Match', 'Partial Match', 'Not demonstrated', 'Missing').
    - gaps: a list of strings detailing required skills missing from the resume. Differentiate between missing skill vs missing evidence.
    - recommendations: actionable advice to rewrite specific bullet points. Do not invent metrics or achievements.
    
    DO NOT generate an overall score. Only extract the evidence.
    """
    
    user_prompt = f"""
    Job Description:
    {structured_jd.model_dump_json()}
    
    Resume:
    {parsed_resume}
    """
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    return ai_gateway.generate_structured(messages, ExtractedResumeEvidence)

def calculate_deterministic_score(evidence: ExtractedResumeEvidence) -> AnalysisResult:
    """
    Calculates the resume match score deterministically based on structured evidence.
    """
    if not evidence.evidence_mapping:
        return AnalysisResult(overall_score=0, gaps=evidence.gaps, recommendations=evidence.recommendations)

    total_reqs = len(evidence.evidence_mapping)
    score_sum = 0
    
    status_weights = {
        'Strong Match': 1.0,
        'Partial Match': 0.5,
        'Mentioned but weak evidence': 0.3,
        'Not demonstrated': 0.0,
        'Missing': 0.0
    }
    
    prep_recs = []
    for mapping in evidence.evidence_mapping:
        score_sum += status_weights.get(mapping.status, 0.0)
        
        # Build preparation recommendations
        if mapping.status == 'Missing':
            prep_recs.append(PreparationRecommendation(
                topic=mapping.requirement,
                gap_type="MISSING_SKILL",
                severity="HIGH",
                reason=f"Required skill '{mapping.requirement}' is completely missing.",
                recommendation_type="LEARN_NEW", # Placeholder, updated in semantic pass
                related_learning_ids=[]
            ))
        elif mapping.status in ['Not demonstrated', 'Mentioned but weak evidence']:
            prep_recs.append(PreparationRecommendation(
                topic=mapping.requirement,
                gap_type="MISSING_EVIDENCE",
                severity="MEDIUM" if mapping.status == 'Not demonstrated' else "LOW",
                reason=f"Skill '{mapping.requirement}' lacks strong project/experience evidence.",
                recommendation_type="STRENGTHEN_EVIDENCE",
                related_learning_ids=[]
            ))
            
    base_score = int((score_sum / total_reqs) * 100)
    
    # We map this to the PRD categories roughly for now
    # Technical Skills 25%, Experience Relevance 20%, Project Relevance 20%, Fundamentals 15%, Responsibilities 10%, Keyword Alignment 10%
    # Since the MVP extracts a flat list of evidence, we apply the base_score across all categories to fulfill the MVP requirement.
    
    category_scores = {
        "Technical Skills": base_score,
        "Experience Relevance": base_score,
        "Project Relevance": base_score,
        "Fundamentals": base_score,
        "Responsibilities": base_score,
        "Keyword Alignment": base_score
    }
    
    return AnalysisResult(
        overall_score=base_score,
        category_scores=category_scores,
        gaps=evidence.gaps,
        recommendations=evidence.recommendations,
        preparation_recommendations=prep_recs
    )

def analyze_resume(parsed_resume: str, structured_jd: StructuredJD) -> AnalysisResult:
    evidence = extract_resume_evidence(parsed_resume, structured_jd)
    return calculate_deterministic_score(evidence)
