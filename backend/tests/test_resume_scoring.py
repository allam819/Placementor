import pytest
from app.ai.resume_analyzer import calculate_deterministic_score, ExtractedResumeEvidence, EvidenceMapping

def test_resume_scoring():
    evidence = ExtractedResumeEvidence(
        evidence_mapping=[
            EvidenceMapping(requirement="Python", evidence="Used Python", status="Strong Match"),
            EvidenceMapping(requirement="Java", evidence="", status="Missing"),
            EvidenceMapping(requirement="React", evidence="Familiar with React", status="Partial Match"),
            EvidenceMapping(requirement="Docker", evidence="Saw Docker", status="Mentioned but weak evidence"),
            EvidenceMapping(requirement="SQL", evidence="", status="Not demonstrated")
        ],
        gaps=["Java", "SQL"],
        recommendations=[]
    )
    
    result = calculate_deterministic_score(evidence)
    
    # Calculation:
    # 5 requirements.
    # Scores: 1.0 + 0.0 + 0.5 + 0.3 + 0.0 = 1.8
    # Base score: (1.8 / 5) * 100 = 36%
    
    assert result.overall_score == 36
    assert result.category_scores["Technical Skills"] == 36
    assert "Java" in result.gaps

def test_empty_resume_scoring():
    evidence = ExtractedResumeEvidence(
        evidence_mapping=[],
        gaps=[],
        recommendations=[]
    )
    result = calculate_deterministic_score(evidence)
    assert result.overall_score == 0
