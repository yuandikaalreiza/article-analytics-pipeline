"""Exercise real PostgreSQL transactions when explicitly invoked."""

import contextlib
import io
import re
import socket
import time
import unittest
from unittest.mock import patch
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row

from scripts import generate_articles as cli


class PostgresIntegrationTests(unittest.TestCase):
    """Use unique fixture titles and restore all pre-existing article data."""

    @classmethod
    def setUpClass(cls):
        """Require a configured, running database and the article schema.

        Raises:
            RuntimeError: If configuration, connectivity, or schema is unavailable.
        """
        try:
            cls.settings = cli.load_settings()
            with psycopg.connect(**cls.settings, connect_timeout=5) as connection:
                exists = connection.execute(
                    "SELECT to_regclass('public.articles') IS NOT NULL"
                ).fetchone()[0]
        except (cli.SettingsError, psycopg.Error):
            raise RuntimeError(
                "Integration tests require configured local PostgreSQL. Run the CLI check first."
            ) from None
        if not exists:
            raise RuntimeError("Apply sql/001_articles.sql before running integration tests.")

    def setUp(self):
        """Capture the original dataset and assign this test a unique marker."""
        self.original_snapshot = self.snapshot()
        self.marker = f"[integration {uuid4().hex}]"
        self.addCleanup(self.assert_database_restored)

    def snapshot(self) -> dict[str, str]:
        """Read row fingerprints without exposing article contents.

        Returns:
            A mapping of article IDs to fingerprints of their stored values.

        Raises:
            psycopg.Error: If connecting or reading the snapshot fails.
        """
        with psycopg.connect(**self.settings, connect_timeout=5) as connection:
            return connection.execute(
                "SELECT COALESCE(jsonb_object_agg(id::text, md5(to_jsonb(a)::text)), "
                "'{}'::jsonb) FROM public.articles AS a"
            ).fetchone()[0]

    def remove_fixture_rows(self, titles: list[str]) -> None:
        """Remove only the uniquely named rows created by this test.

        Args:
            titles: Exact titles belonging to this test's fixtures.

        Raises:
            psycopg.Error: If the connection or fixture cleanup fails.
        """
        with psycopg.connect(**self.settings, connect_timeout=5) as connection:
            connection.execute("DELETE FROM public.articles WHERE title = ANY(%s)", (titles,))

    def assert_database_restored(self):
        """Verify fixture cleanup left the original dataset unchanged."""
        self.assertEqual(self.snapshot(), self.original_snapshot)

    def test_check_is_read_only_and_preserves_data(self):
        """Verify real connection facts and the CLI's successful check output."""
        result = cli.check_database(self.settings)
        self.assertEqual(result["database_name"], self.settings["dbname"])
        self.assertEqual(result["database_user"], self.settings["user"])
        self.assertEqual(result["timezone"], "UTC")
        self.assertEqual(result["transaction_read_only"], "on")
        self.assertTrue(result["articles_table_exists"])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(cli.main(["check"]), 0)
        self.assertIn("Read-only transaction: on", output.getvalue())
        self.assertEqual(self.snapshot(), self.original_snapshot)

    def test_cli_insert_commits_and_round_trips_article_values(self):
        """Verify committed IDs, quoted text, UTC timestamps, and CLI output."""
        titles = [f"{self.marker} article {number}" for number in (1, 2)]
        self.addCleanup(self.remove_fixture_rows, titles)
        original_factory = cli.make_article
        expected_articles = []

        def make_fixture(number: int, author_id: int) -> dict[str, object]:
            """Label real generated articles for isolated verification.

            Args:
                number: Sequential article number supplied by the CLI.
                author_id: Author selected through the CLI.

            Returns:
                A generated article with this test's title and quoted content.
            """
            article = original_factory(number, author_id)
            article["title"] = titles[number - 1]
            article["content"] = "Berita Jakarta: 'kutipan', 50% dan kabar terkini."
            expected_articles.append(article)
            return article

        output = io.StringIO()
        with patch.object(cli, "make_article", side_effect=make_fixture):
            with contextlib.redirect_stdout(output):
                result = cli.main(["insert", "--count", "2", "--author-id", "7"])
        self.assertEqual(result, 0)
        self.assertIn("Inserted articles: 2", output.getvalue())
        match = re.search(r"^IDs: ([0-9, ]+)$", output.getvalue(), re.MULTILINE)
        self.assertIsNotNone(match)
        ids = [int(value.strip()) for value in match.group(1).split(",")]
        self.assertEqual(len(set(ids)), 2)

        with psycopg.connect(**self.settings, row_factory=dict_row) as connection:
            rows = connection.execute(
                "SELECT * FROM public.articles WHERE id = ANY(%s)", (ids,)
            ).fetchall()
        self.assertEqual(len(rows), 2)
        rows_by_id = {row["id"]: row for row in rows}
        for article_id, expected in zip(ids, expected_articles, strict=True):
            with self.subTest(article_id=article_id):
                self.assertGreater(article_id, 0)
                for field, value in expected.items():
                    self.assertEqual(rows_by_id[article_id][field], value)

    def test_caller_can_rollback_a_successful_insert(self):
        """Ensure the insertion helper does not commit on its caller's behalf."""
        article = cli.make_article(1, 1)
        article["title"] = f"{self.marker} caller rollback"
        self.addCleanup(self.remove_fixture_rows, [article["title"]])
        with psycopg.connect(**self.settings) as connection:
            ids = cli.insert_articles(connection, [article])
            self.assertEqual(len(ids), 1)
            connection.rollback()
        self.assertEqual(self.snapshot(), self.original_snapshot)

    def test_failed_second_insert_rolls_back_the_first(self):
        """Reject an invalid author without committing a partial batch."""
        valid = cli.make_article(1, 1)
        invalid = cli.make_article(2, 0)
        valid["title"] = f"{self.marker} valid probe"
        invalid["title"] = f"{self.marker} invalid probe"
        self.addCleanup(self.remove_fixture_rows, [valid["title"], invalid["title"]])
        with self.assertRaises(psycopg.errors.CheckViolation):
            with psycopg.connect(**self.settings) as connection:
                cli.insert_articles(connection, [valid, invalid])
        self.assertEqual(self.snapshot(), self.original_snapshot)

    def test_unreachable_connection_fails_promptly_and_safely(self):
        """Exercise a real connection failure without stopping PostgreSQL."""
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        settings = {**self.settings, "host": "127.0.0.1", "port": port}
        output = io.StringIO()
        started = time.monotonic()
        with (
            patch.object(cli, "load_settings", return_value=settings),
            self.assertLogs(level="ERROR") as logs,
            contextlib.redirect_stdout(output),
        ):
            result = cli.main(["check"])
        self.assertEqual(result, 1)
        self.assertLess(time.monotonic() - started, 12)
        self.assertEqual(output.getvalue(), "")
        message = "\n".join(logs.output)
        self.assertIn("Database connection failed", message)
        self.assertTrue(str(self.settings["password"]) not in message, "Password leaked.")
        self.assertTrue("postgresql://" not in message, "Connection string leaked.")

    def test_missing_table_is_reported_without_schema_changes(self):
        """Use the empty maintenance database without removing any tables."""
        settings = {**self.settings, "dbname": "postgres"}
        readiness = cli.check_database(settings)
        if readiness["articles_table_exists"]:
            self.skipTest("Maintenance database already has articles; leave its table intact.")
        output = io.StringIO()
        with (
            patch.object(cli, "load_settings", return_value=settings),
            self.assertLogs(level="ERROR") as logs,
            contextlib.redirect_stdout(output),
        ):
            result = cli.main(["check"])
        self.assertEqual(result, 1)
        self.assertIn("public.articles is missing", "\n".join(logs.output))
        self.assertEqual(output.getvalue(), "")

    def test_historical_cli_commits_across_batches(self):
        """Round-trip seeded data across full and partial batches via the CLI."""
        original_factory = cli.historical_articles
        expected = list(original_factory(
            3, cli.start_date("2026-10-01"), cli.utc_timestamp("2026-10-02T00:00:00Z"), 42, 7,
        ))
        for number, row in enumerate(expected):
            row["title"] = f"{self.marker} historical {number}"
        self.addCleanup(self.remove_fixture_rows, [row["title"] for row in expected])
        output = io.StringIO()
        with (
            patch.object(cli, "historical_articles", return_value=iter(expected)),
            contextlib.redirect_stdout(output),
        ):
            result = cli.main([
                "historical", "--count", "3", "--start-date", "2026-10-01",
                "--until", "2026-10-02T00:00:00Z", "--seed", "42",
                "--author-id", "7", "--batch-size", "2",
            ])
        self.assertEqual(result, 0)
        self.assertIn("Inserted historical articles: 3", output.getvalue())
        with psycopg.connect(**self.settings, row_factory=dict_row) as connection:
            rows = connection.execute(
                "SELECT * FROM public.articles WHERE title = ANY(%s) ORDER BY title",
                ([row["title"] for row in expected],),
            ).fetchall()
        self.assertEqual(len(rows), 3)
        for stored, generated in zip(rows, expected, strict=True):
            for field, value in generated.items():
                self.assertEqual(stored[field], value)

    def test_historical_later_batch_failure_rolls_back_all_batches(self):
        """Leave no earlier batch committed when the third generated row fails."""
        rows = list(cli.historical_articles(
            3, cli.start_date("2026-10-01"), cli.utc_timestamp("2026-10-02T00:00:00Z"), 42, 7,
        ))
        for number, row in enumerate(rows):
            row["title"] = f"{self.marker} failed historical {number}"
        rows[-1]["author_id"] = 0
        self.addCleanup(self.remove_fixture_rows, [row["title"] for row in rows])
        output = io.StringIO()
        with (
            patch.object(cli, "historical_articles", return_value=iter(rows)),
            self.assertLogs(level="ERROR"),
            contextlib.redirect_stdout(output),
        ):
            result = cli.main([
                "historical", "--count", "3", "--start-date", "2026-10-01",
                "--until", "2026-10-02T00:00:00Z", "--seed", "42", "--batch-size", "2",
            ])
        self.assertEqual(result, 1)
        self.assertNotIn("Inserted historical articles:", output.getvalue())
        self.assertEqual(self.snapshot(), self.original_snapshot)

    def test_batch_size_does_not_change_generated_values(self):
        """Store identical values across batch sizes without retaining fixtures."""
        for batch_size in (1, 2, 10):
            with self.subTest(batch_size=batch_size):
                rows = list(cli.historical_articles(
                    3, cli.start_date("2026-10-01"), cli.utc_timestamp("2026-10-02T00:00:00Z"), 43, 7,
                ))
                for number, row in enumerate(rows):
                    row["title"] = f"{self.marker} batch {batch_size} article {number}"
                self.addCleanup(self.remove_fixture_rows, [row["title"] for row in rows])
                with psycopg.connect(**self.settings, row_factory=dict_row) as connection:
                    self.assertEqual(cli.insert_in_batches(connection, iter(rows), batch_size), 3)
                    stored = connection.execute(
                        "SELECT * FROM public.articles WHERE title = ANY(%s) ORDER BY title",
                        ([row["title"] for row in rows],),
                    ).fetchall()
                    self.assertEqual(len(stored), 3)
                    for actual, expected in zip(stored, rows, strict=True):
                        for field, value in expected.items():
                            self.assertEqual(actual[field], value)
                    connection.rollback()
        self.assertEqual(self.snapshot(), self.original_snapshot)


if __name__ == "__main__":
    unittest.main()
