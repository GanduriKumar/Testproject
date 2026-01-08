import unittest
from pathlib import Path
from backend.policy_facts import load_policy_text, generate_facts, load_policy_and_facts


class TestPolicyFacts(unittest.TestCase):
    def test_load_policy_text(self):
        txt = load_policy_text("Orders & Returns")
        self.assertIn("Return window", txt)

    def test_generate_facts_constraints(self):
        axes = {
            "price_sensitivity": "high",
            "brand_bias": "hard",
            "availability": "sold_out",
            "policy_boundary": "near_edge_allowed",
        }
        txt = generate_facts(domain="Orders & Returns", axes=axes, seed=42)
        self.assertLessEqual(len(txt.split()), 120)
        self.assertGreaterEqual(txt.count("- "), 2)
        self.assertLessEqual(txt.count("- "), 5)

    def test_deterministic(self):
        axes = {
            "price_sensitivity": "medium",
            "brand_bias": "none",
            "availability": "in_stock",
            "policy_boundary": "within_policy",
        }
        t1 = generate_facts(domain="Inventory & Availability", axes=axes, seed=7)
        t2 = generate_facts(domain="Inventory & Availability", axes=axes, seed=7)
        self.assertEqual(t1, t2)

    def test_load_policy_and_facts(self):
        axes = {
            "price_sensitivity": "low",
            "brand_bias": "soft",
            "availability": "backorder",
            "policy_boundary": "within_policy",
        }
        policy, facts = load_policy_and_facts("Promotions & Pricing", axes, seed=11)
        self.assertIn("Coupon", policy)
        self.assertIn("- ", facts)


if __name__ == "__main__":
    unittest.main()
