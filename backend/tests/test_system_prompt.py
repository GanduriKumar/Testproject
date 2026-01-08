import unittest
from backend.system_prompt import build_system_prompt, DEFAULT_PARAMS


class TestSystemPrompt(unittest.TestCase):
    def test_build_contains_sections_and_params(self):
        sp = build_system_prompt(
            domain="Orders & Returns",
            behavior="Refund/Exchange/Cancellation",
            axes={"price_sensitivity": "high", "brand_bias": "none", "availability": "sold_out", "policy_boundary": "near_edge_allowed"},
            policy_text="- Return window: 30 days",
            facts_text="- Order was delivered 7 days ago; quantity 1.",
        )
        self.assertIn("Role:", sp.content)
        self.assertIn("Safety/Policy:", sp.content)
        self.assertIn("Scenario Facts:", sp.content)
        self.assertIn("Output Requirements:", sp.content)
        self.assertEqual(sp.params["temperature"], DEFAULT_PARAMS["temperature"])
        self.assertEqual(sp.params["max_tokens"], DEFAULT_PARAMS["max_tokens"])

    def test_override_params(self):
        sp = build_system_prompt(
            domain="Orders & Returns",
            behavior="Refund/Exchange/Cancellation",
            axes={},
            policy_text="p",
            facts_text="f",
            params_override={"temperature": 0.1},
        )
        self.assertEqual(sp.params["temperature"], 0.1)


if __name__ == "__main__":
    unittest.main()
