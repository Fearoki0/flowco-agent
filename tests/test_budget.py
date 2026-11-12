"""
test_budget.py - Offline unit tests for FlowCo v5.0 BudgetManager
"""
import os
import sys
import unittest
from pathlib import Path

# Add work directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import flowco


class TestBudgetManager(unittest.TestCase):
    def setUp(self):
        self.bm = flowco.BudgetManager()
        flowco.BUDGET = self.bm

    def test_task_vs_session_usage(self):
        """Verify task usage resets per task while session usage accumulates."""
        self.bm.start_task("task_1", budget=10000)
        self.assertEqual(self.bm.total_task_tokens(), 0)
        self.assertEqual(self.bm.total_session_tokens(), 0)

        # Record task 1 usage
        self.bm.record_request_start(caller="main")
        self.bm.record_success(
            {"prompt_tokens": 100, "completion_tokens": 50},
            in_chars=400,
            out_chars=200,
            caller="main",
            provider="test_prov"
        )
        self.assertEqual(self.bm.total_task_tokens(), 150)
        self.assertEqual(self.bm.total_session_tokens(), 150)

        # Start task 2
        self.bm.start_task("task_2", budget=5000)
        self.assertEqual(self.bm.total_task_tokens(), 0)
        self.assertEqual(self.bm.total_session_tokens(), 150)

        # Record task 2 usage
        self.bm.record_request_start(caller="main")
        self.bm.record_success(
            {"prompt_tokens": 80, "completion_tokens": 20},
            in_chars=320,
            out_chars=80,
            caller="main",
            provider="test_prov"
        )
        self.assertEqual(self.bm.total_task_tokens(), 100)
        self.assertEqual(self.bm.total_session_tokens(), 250)

    def test_subagent_budget_sharing(self):
        """Verify subagent calls consume task budget and are tracked separately."""
        self.bm.start_task("task_sub", budget=500)
        self.bm.record_request_start(caller="subagent")
        self.bm.record_success(
            {"prompt_tokens": 200, "completion_tokens": 100},
            caller="subagent",
            provider="test_prov"
        )
        self.assertEqual(self.bm.task_usage["subagent_tokens"], 300)
        self.assertEqual(self.bm.total_task_tokens(), 300)
        self.assertEqual(self.bm.remaining_task_budget(), 200)

        # Request exceeding remaining allowance must be rejected
        allowed, reason = self.bm.check_pre_request(estimated_tokens=250, is_subagent=True)
        self.assertFalse(allowed)
        self.assertIn("Task token budget exceeded", reason)

    def test_budget_extension(self):
        """Verify /budget add increases task allowance and clears paused state."""
        self.bm.start_task("task_paused", budget=100)
        self.bm.record_request_start()
        self.bm.record_success({"prompt_tokens": 80, "completion_tokens": 30})
        self.bm.task_usage["paused"] = True

        # Extend budget by 500 tokens
        new_budget = self.bm.add_budget(500)
        self.assertEqual(new_budget, 600)
        self.assertFalse(self.bm.task_usage["paused"])
        self.assertGreater(self.bm.remaining_task_budget(), 0)

    def test_usage_normalization(self):
        """Verify normalization across different provider schemas."""
        # Standard OpenAI schema
        pt, ct, cached, is_est = flowco.normalize_usage({"prompt_tokens": 50, "completion_tokens": 25})
        self.assertEqual((pt, ct, cached, is_est), (50, 25, 0, False))

        # Anthropic / OpenRouter with prompt_tokens_details
        pt, ct, cached, is_est = flowco.normalize_usage({
            "input_tokens": 100,
            "output_tokens": 40,
            "prompt_tokens_details": {"cached_tokens": 30}
        })
        self.assertEqual((pt, ct, cached, is_est), (100, 40, 30, False))

        # Missing usage (estimated fallback)
        pt, ct, cached, is_est = flowco.normalize_usage(None, in_chars=400, out_chars=200)
        self.assertEqual((pt, ct, cached, is_est), (100, 50, 0, True))


if __name__ == "__main__":
    unittest.main()
