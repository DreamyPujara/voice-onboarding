import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout

import tool


class FunnelSimulatorTests(unittest.TestCase):
    def test_default_demo_summary_is_valid(self):
        result = tool.summarize(tool.DEFAULT_DATA)
        self.assertTrue(result["valid"])
        self.assertEqual(result["flows"]["guided"]["starts"], 2)
        self.assertEqual(result["flows"]["guided"]["dropoffs"], 1)
        self.assertEqual(result["flows"]["fast"]["median_completion_minutes"], 1.25)

    def test_terminal_before_start_is_rejected(self):
        data = {
            "assumptions": {"flows": ["guided"]},
            "events": [
                {"participant": "p1", "flow": "guided", "event": "complete", "ts": "2026-01-01T09:00:00Z"}
            ],
        }
        result = tool.summarize(data)
        self.assertFalse(result["valid"])
        self.assertIn("terminal before start", "\n".join(result["errors"]))

    def test_cli_json_output_from_file(self):
        payload = {
            "assumptions": {"description": "test", "flows": ["fast"]},
            "events": [
                {"participant": "p1", "flow": "fast", "event": "start", "ts": "2026-01-01T10:00:00Z"},
                {"participant": "p1", "flow": "fast", "event": "complete", "ts": "2026-01-01T10:02:00Z"},
            ],
        }
        with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=True) as handle:
            json.dump(payload, handle)
            handle.flush()
            out = io.StringIO()
            with redirect_stdout(out):
                code = tool.main([handle.name, "--json"])
        self.assertEqual(code, 0)
        parsed = json.loads(out.getvalue())
        self.assertEqual(parsed["flows"]["fast"]["completion_rate"], 1.0)
        self.assertEqual(parsed["flows"]["fast"]["median_completion_minutes"], 2.0)


if __name__ == "__main__":
    unittest.main()
