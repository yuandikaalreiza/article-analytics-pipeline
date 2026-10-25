"""Check configuration, CLI boundaries, and article data without PostgreSQL."""

import contextlib
import io
import json
import os
import runpy
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from dotenv import load_dotenv

from scripts import generate_articles as cli


TEST_ENV = {
    "POSTGRES_HOST": "configured-host.example",
    "POSTGRES_PORT": "15432",
    "POSTGRES_DB": "test_articles",
    "POSTGRES_USER": "test_writer",
    "POSTGRES_PASSWORD": "  test-only-password  ",
}


class ArticleUnitTests(unittest.TestCase):
    """Verify behavior without reading local credentials or opening sockets."""

    def setUp(self):
        """Isolate environment variables and stub the local dotenv reader."""
        environment = patch.dict(os.environ, TEST_ENV, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        dotenv_patch = patch.object(cli, "load_dotenv")
        self.dotenv = dotenv_patch.start()
        self.addCleanup(dotenv_patch.stop)

    def test_all_connection_settings_are_required(self):
        """Reject absent, empty, and whitespace-only connection values."""
        for name in TEST_ENV:
            for value in (None, "", "   "):
                with self.subTest(variable=name, value=value):
                    environment = {**TEST_ENV, name: value}
                    if value is None:
                        del environment[name]
                    with patch.dict(os.environ, environment, clear=True):
                        with self.assertRaisesRegex(cli.SettingsError, name):
                            cli.load_settings()

    def test_custom_values_and_password_whitespace_are_preserved(self):
        """Use supplied values instead of local-development defaults."""
        self.assertEqual(
            cli.load_settings(),
            {
                "host": TEST_ENV["POSTGRES_HOST"],
                "port": 15432,
                "dbname": TEST_ENV["POSTGRES_DB"],
                "user": TEST_ENV["POSTGRES_USER"],
                "password": TEST_ENV["POSTGRES_PASSWORD"],
            },
        )

    def test_root_dotenv_loading_preserves_process_overrides(self):
        """Read a fixture root dotenv file while retaining shell settings."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contents = "\n".join(f"{key}={json.dumps(value)}" for key, value in TEST_ENV.items())
            (root / ".env").write_text(contents, encoding="utf-8")
            with (
                patch.object(cli, "__file__", str(root / "scripts" / "generate_articles.py")),
                patch.object(cli, "load_dotenv", wraps=load_dotenv),
                patch.dict(os.environ, {"POSTGRES_HOST": "shell-override.example"}, clear=True),
            ):
                settings = cli.load_settings()
        self.assertEqual(settings["host"], "shell-override.example")
        self.assertEqual(settings["dbname"], TEST_ENV["POSTGRES_DB"])
        self.assertEqual(settings["password"], TEST_ENV["POSTGRES_PASSWORD"])

    def test_invalid_ports_are_rejected(self):
        """Reject noninteger and out-of-range ports."""
        for value in ("not-a-port", "1.5", "0", "-1", "65536"):
            with self.subTest(port=value), patch.dict(os.environ, POSTGRES_PORT=value):
                with self.assertRaisesRegex(cli.SettingsError, "POSTGRES_PORT"):
                    cli.load_settings()

    def test_port_boundaries_are_accepted(self):
        """Accept both valid TCP port boundaries."""
        for value in ("1", "65535"):
            with self.subTest(port=value), patch.dict(os.environ, POSTGRES_PORT=value):
                self.assertEqual(cli.load_settings()["port"], int(value))

    def test_password_placeholder_is_rejected(self):
        """Require a real configured password rather than the example value."""
        with patch.dict(os.environ, POSTGRES_PASSWORD="replace_with_your_local_password"):
            with self.assertRaisesRegex(cli.SettingsError, "POSTGRES_PASSWORD"):
                cli.load_settings()

    def test_dotenv_read_errors_are_sanitized(self):
        """Normalize file and decoding errors without their private details."""
        for error in (PermissionError("private detail"), UnicodeError("private detail")):
            with self.subTest(error=type(error).__name__):
                self.dotenv.side_effect = error
                with self.assertRaises(cli.SettingsError) as raised:
                    cli.load_settings()
                self.assertIn("Could not read", str(raised.exception))
                self.assertNotIn("private detail", str(raised.exception))

    def test_invalid_arguments_fail_before_configuration_or_connection(self):
        """Reject invalid CLI counts and authors before any external work."""
        cases = [[]]
        for option in ("--count", "--author-id"):
            cases.extend(["insert", option, value] for value in ("0", "-1", "bad", "1.5"))
        for args in cases:
            with (
                self.subTest(arguments=args),
                patch.object(cli, "load_settings") as settings,
                patch.object(cli.psycopg, "connect") as connect,
                contextlib.redirect_stderr(io.StringIO()),
            ):
                with self.assertRaises(SystemExit) as raised:
                    cli.main(args)
                self.assertEqual(raised.exception.code, 2)
                settings.assert_not_called()
                connect.assert_not_called()

    def test_help_needs_no_configuration(self):
        """Display help without credentials or a database connection."""
        for args in (["--help"], ["insert", "--help"]):
            with (
                self.subTest(arguments=args),
                patch.object(cli, "load_settings") as settings,
                contextlib.redirect_stdout(io.StringIO()),
            ):
                with self.assertRaises(SystemExit) as raised:
                    cli.main(args)
                self.assertEqual(raised.exception.code, 0)
                settings.assert_not_called()

    def test_generated_article_has_coherent_utc_timestamps(self):
        """Create active articles with one aware UTC lifecycle instant."""
        before = datetime.now(timezone.utc)
        article = cli.make_article(3, 17)
        after = datetime.now(timezone.utc)
        self.assertLessEqual(before, article["created_at"])
        self.assertLessEqual(article["created_at"], after)
        self.assertEqual(article["created_at"].utcoffset(), timedelta(0))
        self.assertEqual(article["created_at"], article["published_at"])
        self.assertEqual(article["published_at"], article["updated_at"])
        self.assertIsNone(article["deleted_at"])
        self.assertEqual(article["author_id"], 17)
        self.assertTrue(article["title"])
        self.assertTrue(article["content"])
        self.assertNotIn("id", article)

    def test_configuration_errors_prevent_database_access(self):
        """Return a safe failure before attempting an invalid connection."""
        del os.environ["POSTGRES_PASSWORD"]
        with patch.object(cli.psycopg, "connect") as connect, self.assertLogs(level="ERROR"):
            self.assertEqual(cli.main(["check"]), 1)
        connect.assert_not_called()

    def test_connection_errors_do_not_leak_credentials(self):
        """Hide driver exception details from CLI logs and output."""
        output = io.StringIO()
        error = cli.psycopg.OperationalError("postgresql://private-secret@example/db")
        with (
            patch.object(cli.psycopg, "connect", side_effect=error),
            self.assertLogs(level="ERROR") as logs,
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(cli.main(["insert"]), 1)
        self.assertEqual(output.getvalue(), "")
        self.assertNotIn("private-secret", "\n".join(logs.output))
        self.assertNotIn("postgresql://", "\n".join(logs.output))

    def test_missing_table_returns_a_safe_error(self):
        """Report schema readiness failure without printing success."""
        output = io.StringIO()
        with (
            patch.object(cli, "check_database", return_value={"articles_table_exists": False}),
            self.assertLogs(level="ERROR") as logs,
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(cli.main(["check"]), 1)
        self.assertIn("public.articles is missing", "\n".join(logs.output))
        self.assertEqual(output.getvalue(), "")

    def test_commit_failure_does_not_report_inserted_ids(self):
        """Print inserted IDs only after the connection context succeeds."""
        output = io.StringIO()
        with (
            patch.object(cli.psycopg, "connect") as connect,
            patch.object(cli, "insert_articles", return_value=[501, 502]),
            self.assertLogs(level="ERROR"),
            contextlib.redirect_stdout(output),
        ):
            connect.return_value.__exit__.side_effect = cli.psycopg.OperationalError("private detail")
            self.assertEqual(cli.main(["insert", "--count", "2"]), 1)
        self.assertEqual(output.getvalue(), "")

    def test_import_has_no_configuration_or_database_side_effects(self):
        """Load a fresh module namespace without invoking the application."""
        with patch("dotenv.load_dotenv") as dotenv, patch("psycopg.connect") as connect:
            runpy.run_path(cli.__file__, run_name="import_safety_check")
        dotenv.assert_not_called()
        connect.assert_not_called()

    def test_historical_values_are_reproducible_and_seeded(self):
        """Keep fixed-input values stable and vary them with a different seed."""
        start = cli.start_date("2026-10-01")
        until = cli.utc_timestamp("2026-10-25T00:00:00Z")
        first = list(cli.historical_articles(300, start, until, 42, 7))
        self.assertEqual(first, list(cli.historical_articles(300, start, until, 42, 7)))
        self.assertNotEqual(first, list(cli.historical_articles(300, start, until, 43, 7)))
        self.assertEqual(len(first), 300)
        self.assertGreater(len({row["published_at"].date() for row in first}), 1)
        for row in first:
            self.assertLessEqual(start, row["created_at"])
            self.assertLessEqual(row["created_at"], row["published_at"])
            self.assertLess(row["published_at"], until)
            self.assertEqual(row["published_at"], row["updated_at"])
            self.assertLessEqual(row["published_at"] - row["created_at"], timedelta(hours=6))
            self.assertEqual(row["published_at"].utcoffset(), timedelta(0))
            self.assertIsNone(row["deleted_at"])
            self.assertEqual(row["author_id"], 7)
            self.assertIn("DATA SINTETIS", row["content"])
            self.assertTrue(row["title"])

    def test_historical_short_interval_respects_exclusive_cutoff(self):
        """Generate within even a one-microsecond publication interval."""
        start = cli.start_date("2026-10-01")
        rows = list(cli.historical_articles(3, start, start + timedelta(microseconds=1), 1, 1))
        for row in rows:
            self.assertEqual(row["created_at"], start)
            self.assertEqual(row["published_at"], start)

    def test_historical_preview_never_loads_settings_or_connects(self):
        """Show a bounded preview while counting the full generated stream."""
        output = io.StringIO()
        with (
            patch.object(cli, "load_settings") as settings,
            patch.object(cli.psycopg, "connect") as connect,
            contextlib.redirect_stdout(output),
        ):
            result = cli.main([
                "historical", "--count", "20", "--start-date", "2026-10-01",
                "--until", "2026-10-02T00:00:00Z", "--seed", "42", "--preview",
            ])
        self.assertEqual(result, 0)
        self.assertIn("Preview articles: 20", output.getvalue())
        self.assertEqual(output.getvalue().count("Sample "), 3)
        settings.assert_not_called()
        connect.assert_not_called()

    def test_invalid_historical_inputs_fail_before_external_work(self):
        """Reject invalid ranges, timezone omissions, counts, authors, and batches."""
        base = ["historical", "--count", "3", "--start-date", "2026-10-01",
                "--until", "2026-10-02T00:00:00Z"]
        cases = (
            ("--count", "0"), ("--batch-size", "0"), ("--author-id", "-1"),
            ("--until", "2026-10-01T00:00:00Z"),
            ("--until", "2026-09-30T00:00:00Z"),
            ("--until", "2999-10-02T00:00:00Z"),
            ("--until", "2026-10-02T00:00:00"),
            ("--start-date", "invalid"), ("--seed", "invalid"),
        )
        for option, value in cases:
            with (
                self.subTest(option=option, value=value),
                patch.object(cli, "load_settings") as settings,
                patch.object(cli.psycopg, "connect") as connect,
                contextlib.redirect_stderr(io.StringIO()),
            ):
                with self.assertRaises(SystemExit) as raised:
                    cli.main([*base, option, value])
                self.assertEqual(raised.exception.code, 2)
                settings.assert_not_called()
                connect.assert_not_called()

    def test_historical_cutoff_normalizes_explicit_offsets(self):
        """Treat equivalent timezone-aware timestamps as the same cutoff."""
        self.assertEqual(cli.utc_timestamp("2026-10-02T07:00:00+07:00"),
                         cli.utc_timestamp("2026-10-02T00:00:00Z"))

    def test_historical_commit_failure_does_not_report_success(self):
        """Suppress the final inserted summary when committing fails."""
        output = io.StringIO()
        with (
            patch.object(cli.psycopg, "connect") as connect,
            patch.object(cli, "insert_in_batches", return_value=3),
            self.assertLogs(level="ERROR"),
            contextlib.redirect_stdout(output),
        ):
            connect.return_value.__exit__.side_effect = cli.psycopg.OperationalError("private detail")
            result = cli.main([
                "historical", "--count", "3", "--start-date", "2026-10-01",
                "--until", "2026-10-02T00:00:00Z", "--seed", "42",
            ])
        self.assertEqual(result, 1)
        self.assertNotIn("Inserted historical articles:", output.getvalue())


if __name__ == "__main__":
    unittest.main()
