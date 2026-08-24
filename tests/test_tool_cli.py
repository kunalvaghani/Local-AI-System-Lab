import io
import json
import unittest
from contextlib import redirect_stdout

from runtime.tool_cli import main


class ToolCliTests(unittest.TestCase):
    def test_demo_shows_permitted_and_default_denied_requests(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["--demo"])

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["permitted_request"]["allowed"])
        self.assertEqual(
            payload["permitted_request"]["result"]["final_state"],
            "completed",
        )
        self.assertFalse(payload["denied_request"]["allowed"])
        self.assertEqual(payload["denied_request"]["final_state"], "security_blocked")
        self.assertEqual(
            payload["denied_request"]["error"]["code"],
            "tool_permission_denied",
        )


if __name__ == "__main__":
    unittest.main()
