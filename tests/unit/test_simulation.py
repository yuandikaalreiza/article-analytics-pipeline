"""Check simulation timing, counts, and partial completion without real waits."""

import argparse
import contextlib
import io
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import psycopg

from scripts import generate_articles as cli


class SimulationTests(unittest.TestCase):
    """Exercise the full scheduler with a controlled clock and database seam."""

    def run_simulation(self, active=5, failure=None, **counts):
        """Run against a fake clock and capture operations and output.

        Args:
            active: Initial active article count.
            failure: Optional failure raised on the second operation.
            **counts: Operation totals overriding the fixture defaults.

        Returns:
            Exit code, output, operation log, elapsed seconds, and exception.
        """
        clock = [0.0]
        calls = []
        connection = MagicMock()
        connection.execute.return_value.fetchone.return_value = (active,)
        args = argparse.Namespace(
            duration=1, inserts=2, updates=2, soft_deletes=1, hard_deletes=0,
            author_id=7, seed=42,
        )
        for key, value in counts.items():
            setattr(args, key, value)

        def perform(connection, rng, operation, author_id, number):
            if failure and len(calls) == 1:
                raise failure
            calls.append((operation, clock[0]))
            return 1, datetime.now(timezone.utc)

        def sleep(seconds):
            clock[0] += seconds

        output = io.StringIO()
        error = None
        code = None
        with (
            patch.object(cli.psycopg, "connect") as connect,
            patch.object(cli, "simulate_operation", side_effect=perform),
            patch.object(cli.time, "monotonic", side_effect=lambda: clock[0]),
            patch.object(cli.time, "sleep", side_effect=sleep),
            contextlib.redirect_stdout(output),
        ):
            connect.return_value.__enter__.return_value = connection
            try:
                code = cli.simulate({}, args)
            except (RuntimeError, psycopg.Error) as caught:
                error = caught
        return code, output.getvalue(), calls, clock[0], error

    def test_counts_are_spread_across_minutes_and_seeded(self):
        """Finish all requested operations across 60 seconds with stable ordering."""
        first = self.run_simulation()
        second = self.run_simulation()
        self.assertEqual(first[0], 0)
        self.assertEqual(first[2], second[2])
        self.assertEqual(first[3], 60)
        self.assertEqual(sorted(op for op, _ in first[2]),
                         ["insert", "insert", "soft_delete", "update", "update"])
        self.assertTrue(all(i * 12 <= at < (i + 1) * 12
                            for i, (_, at) in enumerate(first[2])))

    def test_empty_database_inserts_before_editing_and_deleting(self):
        """Keep a target until all edits finish, even when every row is deleted."""
        result = self.run_simulation(active=0, inserts=1, updates=3, soft_deletes=1)
        self.assertEqual(result[0], 0)
        self.assertEqual(result[2][0][0], "insert")
        self.assertEqual(result[2][-1][0], "soft_delete")

    def test_impossible_counts_fail_before_any_write_or_wait(self):
        """Reject insufficient active rows without partially executing the run."""
        result = self.run_simulation(active=0, inserts=0, updates=0, soft_deletes=1)
        self.assertIsInstance(result[4], RuntimeError)
        self.assertEqual(result[2], [])
        self.assertEqual(result[3], 0)

    def test_hard_delete_only_run(self):
        """Allow a run containing only permanent deletions."""
        result = self.run_simulation(inserts=0, updates=0, soft_deletes=0, hard_deletes=1)
        self.assertEqual(result[0], 0)
        self.assertEqual([op for op, _ in result[2]], ["hard_delete"])

    def test_hard_delete_keeps_last_active_row_until_edits_finish(self):
        """Insert before edits on an empty source, then remove the last row."""
        result = self.run_simulation(active=0, inserts=1, updates=3,
                                     soft_deletes=0, hard_deletes=1)
        self.assertEqual(result[0], 0)
        self.assertEqual(result[2][0][0], "insert")
        self.assertEqual(result[2][-1][0], "hard_delete")

    def test_soft_and_hard_deletes_share_the_available_row_budget(self):
        """Reject combined deletions exceeding available active rows."""
        result = self.run_simulation(active=1, inserts=0, updates=0,
                                     soft_deletes=1, hard_deletes=1)
        self.assertIsInstance(result[4], RuntimeError)
        self.assertEqual(result[2], [])

    def test_failure_reports_only_committed_operations(self):
        """Stop on the second failed operation and report the first completion."""
        result = self.run_simulation(failure=psycopg.DatabaseError("test failure"))
        self.assertIsInstance(result[4], psycopg.Error)
        self.assertEqual(len(result[2]), 1)
        self.assertNotIn("Simulation completed", result[1])
        self.assertIn("remaining:", result[1])

    def test_keyboard_interrupt_returns_partial_summary(self):
        """Allow Ctrl+C without claiming the requested totals were completed."""
        result = self.run_simulation(failure=KeyboardInterrupt())
        self.assertEqual(result[0], 130)
        self.assertEqual(len(result[2]), 1)
        self.assertIn("Simulation stopped", result[1])

    def test_invalid_cli_inputs_never_connect(self):
        """Reject invalid durations and counts before loading credentials."""
        cases = [
            ["--duration", value] for value in ("0", "-1", "nan", "inf", "text")
        ] + [
            ["--duration", "60", "--updates", "-1"],
            ["--duration", "60", "--hard-deletes", "-1"],
            ["--duration", "60", "--inserts", "0", "--updates", "0", "--soft-deletes", "0"],
        ]
        with patch.object(cli, "load_settings") as settings:
            for flags in cases:
                with self.subTest(flags=flags), contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as caught:
                        cli.main(["simulate", *flags])
                    self.assertEqual(caught.exception.code, 2)
            settings.assert_not_called()


if __name__ == "__main__":
    unittest.main()
