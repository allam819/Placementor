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

@patch("app.api.interviews.get_supabase_client")
@patch("app.ai.evaluation.calculate_dsa_evaluation")
@patch("app.ai.embeddings.generate_embedding")
def test_evaluate_with_learning_matches(mock_generate_embedding, mock_calc, mock_get_supabase):
    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase
    
    mock_session_res = MagicMock()
    mock_session_res.data = [{"id": "123", "user_id": "user_123", "evaluation_data": None}]
    mock_supabase.table().select().eq().eq().execute.return_value = mock_session_res
    
    mock_history_res = MagicMock()
    mock_history_res.data = []
    mock_supabase.table().select().eq().order().execute.return_value = mock_history_res
    
    eval_mock = MagicMock()
    eval_mock.weaknesses = [{"topic": "Hash Maps", "issue": "Syntax", "severity": "low"}]
    eval_mock.overall_score = 90
    eval_mock.model_dump.return_value = {"weaknesses": eval_mock.weaknesses, "overall_score": 90}
    mock_calc.return_value = eval_mock
    
    mock_generate_embedding.return_value = [0.1, 0.2]
    
    mock_rpc_res = MagicMock()
    mock_rpc_res.data = [{"id": "learn_1", "similarity": 0.8}]
    mock_supabase.rpc.return_value.execute.return_value = mock_rpc_res
    
    res = client.post("/api/interviews/evaluate", json={"session_id": "123"})
    assert res.status_code == 200
    
    data = res.json()
    recs = data.get("learning_recommendations")
    assert recs
    assert len(recs) == 1
    assert recs[0]["recommendation_type"] == "REVISE_EXISTING"
    assert "learn_1" in recs[0]["related_learning_ids"]

@patch("app.api.interviews.get_supabase_client")
@patch("app.ai.evaluation.calculate_dsa_evaluation")
@patch("app.ai.embeddings.generate_embedding")
def test_evaluate_without_learning_matches(mock_generate_embedding, mock_calc, mock_get_supabase):
    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase
    
    mock_session_res = MagicMock()
    mock_session_res.data = [{"id": "123", "user_id": "user_123", "evaluation_data": None}]
    mock_supabase.table().select().eq().eq().execute.return_value = mock_session_res
    
    mock_history_res = MagicMock()
    mock_history_res.data = []
    mock_supabase.table().select().eq().order().execute.return_value = mock_history_res
    
    eval_mock = MagicMock()
    eval_mock.weaknesses = [{"topic": "Graphs", "issue": "DFS", "severity": "high"}]
    eval_mock.overall_score = 60
    eval_mock.model_dump.return_value = {"weaknesses": eval_mock.weaknesses, "overall_score": 60}
    mock_calc.return_value = eval_mock
    
    mock_generate_embedding.return_value = [0.1, 0.2]
    
    mock_rpc_res = MagicMock()
    mock_rpc_res.data = []
    mock_supabase.rpc.return_value.execute.return_value = mock_rpc_res
    
    res = client.post("/api/interviews/evaluate", json={"session_id": "123"})
    assert res.status_code == 200
    
    data = res.json()
    recs = data.get("learning_recommendations")
    assert recs
    assert len(recs) == 1
    assert recs[0]["recommendation_type"] == "LEARN_NEW"
    assert len(recs[0]["related_learning_ids"]) == 0

@patch("app.api.interviews.get_supabase_client")
def test_idempotent_evaluation_refresh(mock_get_supabase):
    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase
    
    mock_session_res = MagicMock()
    mock_session_res.data = [{"id": "123", "user_id": "user_123", "evaluation_data": {"existing": True, "learning_recommendations": []}}]
    mock_supabase.table().select().eq().eq().execute.return_value = mock_session_res
    
    res = client.post("/api/interviews/evaluate", json={"session_id": "123"})
    assert res.status_code == 200
    assert res.json().get("existing") == True
