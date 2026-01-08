import unittest
from pathlib import Path
from backend.commerce_taxonomy import (
    load_taxonomy,
    load_risk_tiers,
    load_commerce_config,
    TaxonomyValidationError,
)


class TestCommerceTaxonomy(unittest.TestCase):
    def setUp(self):
        self.tax_path = Path("configs/commerce_taxonomy.json")
        self.risk_path = Path("configs/risk_tiers.json")

    def test_load_taxonomy_ok(self):
        tax = load_taxonomy(self.tax_path)
        self.assertEqual(tax.domain_type, "commerce")
        self.assertIn("Orders & Returns", tax.domains)
        self.assertIn("Refund/Exchange/Cancellation", tax.behaviors)
        self.assertIn("price_sensitivity", tax.axes)
        self.assertIn("high", tax.axes["price_sensitivity"])  # bin exists

    def test_load_risk_tiers_ok(self):
        tax = load_taxonomy(self.tax_path)
        risk = load_risk_tiers(self.risk_path, tax)
        alloc = risk.strategy["allocation"]
        self.assertEqual(int(alloc["per_behavior_total"]), int(alloc["high"] + alloc["medium"] + alloc["low"]))
        # check an axis label valid
        self.assertEqual(risk.risk["axes"]["policy_boundary"]["near_edge_allowed"], "high")

    def test_load_commerce_config_ok(self):
        cfg = load_commerce_config(self.tax_path, self.risk_path)
        self.assertIn("taxonomy", cfg)
        self.assertIn("risk_tiers", cfg)

    def test_risk_invalid_axis_bin_raises(self):
        tax = load_taxonomy(self.tax_path)
        # create temp invalid risk file
        tmp = Path("configs/tmp_invalid_risk.json")
        tmp.write_text(
            """
            {
              "version": "x",
              "strategy": {"allocation": {"per_behavior_total": 100, "high": 50, "medium": 35, "low": 15, "min_per_domain": 3}},
              "risk": {"axes": {"price_sensitivity": {"extreme": "high"}}, "domains": {}, "behaviors": {}}
            }
            """,
            encoding="utf-8",
        )
        try:
            with self.assertRaises(TaxonomyValidationError):
                load_risk_tiers(tmp, tax)
        finally:
            try:
                tmp.unlink()
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main()
