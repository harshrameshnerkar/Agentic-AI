"""Unit tests for Day 20 Session 3: Sprint Retrospective Analyzer."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from retro_analyzer import SprintRetrospectiveManager


class TestSprintRetrospective(unittest.TestCase):
    """Test suite for Day 20 Sprint Retrospective data and lessons."""

    def setUp(self):
        self.mgr = SprintRetrospectiveManager()

    def test_load_retro_data_structure(self):
        """Verify retrospective data structure and participants."""
        data = self.mgr.load_retro_data()
        self.assertIn("participants", data)
        self.assertIn("sprint_variance", data)
        self.assertIn("three_specific_mistakes", data)
        self.assertIn("action_items_next_sprint", data)
        self.assertEqual(len(data["participants"]), 2)

    def test_variance_summary_calculation(self):
        """Verify estimation variance math across analyzed sprint tasks."""
        summary = self.mgr.calculate_variance_summary()
        self.assertEqual(summary.tasks_analyzed, 4)
        self.assertAlmostEqual(summary.total_estimated_hours, 9.0, places=1)
        self.assertAlmostEqual(summary.total_actual_hours, 7.5, places=1)
        self.assertAlmostEqual(summary.net_variance_hours, -1.5, places=1)
        self.assertEqual(summary.mistakes_cataloged, 3)

    def test_three_specific_mistakes_completeness(self):
        """Verify exactly 3 technical mistakes with lessons are documented."""
        mistakes = self.mgr.get_mistakes()
        self.assertEqual(len(mistakes), 3)
        for m in mistakes:
            self.assertIn("id", m)
            self.assertIn("title", m)
            self.assertIn("what_happened", m)
            self.assertIn("technical_lesson", m)

    def test_mistakes_architectural_depth(self):
        """Verify mistakes cover HMAC replay, ReDoS, and audit lock concurrency."""
        mistakes = self.mgr.get_mistakes()
        titles = " ".join(m["title"] for m in mistakes)
        self.assertIn("HMAC", titles)
        self.assertIn("ReDoS", titles)
        self.assertIn("Audit", titles)

    def test_action_items_count(self):
        """Verify forward-looking action items are cataloged."""
        summary = self.mgr.calculate_variance_summary()
        self.assertGreaterEqual(summary.action_items_count, 3)


if __name__ == "__main__":
    unittest.main()
