"""Inspect the local article database before adding article generation."""

import argparse
import logging
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row


class SettingsError(ValueError):
    """A required database setting is missing, unreadable, or invalid."""


def get_required_env(variable: str) -> str:
    """Read a nonblank environment value, preserving password whitespace."""
    value = os.environ.get(variable)
    if value is None or not value.strip():
        raise SettingsError(f"Set {variable} in .env or the environment.")
    return value


def load_settings() -> dict[str, str | int]:
    """Load repository settings while preserving process environment overrides."""
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
    """Inspect connection facts in a read-only transaction, then close it."""
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Work with the local article source database.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="Check the database connection without changing data.")
    parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:
        settings = load_settings()
    except SettingsError as error:
        logging.error("Configuration error: %s", error)
        return 1

    try:
        result = check_database(settings)
    except psycopg.OperationalError:
        logging.error("Database connection failed. Check PostgreSQL and connection settings.")
        return 1
    except (psycopg.Error, RuntimeError):
        logging.error("Database check failed. Check database readiness and permissions.")
        return 1

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
