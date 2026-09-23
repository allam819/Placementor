import pytest
import sys
from unittest.mock import patch, MagicMock

# Mock sentence_transformers before anything else imports it
sys.modules["sentence_transformers"] = MagicMock()

from fastapi.testclient import TestClient
from main import app
from app.api.auth import verify_user

client = TestClient(app)

def mock_verify_user():
    return MagicMock(user=MagicMock(id="user_123"))

app.dependency_overrides[verify_user] = mock_verify_user

@patch("app.api.resume.get_supabase_client")
@patch("app.api.resume.analyze_resume")
@patch("app.api.resume.structure_job_description")
@patch("app.ai.embeddings.generate_embedding")
def test_resume_missing_skill_learn_new(mock_generate_embedding, mock_structure, mock_analyze, mock_get_supabase):
    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase
    
    def table_side_effect(name):
        mock_tbl = MagicMock()
        if name == "resumes":
            mock_tbl.select().eq().eq().execute.return_value = MagicMock(data=[{"parsed_content": "Resume"}])
        elif name == "job_descriptions":
            mock_tbl.insert().execute.return_value = MagicMock(data=[{"id": "jd_123"}])
        elif name == "resume_analyses":
            def mock_insert(data):
                return MagicMock(execute=lambda: MagicMock(data=[data]))
            mock_tbl.insert = mock_insert
        return mock_tbl
        
    mock_supabase.table.side_effect = table_side_effect
    
    mock_structure.return_value = MagicMock(model_dump=lambda: {})
    
    analysis_mock = MagicMock()
    analysis_mock.overall_score = 50
    analysis_mock.gaps = []
    analysis_mock.recommendations = []
    
    from app.ai.resume_analyzer import PreparationRecommendation
    analysis_mock.preparation_recommendations = [
        PreparationRecommendation(
            topic="Docker",
            gap_type="MISSING_SKILL",
            severity="HIGH",
            reason="Required but missing",
            recommendation_type="LEARN_NEW"
        )
    ]
    mock_analyze.return_value = analysis_mock
    
    mock_generate_embedding.return_value = [0.1, 0.2]
    
    mock_rpc_res = MagicMock()
    mock_rpc_res.data = []
    mock_supabase.rpc.return_value.execute.return_value = mock_rpc_res
    
    res = client.post("/api/resume/analyze", json={
        "resume_id": "res_123",
        "job_description_raw": "We need Docker"
    })
    
    assert res.status_code == 200
    data = res.json()
    
    prep_recs = data["analysis"]["preparation_recommendations"]
    assert len(prep_recs) == 1
    assert prep_recs[0]["topic"] == "Docker"
    assert prep_recs[0]["recommendation_type"] == "LEARN_NEW"

@patch("app.api.resume.get_supabase_client")
@patch("app.api.resume.analyze_resume")
@patch("app.api.resume.structure_job_description")
@patch("app.ai.embeddings.generate_embedding")
def test_resume_missing_skill_revise_existing(mock_generate_embedding, mock_structure, mock_analyze, mock_get_supabase):
    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase
    
    def table_side_effect(name):
        mock_tbl = MagicMock()
        if name == "resumes":
            mock_tbl.select().eq().eq().execute.return_value = MagicMock(data=[{"parsed_content": "Resume"}])
        elif name == "job_descriptions":
            mock_tbl.insert().execute.return_value = MagicMock(data=[{"id": "jd_123"}])
        elif name == "resume_analyses":
            def mock_insert(data):
                return MagicMock(execute=lambda: MagicMock(data=[data]))
            mock_tbl.insert = mock_insert
        return mock_tbl
        
    mock_supabase.table.side_effect = table_side_effect
    
    mock_structure.return_value = MagicMock(model_dump=lambda: {})
    
    analysis_mock = MagicMock()
    analysis_mock.overall_score = 50
    analysis_mock.gaps = []
    analysis_mock.recommendations = []
    
    from app.ai.resume_analyzer import PreparationRecommendation
    analysis_mock.preparation_recommendations = [
        PreparationRecommendation(
            topic="Docker",
            gap_type="MISSING_SKILL",
            severity="HIGH",
            reason="Required but missing",
            recommendation_type="LEARN_NEW"
        )
    ]
    mock_analyze.return_value = analysis_mock
    
    mock_generate_embedding.return_value = [0.1, 0.2]
    
    mock_rpc_res = MagicMock()
    mock_rpc_res.data = [{"id": "learn_2", "similarity": 0.9}]
    mock_supabase.rpc.return_value.execute.return_value = mock_rpc_res
    
    res = client.post("/api/resume/analyze", json={
        "resume_id": "res_123",
        "job_description_raw": "We need Docker"
    })
    
    assert res.status_code == 200
    data = res.json()
    
    prep_recs = data["analysis"]["preparation_recommendations"]
    assert len(prep_recs) == 1
    assert prep_recs[0]["recommendation_type"] == "REVISE_EXISTING"
    assert "learn_2" in prep_recs[0]["related_learning_ids"]

@patch("app.api.resume.get_supabase_client")
@patch("app.api.resume.analyze_resume")
@patch("app.api.resume.structure_job_description")
def test_resume_missing_evidence(mock_structure, mock_analyze, mock_get_supabase):
    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase
    
    def table_side_effect(name):
        mock_tbl = MagicMock()
        if name == "resumes":
            mock_tbl.select().eq().eq().execute.return_value = MagicMock(data=[{"parsed_content": "Resume"}])
        elif name == "job_descriptions":
            mock_tbl.insert().execute.return_value = MagicMock(data=[{"id": "jd_123"}])
        elif name == "resume_analyses":
            def mock_insert(data):
                return MagicMock(execute=lambda: MagicMock(data=[data]))
            mock_tbl.insert = mock_insert
        return mock_tbl
        
    mock_supabase.table.side_effect = table_side_effect
    
    mock_structure.return_value = MagicMock(model_dump=lambda: {})
    
    analysis_mock = MagicMock()
    analysis_mock.overall_score = 50
    analysis_mock.gaps = []
    analysis_mock.recommendations = []
    
    from app.ai.resume_analyzer import PreparationRecommendation
    analysis_mock.preparation_recommendations = [
        PreparationRecommendation(
            topic="Python",
            gap_type="MISSING_EVIDENCE",
            severity="MEDIUM",
            reason="Not demonstrated well",
            recommendation_type="STRENGTHEN_EVIDENCE"
        )
    ]
    mock_analyze.return_value = analysis_mock
    
    res = client.post("/api/resume/analyze", json={
        "resume_id": "res_123",
        "job_description_raw": "We need Python"
    })
    
    assert res.status_code == 200
    data = res.json()
    
    prep_recs = data["analysis"]["preparation_recommendations"]
    assert len(prep_recs) == 1
    assert prep_recs[0]["recommendation_type"] == "STRENGTHEN_EVIDENCE"
