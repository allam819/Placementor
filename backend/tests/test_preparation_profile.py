import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from app.api.auth import verify_user

client = TestClient(app)

def mock_verify_user():
    return MagicMock(user=MagicMock(id="user_123"))

app.dependency_overrides[verify_user] = mock_verify_user

@patch("app.api.profiles.get_supabase_client")
def test_empty_profile(mock_get_supabase):
    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase
    
    # Return empty for all queries
    mock_res = MagicMock()
    mock_res.data = []
    
    def side_effect(*args, **kwargs):
        return MagicMock(eq=lambda *a, **k: MagicMock(order=lambda *a, **k: MagicMock(limit=lambda *a, **k: MagicMock(execute=lambda: mock_res), execute=lambda: mock_res), execute=lambda: mock_res))

    mock_supabase.table.return_value.select.side_effect = side_effect
    
    res = client.get("/api/profiles/preparation")
    assert res.status_code == 200
    data = res.json()
    assert data["target_role"] is None
    assert data["resume"] is None
    assert data["learning"]["total_learning_activities"] == 0
    assert data["interview"]["total_completed_interviews"] == 0
    assert len(data["preparation"]["next_recommended_actions"]) == 0

@patch("app.api.profiles.get_supabase_client")
def test_resume_and_interview_unified_weakness(mock_get_supabase):
    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase
    
    def table_side_effect(name):
        mock_tbl = MagicMock()
        
        if name == "profiles" or name == "job_descriptions":
            res = MagicMock()
            res.data = [{"target_role": "Backend Engineer", "title": "Backend Engineer"}]
            mock_tbl.select.return_value.eq.return_value.execute.return_value = res
            mock_tbl.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = res
            return mock_tbl
            
        elif name == "resume_analyses":
            res = MagicMock()
            res.data = [{
                "id": "r1",
                "overall_score": 80,
                "gaps": ["PostgreSQL"],
                "preparation_recommendations": [
                    {"topic": "Docker", "gap_type": "MISSING_SKILL", "severity": "MEDIUM", "recommendation_type": "LEARN_NEW", "reason": "Missing"}
                ]
            }]
            mock_tbl.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = res
            return mock_tbl
            
        elif name == "learning_activities":
            res = MagicMock()
            res.data = [] # Empty learning
            mock_tbl.select.return_value.eq.return_value.order.return_value.execute.return_value = res
            return mock_tbl
            
        elif name == "interview_sessions":
            res = MagicMock()
            res.data = [{
                "id": "i1",
                "status": "completed",
                "evaluation_data": {
                    "overall_score": 7,
                    "weaknesses": [
                        {"topic": "Docker", "severity": "HIGH", "issue": "Bad debugging"}
                    ]
                }
            }]
            mock_tbl.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = res
            return mock_tbl
            
        return mock_tbl
        
    mock_supabase.table.side_effect = table_side_effect
    
    res = client.get("/api/profiles/preparation")
    assert res.status_code == 200
    data = res.json()
    
    # 1. Check basic mapping
    assert data["target_role"] == "Backend Engineer"
    assert data["resume"]["latest_resume_score"] == 80
    assert data["interview"]["total_completed_interviews"] == 1
    
    # 2. Check Unified Action
    actions = data["preparation"]["next_recommended_actions"]
    assert len(actions) == 1
    
    docker_action = actions[0]
    assert docker_action["topic"].lower() == "docker"
    assert docker_action["source"] == "MULTIPLE"
    assert docker_action["occurrences"] == 2
    assert docker_action["severity"] == "HIGH" # Elevated by interview
    assert docker_action["priority"] == "HIGH"
