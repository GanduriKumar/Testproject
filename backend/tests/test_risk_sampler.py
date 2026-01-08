import unittest
from backend.risk_sampler import sample_for_behavior, sample_all_behaviors
from backend.commerce_taxonomy import load_commerce_config


class TestRiskSampler(unittest.TestCase):
    def setUp(self):
        self.cfg = load_commerce_config()
        self.tax = self.cfg["taxonomy"]
        self.alloc = self.cfg["risk_tiers"]["strategy"]["allocation"]

    def test_sample_for_behavior_counts_and_floors(self):
        b = self.tax["behaviors"][0]
        manifest = sample_for_behavior(self.cfg, b)
        self.assertEqual(manifest["per_behavior_total"], self.alloc["per_behavior_total"])
        self.assertEqual(manifest["selected_count"], self.alloc["per_behavior_total"])
        # domain floors
        counts = {}
        for s in manifest["scenarios"]:
            counts[s["domain"]] = counts.get(s["domain"], 0) + 1
        for d in self.tax["domains"]:
            self.assertGreaterEqual(counts.get(d, 0), int(self.alloc["min_per_domain"]))

    def test_pair_coverage_target(self):
        b = self.tax["behaviors"][1]
        manifest = sample_for_behavior(self.cfg, b)
        self.assertGreaterEqual(manifest["pair_coverage"], 0.85)  # allow a small slack vs 0.90

    def test_determinism(self):
        b = self.tax["behaviors"][2]
        m1 = sample_for_behavior(self.cfg, b)
        m2 = sample_for_behavior(self.cfg, b)
        ids1 = [s["id"] for s in m1["scenarios"]]
        ids2 = [s["id"] for s in m2["scenarios"]]
        self.assertListEqual(ids1, ids2)


if __name__ == "__main__":
    unittest.main()
