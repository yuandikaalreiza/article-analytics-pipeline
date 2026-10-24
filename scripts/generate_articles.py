"""Inspect the local article database and insert small demonstration datasets."""

import argparse
import logging
import os
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row


class SettingsError(ValueError):
    """A required database setting is missing, unreadable, or invalid."""


def get_required_env(variable: str) -> str:
    """Read a nonblank environment value without trimming its value.

    Args:
        variable: Name of the environment variable to read.

    Returns:
        The environment variable value, preserving surrounding whitespace.

    Raises:
        SettingsError: If the variable is missing or contains only whitespace.
    """
    value = os.environ.get(variable)
    if value is None or not value.strip():
        raise SettingsError(f"Set {variable} in .env or the environment.")
    return value


def load_settings() -> dict[str, str | int]:
    """Load database settings from the repository environment configuration.

    Values already set in the process environment take precedence over `.env`.

    Returns:
        Connection settings accepted by `psycopg.connect`.

    Raises:
        SettingsError: If `.env` cannot be read or a setting is invalid.
    """
    repository_root = Path(__file__).resolve().parents[1]
    try:
        load_dotenv(repository_root / ".env", override=False)
    except (OSError, UnicodeError):
        raise SettingsError(
            "Could not read the repository .env file. Check its encoding and permissions."
        ) from None

    host = get_required_env("POSTGRES_HOST").strip()
    database = get_required_env("POSTGRES_DB").strip()
    user = get_required_env("POSTGRES_USER").strip()
    port_value = get_required_env("POSTGRES_PORT")
    password = get_required_env("POSTGRES_PASSWORD")

    try:
        port = int(port_value)
    except ValueError:
        raise SettingsError("POSTGRES_PORT must be an integer from 1 to 65535.") from None
    if not 1 <= port <= 65535:
        raise SettingsError("POSTGRES_PORT must be an integer from 1 to 65535.")

    if password.strip() == "replace_with_your_local_password":
        raise SettingsError(
            "Set POSTGRES_PASSWORD to a local password in .env or the environment."
        )

    return {
        "host": host,
        "dbname": database,
        "user": user,
        "port": port,
        "password": password,
    }


def check_database(settings: dict[str, str | int]) -> dict[str, object]:
    """Inspect database connection facts without changing data.

    Args:
        settings: Connection settings accepted by `psycopg.connect`.

    Returns:
        Database name, user, server version, timezone, transaction mode, and
        whether `public.articles` exists.

    Raises:
        psycopg.Error: If connecting or querying the database fails.
        RuntimeError: If the query returns no row.
    """
    with psycopg.connect(**settings, connect_timeout=5, row_factory=dict_row) as connection:
        connection.read_only = True
        result = connection.execute(
            """
            SELECT current_database() AS database_name,
                   current_user AS database_user,
                   current_setting('server_version') AS server_version,
                   current_setting('TimeZone') AS timezone,
                   current_setting('transaction_read_only') AS transaction_read_only,
                   to_regclass('public.articles') IS NOT NULL AS articles_table_exists
            """
        ).fetchone()
    if result is None:
        raise RuntimeError("The database check returned no result.")
    return result


def positive_int(value: str) -> int:
    """Parse a positive integer for use as a command-line argument.

    Args:
        value: Text supplied for an integer command-line option.

    Returns:
        The parsed positive integer.

    Raises:
        argparse.ArgumentTypeError: If the value is not a positive integer.
    """
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be a positive integer") from None
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def make_article(number: int, author_id: int) -> dict[str, object]:
    """Create one demonstration article with consistent UTC timestamps.

    Args:
        number: Number used in the generated title and content.
        author_id: ID of the article's author.

    Returns:
        Article values ready for insertion into `public.articles`.
    """
    now = datetime.now(timezone.utc)
    return {
        "title": f"[python demo] Article {number}",
        "content": f"This article's content is generated for local practice, article {number}.",
        "published_at": now,
        "author_id": author_id,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None,
    }


def insert_articles(
    connection: psycopg.Connection,
    articles: Iterable[dict[str, object]],
) -> list[int]:
    """Insert articles and return their generated IDs.

    The caller owns the transaction and decides whether it commits or rolls back.

    Args:
        connection: Open PostgreSQL connection for the active transaction.
        articles: Article values to insert.

    Returns:
        IDs returned by PostgreSQL, in insertion order.

    Raises:
        psycopg.Error: If PostgreSQL rejects an insert or execution fails.
        RuntimeError: If an insertion returns no ID.
    """
    inserted_ids = []
    with connection.cursor(row_factory=dict_row) as cursor:
        for article in articles:
            cursor.execute(
                """
                INSERT INTO public.articles (
                    title, content, published_at, author_id,
                    created_at, updated_at, deleted_at
                ) VALUES (
                    %(title)s, %(content)s, %(published_at)s, %(author_id)s,
                    %(created_at)s, %(updated_at)s, %(deleted_at)s
                )
                RETURNING id
                """,
                article,
            )
            result = cursor.fetchone()
            if result is None:
                raise RuntimeError("Article insertion returned no ID.")
            inserted_ids.append(result["id"])
    return inserted_ids


def main(argv: list[str] | None = None) -> int:
    """Run the article database command-line interface.

    Args:
        argv: Optional command-line arguments; defaults to process arguments.

    Returns:
        Exit status: `0` for success and `1` for handled configuration or
        database errors. Argument parsing may exit with status `2` on invalid
        command-line input.
    """
    parser = argparse.ArgumentParser(description="Work with the local article source database.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="Check the database connection without changing data.")
    insert_command = commands.add_parser("insert", help="Insert a few demonstration articles.")
    insert_command.add_argument(
        "--count", type=positive_int, default=1, help="Number of articles (default: 1)."
    )
    insert_command.add_argument(
        "--author-id", type=positive_int, default=1, help="Author ID (default: 1)."
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:
        settings = load_settings()
    except SettingsError as error:
        logging.error("Configuration error: %s", error)
        return 1

    try:
        if args.command == "check":
            result = check_database(settings)
        else:
            articles = (
                make_article(number, args.author_id)
                for number in range(1, args.count + 1)
            )
            with psycopg.connect(**settings, connect_timeout=5) as connection:
                inserted_ids = insert_articles(connection, articles)
    except psycopg.OperationalError:
        logging.error("Database connection failed. Check PostgreSQL and connection settings.")
        return 1
    except (psycopg.Error, RuntimeError):
        logging.error("Database operation failed. Check schema, permissions, and article values.")
        return 1

    if args.command == "insert":
        print(f"Inserted articles: {len(inserted_ids)}")
        print(f"IDs: {', '.join(str(article_id) for article_id in inserted_ids)}")
        return 0

    if not result["articles_table_exists"]:
        logging.error("public.articles is missing. Apply sql/001_articles.sql first.")
        return 1

    print(f"Database: {result['database_name']}")
    print(f"User: {result['database_user']}")
    print(f"PostgreSQL: {result['server_version']}")
    print(f"Timezone: {result['timezone']}")
    print(f"Read-only transaction: {result['transaction_read_only']}")
    print("Articles table: public.articles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
