import json
import subprocess
import sys
import unittest


class CliIntegrationTests(unittest.TestCase):
    def test_cli_demonstrates_start_task_completion_and_shutdown(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", "runtime", "--objective", "CLI integration"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        events = [json.loads(line) for line in completed.stdout.splitlines()]
        self.assertEqual(
            [event["event"] for event in events],
            [
                "runtime.started",
                "task.created",
                "task.completed",
                "runtime.stopped",
            ],
        )
        self.assertEqual(events[2]["real_llm_calls"], 0)
        self.assertIn("STUB (no LLM inference)", events[2]["output"])


if __name__ == "__main__":
    unittest.main()
