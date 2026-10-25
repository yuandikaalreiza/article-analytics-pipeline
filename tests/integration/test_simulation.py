"""Verify lifecycle SQL against PostgreSQL inside rolled-back transactions."""

import random
import unittest

import psycopg

from scripts import generate_articles as cli


class SimulationIntegrationTests(unittest.TestCase):
    """Check real lifecycle constraints without committing fixture changes."""

    def test_lifecycle_operations_preserve_immutable_fields_and_rollback(self):
        """Exercise inserts, random edits, and soft deletes with actual SQL."""
        with psycopg.connect(**cli.load_settings(), connect_timeout=5, autocommit=True) as connection:
            before = connection.execute(
                "SELECT id, md5(row_to_json(a)::text) FROM public.articles a ORDER BY id"
            ).fetchall()
            with connection.transaction(force_rollback=True):
                rng = random.Random(42)
                original = dict(connection.execute(
                    "SELECT id, (author_id,created_at,published_at,deleted_at)::text "
                    "FROM public.articles"
                ).fetchall())
                inserted_id, _ = cli.simulate_operation(connection, rng, "insert", 7, 1)
                article = connection.execute(
                    "SELECT created_at=published_at AND published_at=updated_at, "
                    "deleted_at IS NULL FROM public.articles WHERE id=%s", (inserted_id,),
                ).fetchone()
                self.assertEqual(article, (True, True))
                edited_id, _ = cli.simulate_operation(connection, rng, "update", 7, 1)
                if edited_id in original:
                    immutable = connection.execute(
                        "SELECT (author_id,created_at,published_at,deleted_at)::text "
                        "FROM public.articles WHERE id=%s", (edited_id,),
                    ).fetchone()[0]
                    self.assertEqual(immutable, original[edited_id])
                deleted_id, _ = cli.simulate_operation(connection, rng, "soft_delete", 7, 1)
                self.assertEqual(connection.execute(
                    "SELECT deleted_at=updated_at, published_at<=deleted_at "
                    "FROM public.articles WHERE id=%s", (deleted_id,),
                ).fetchone(), (True, True))
                with connection.transaction(force_rollback=True):
                    connection.execute("UPDATE public.articles SET deleted_at=updated_at")
                    with self.assertRaisesRegex(RuntimeError, "No active article"):
                        cli.simulate_operation(connection, rng, "update", 7, 1)
            after = connection.execute(
                "SELECT id, md5(row_to_json(a)::text) FROM public.articles a ORDER BY id"
            ).fetchall()
            self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
