import unittest
from typing import Dict, Any
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ai.dsa_selector import DSASelector

class MockSupabase:
    pass

class TestableDSASelector(DSASelector):
    def __init__(self, signals: Dict[str, Any]):
        super().__init__(MockSupabase(), "mock_user")
        self._mock_signals = signals
        
    def get_candidate_signals(self) -> Dict[str, Any]:
        return self._mock_signals


class TestDSASelector(unittest.TestCase):
    def setUp(self):
        self.mock_problems = [
            {
                "id": "p1",
                "title": "Two Sum",
                "description": "Given an array of integers, return indices using a hash map.",
                "difficulty": "Easy"
            },
            {
                "id": "p2",
                "title": "Longest Substring Without Repeating Characters",
                "description": "Use sliding window and a hash map to find the longest substring.",
                "difficulty": "Medium"
            },
            {
                "id": "p3",
                "title": "Edit Distance",
                "description": "Use dynamic programming to find the minimum number of operations.",
                "difficulty": "Hard"
            },
            {
                "id": "p4",
                "title": "Binary Tree Level Order Traversal",
                "description": "Use bfs on a binary tree.",
                "difficulty": "Medium"
            }
        ]

    def test_cold_start(self):
        # No history, should pick a Medium problem (default difficulty)
        signals = {
            "weaknesses": {},
            "resume_gaps": [],
            "recent_problems": [],
            "learning": [],
            "difficulty_level": "Medium"
        }
        selector = TestableDSASelector(signals)
        rec = selector.recommend_problem(self.mock_problems)
        
        self.assertIsNotNone(rec)
        self.assertEqual(rec["problem"]["difficulty"], "Medium")
        self.assertTrue(any("Appropriate difficulty" in r for r in rec["reasons"]))

    def test_recurring_weakness(self):
        # Hash map weakness repeated 2 times
        signals = {
            "weaknesses": {"hash map": 2},
            "resume_gaps": [],
            "recent_problems": [],
            "learning": [],
            "difficulty_level": "Medium"
        }
        selector = TestableDSASelector(signals)
        rec = selector.recommend_problem(self.mock_problems)
        
        self.assertIsNotNone(rec)
        self.assertEqual(rec["problem"]["id"], "p2") # p2 is Medium and has "hash map"
        self.assertTrue(any("Recurring weakness" in r for r in rec["reasons"]))

    def test_resume_gap(self):
        # DP gap
        signals = {
            "weaknesses": {},
            "resume_gaps": ["dynamic programming"],
            "recent_problems": [],
            "learning": [],
            "difficulty_level": "Hard"
        }
        selector = TestableDSASelector(signals)
        rec = selector.recommend_problem(self.mock_problems)
        
        self.assertIsNotNone(rec)
        self.assertEqual(rec["problem"]["id"], "p3") # Edit Distance
        self.assertTrue(any("Resume preparation gap" in r for r in rec["reasons"]))

    def test_difficulty_match(self):
        # Strong performance -> Hard
        signals = {
            "weaknesses": {},
            "resume_gaps": [],
            "recent_problems": [],
            "learning": [],
            "difficulty_level": "Hard"
        }
        selector = TestableDSASelector(signals)
        rec = selector.recommend_problem(self.mock_problems)
        
        self.assertEqual(rec["problem"]["difficulty"], "Hard")
        self.assertEqual(rec["problem"]["id"], "p3")

    def test_recent_attempt_penalty(self):
        # Recently attempted p2, should pick p4
        signals = {
            "weaknesses": {},
            "resume_gaps": [],
            "recent_problems": ["p2"],
            "learning": [],
            "difficulty_level": "Medium"
        }
        selector = TestableDSASelector(signals)
        rec = selector.recommend_problem(self.mock_problems)
        
        self.assertEqual(rec["problem"]["id"], "p4")

    def test_multiple_signals(self):
        # Weakness in DP, gap in hash map. DP is weighted higher for recurring.
        signals = {
            "weaknesses": {"dynamic programming": 3},
            "resume_gaps": ["hash map"],
            "recent_problems": [],
            "learning": [],
            "difficulty_level": "Medium"
        }
        selector = TestableDSASelector(signals)
        rec = selector.recommend_problem(self.mock_problems)
        
        # DP weakness (3 occurrences * 3 = 9 points) + difficulty match? p3 is Hard, p2 is Medium (hash map +3, diff +1 = 4).
        # p3 should win.
        self.assertEqual(rec["problem"]["id"], "p3")

    def test_no_matching_problem(self):
        signals = {
            "weaknesses": {"advanced segment trees": 1},
            "resume_gaps": [],
            "recent_problems": [],
            "learning": [],
            "difficulty_level": "Medium"
        }
        selector = TestableDSASelector(signals)
        rec = selector.recommend_problem(self.mock_problems)
        
        # Should gracefully fallback to an appropriate difficulty problem
        self.assertIsNotNone(rec)
        self.assertEqual(rec["problem"]["difficulty"], "Medium")

if __name__ == '__main__':
    unittest.main()
