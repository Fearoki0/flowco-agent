"""
test_api.py - Offline unit tests for FlowCo v5.0 API layer, SSE parser, and mock engine
"""
import os
import sys
import unittest
from pathlib import Path

# Add work directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import flowco


class TestApiLayer(unittest.TestCase):
    def test_mock_test_mode(self):
        """Verify FLOWCO_TEST_MODE simulates model responses without network calls."""
        os.environ["FLOWCO_TEST_MODE"] = "1"
        try:
            flowco.BUDGET.start_task("test_mock", budget=10000)
            res = flowco.chat_plain([{"role": "user", "content": "hello"}])
            self.assertIn("choices", res)
            msg = res["choices"][0]["message"]
            self.assertIn("content", msg)
            self.assertGreater(flowco.BUDGET.total_task_tokens(), 0)
        finally:
            os.environ.pop("FLOWCO_TEST_MODE", None)

    def test_pricing_calculation(self):
        """Verify cost calculation with configured provider rates."""
        rates = {"price_in_per_m": 2.0, "price_out_per_m": 8.0, "price_cache_read_per_m": 0.5}
        cost = flowco.calculate_cost(prompt_tokens=1_000_000, completion_tokens=500_000, cached_tokens=200_000, rates=rates)
        # 800k uncached * $2.0/M ($1.60) + 500k output * $8.0/M ($4.00) + 200k cached * $0.5/M ($0.10) = $5.70
        self.assertAlmostEqual(cost, 5.70, places=2)


if __name__ == "__main__":
    unittest.main()
