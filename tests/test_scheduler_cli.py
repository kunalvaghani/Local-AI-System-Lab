import io
import json
import unittest
from contextlib import redirect_stdout

from runtime.scheduler_cli import main


class SchedulerCliTests(unittest.TestCase):
    def test_cli_visibly_compares_fifo_and_priority_order(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main([])

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["matches_expected"])
        self.assertEqual(
            payload["comparison"]["fifo"]["controlled_execution_order"],
            ["background", "standard", "interactive"],
        )
        self.assertEqual(
            payload["comparison"]["priority"]["controlled_execution_order"],
            ["interactive", "standard", "background"],
        )
        self.assertEqual(
            payload["comparison"]["priority"]["metrics"]["peak_queue_depth"],
            3,
        )


if __name__ == "__main__":
    unittest.main()
