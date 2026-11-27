"""Unit & integration test for Trend Intelligence Engine.
Tests normalization, niche filtering, scoring, and trend selection without publishing.
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from trend_research import normalizer, niche_filter, scorer, selector

class TestTrendIntelligence(unittest.TestCase):
    def test_normalization_and_topic_id(self):
        cand = normalizer.create_candidate(
            title="Why Is The Sky Blue? <b>Surprising</b> Physics Fact!",
            category="science",
            source="test_source",
            url="https://example.com/sky",
            summary="Rayleigh scattering causes the sky to appear blue to the human eye.",
            raw_metrics={"traffic": 100_000}
        )
        self.assertTrue(len(cand["topic_id"]) > 8)
        self.assertEqual(cand["category"], "science")
        self.assertIn("Rayleigh scattering", cand["summary"])

    def test_niche_filter_blocks_toxic(self):
        toxic_cand = {
            "title": "Shocking Political Election Scandal: Minister Arrested in Fraud Scheme",
            "summary": "Police arrest minister over scam money."
        }
        safe, reason, cat = niche_filter.is_safe_and_relevant(toxic_cand)
        self.assertFalse(safe)
        self.assertIn("Banned keyword", reason)

    def test_niche_filter_allows_curiosity(self):
        good_cand = {
            "title": "ISRO Discovers Ancient Water Ice Signs in Moon Polar Craters",
            "summary": "Chandrayaan instruments detected water molecules in the shadowed regions.",
            "category": "space"
        }
        safe, reason, cat = niche_filter.is_safe_and_relevant(good_cand)
        self.assertTrue(safe)
        self.assertEqual(cat, "space")

    def test_scoring_weights(self):
        cand = normalizer.create_candidate(
            title="Why Do Octopuses Have Three Hearts and Blue Blood?",
            category="animals",
            source="google_trends",
            url="https://example.com/octopus",
            summary="Octopuses use hemocyanin instead of hemoglobin to transport oxygen.",
            raw_metrics={"traffic": 250_000}
        )
        scored = scorer.score_candidate(cand)
        score = scored["score"]
        self.assertTrue(0.0 <= score <= 100.0)
        self.assertTrue(score >= 60.0, f"Score should be high for viral trend, got {score}")
        self.assertIn("search_popularity", scored["score_breakdown"])

    def test_candidate_merging(self):
        c1 = normalizer.create_candidate("James Webb Telescope", "space", "google_trends", "https://url1.com")
        c2 = normalizer.create_candidate("James Webb Telescope", "space", "rss_news", "https://url2.com")
        merged = normalizer.merge_candidates(c1, c2)
        self.assertEqual(len(merged["sources"]), 2)
        self.assertEqual(len(merged["source_urls"]), 2)

if __name__ == "__main__":
    unittest.main()
