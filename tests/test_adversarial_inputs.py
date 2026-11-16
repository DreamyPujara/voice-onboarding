import unittest

import tool


class AdversarialInputTests(unittest.TestCase):
    def test_rejects_non_object_and_empty_events(self):
        self.assertEqual(
            tool.summarize([]),
            {"valid": False, "errors": ["input must be a JSON object with assumptions and events"]},
        )
        result = tool.summarize({"assumptions": {}, "events": []})
        self.assertFalse(result["valid"])
        self.assertIn("events must contain at least one event", result["errors"])

    def test_reports_multiple_malformed_event_errors(self):
        data = {
            "assumptions": {"flows": ["guided"], "terminal_events": ["complete", "dropoff"]},
            "events": [
                "not an object",
                {"participant": "", "flow": "guided", "event": "start", "ts": "bad"},
                {"participant": "p1", "flow": "unknown", "event": "skip", "ts": 7},
                {"participant": "p2", "flow": "guided", "event": "complete", "ts": "2026-01-01T09:00:00Z"},
            ],
        }
        errors = tool.summarize(data)["errors"]
        self.assertIn("event 0 must be an object", errors)
        self.assertIn("event 1 field participant must be a non-empty string", errors)
        self.assertIn("event 1 invalid timestamp 'bad'", errors)
        self.assertIn("event 2 has unknown flow 'unknown'", errors)
        self.assertIn("event 2 has unsupported event 'skip'", errors)
        self.assertIn("event 2 timestamp must be a string", errors)
        self.assertIn("event 3 has terminal before start for p2 in guided", errors)

    def test_zero_minute_completion_is_valid_boundary(self):
        data = {
            "assumptions": {"flows": ["guided"], "terminal_events": ["complete", "dropoff"]},
            "events": [
                {"participant": "p1", "flow": "guided", "event": "start", "ts": "2026-01-01T09:00:00Z"},
                {"participant": "p1", "flow": "guided", "event": "complete", "ts": "2026-01-01T09:00:00Z"},
            ],
        }
        result = tool.summarize(data)
        self.assertTrue(result["valid"])
        self.assertEqual(result["flows"]["guided"]["median_completion_minutes"], 0.0)


if __name__ == "__main__":
    unittest.main()
