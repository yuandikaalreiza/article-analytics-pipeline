"""Inspect the local article database and generate synthetic article datasets."""

import argparse
import logging
import os
import random
import time
from collections import Counter
from collections.abc import Iterable, Iterator
from datetime import date, datetime, timedelta, timezone
from itertools import accumulate, batched
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


def start_date(value: str) -> datetime:
    """Parse a calendar date as midnight UTC.

    Args:
        value: Calendar date in YYYY-MM-DD form.

    Returns:
        The date's timezone-aware UTC midnight.

    Raises:
        argparse.ArgumentTypeError: If the date is invalid.
    """
    try:
        return datetime.combine(date.fromisoformat(value), datetime.min.time(), timezone.utc)
    except ValueError:
        raise argparse.ArgumentTypeError("must be a date in YYYY-MM-DD form") from None


def utc_timestamp(value: str) -> datetime:
    """Parse an explicitly timezone-aware ISO timestamp and normalize to UTC.

    Args:
        value: ISO timestamp with an offset or Z suffix.

    Returns:
        The equivalent timezone-aware UTC instant.

    Raises:
        argparse.ArgumentTypeError: If the timestamp is invalid or lacks a timezone.
    """
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError
        return parsed.astimezone(timezone.utc)
    except ValueError:
        raise argparse.ArgumentTypeError("must be an ISO timestamp with a timezone") from None


def historical_articles(
    count: int, start: datetime, until: datetime, seed: int, author_id: int,
) -> Iterator[dict[str, object]]:
    """Yield seeded articles with daytime-biased historical publication times.

    Args:
        count: Number of articles to yield.
        start: Inclusive UTC start instant.
        until: Exclusive UTC cutoff, validated by the CLI before generation.
        seed: Seed for an isolated random generator.
        author_id: Positive author ID for every generated article.

    Yields:
        Synthetic article values satisfying the existing lifecycle constraints.
    """
    rng = random.Random(seed)
    buckets = []
    weights = []
    begin = start
    while begin < until:
        end = min(begin.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1), until)
        duration = (end - begin) // timedelta(microseconds=1)
        daytime_weight = 3 if 8 <= begin.hour < 20 else 1
        weekday_weight = 1.2 if begin.weekday() < 5 else 1
        buckets.append((begin, duration))
        weights.append(duration * daytime_weight * weekday_weight)
        begin = end
    cumulative_weights = list(accumulate(weights))
    locations = ("Jakarta", "Bandung", "Surabaya", "Yogyakarta", "Semarang")
    topics = (
        ("Transportasi publik", "penambahan layanan untuk perjalanan harian"),
        ("Pelaku UMKM", "pelatihan pemasaran dan pengembangan produk lokal"),
        ("Ruang terbuka hijau", "perawatan fasilitas dan akses bagi warga"),
        ("Pendidikan digital", "pendampingan belajar dan pemanfaatan teknologi"),
        ("Festival budaya", "persiapan kegiatan seni bersama komunitas"),
        ("Pengelolaan sampah", "pemilahan sampah dan perluasan layanan lingkungan"),
    )
    for number in range(1, count + 1):
        bucket_start, duration = rng.choices(buckets, cum_weights=cumulative_weights, k=1)[0]
        published = bucket_start + timedelta(microseconds=rng.randrange(duration))
        max_delay = min(6 * 60 * 60 * 1_000_000, (published - start) // timedelta(microseconds=1))
        created = published - timedelta(microseconds=rng.randrange(max_delay + 1))
        city = rng.choice(locations)
        topic, activity = rng.choice(topics)
        yield {
            "title": f"[historical seed={seed}] {topic} di {city} Jadi Perhatian Warga #{number}",
            "content": (
                f"DATA SINTETIS UNTUK LATIHAN. {city} - {topic} menjadi pembahasan "
                f"warga dalam kegiatan yang berfokus pada {activity}. "
                "Peserta menyampaikan kebutuhan mereka dan membahas langkah yang dapat "
                "dilakukan bersama untuk meningkatkan layanan di lingkungan sekitar.\n\n"
                "Kegiatan dilanjutkan dengan diskusi antara komunitas dan pengelola "
                "fasilitas. Masukan akan dirangkum untuk menentukan prioritas berikutnya. "
                "Evaluasi berkala direncanakan agar perkembangan kegiatan dapat diikuti warga.\n\n"
                f"Artikel simulasi nomor {number}; bukan laporan peristiwa nyata."
            ),
            "published_at": published,
            "author_id": author_id,
            "created_at": created,
            "updated_at": published,
            "deleted_at": None,
        }


def preview_articles(articles: Iterable[dict[str, object]]) -> None:
    """Print three samples and a summary without database access.

    Args:
        articles: Generated articles to inspect in one streaming pass.
    """
    days = Counter()
    count = 0
    for count, article in enumerate(articles, start=1):
        if count <= 3:
            print(f"Sample {count}: {article['title']} | {article['published_at'].isoformat()}")
            print(article["content"])
        days[article["published_at"].date().isoformat()] += 1
    print(f"Preview articles: {count}")
    print(f"Publication dates: {len(days)}")
    if days:
        print(f"Date range (UTC): {min(days)} through {max(days)}")


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


def insert_in_batches(
    connection: psycopg.Connection,
    articles: Iterable[dict[str, object]],
    batch_size: int,
) -> int:
    """Insert bounded batches without committing the caller's transaction.

    Args:
        connection: Open connection owned by the caller.
        articles: Article stream to consume once.
        batch_size: Maximum articles retained for each insertion batch.

    Returns:
        The number of successfully inserted rows, still awaiting caller commit.

    Raises:
        psycopg.Error: If an insertion fails.
        RuntimeError: If an insertion returns no ID.
        ValueError: If batch_size is not positive.
    """
    count = 0
    for batch in batched(articles, batch_size):
        count += len(insert_articles(connection, batch))
    return count


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
    historical_command = commands.add_parser(
        "historical", help="Preview or insert seeded historical articles."
    )
    historical_command.add_argument("--count", type=positive_int, required=True)
    historical_command.add_argument("--start-date", type=start_date, required=True)
    historical_command.add_argument("--until", type=utc_timestamp, required=True)
    historical_command.add_argument("--seed", type=int)
    historical_command.add_argument("--author-id", type=positive_int, default=1)
    historical_command.add_argument("--batch-size", type=positive_int, default=500)
    historical_command.add_argument("--preview", action="store_true", help="Generate without database access.")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    started = time.monotonic()
    if args.command == "historical":
        if args.start_date >= args.until:
            parser.error("--until must be later than --start-date")
        if args.until > datetime.now(timezone.utc):
            parser.error("--until cannot be in the future")
        if args.seed is None:
            args.seed = random.SystemRandom().randrange(2**63)
        print(f"Seed: {args.seed}", flush=True)
        print(f"Range (UTC): [{args.start_date.isoformat()}, {args.until.isoformat()})", flush=True)
        articles = historical_articles(args.count, args.start_date, args.until, args.seed, args.author_id)
        if args.preview:
            preview_articles(articles)
            return 0

    try:
        settings = load_settings()
    except SettingsError as error:
        logging.error("Configuration error: %s", error)
        return 1

    try:
        if args.command == "check":
            result = check_database(settings)
        elif args.command == "insert":
            articles = (
                make_article(number, args.author_id)
                for number in range(1, args.count + 1)
            )
            with psycopg.connect(**settings, connect_timeout=5) as connection:
                inserted_ids = insert_articles(connection, articles)
        else:
            with psycopg.connect(**settings, connect_timeout=5) as connection:
                inserted_count = insert_in_batches(connection, articles, args.batch_size)
    except psycopg.OperationalError:
        logging.error("Database connection failed. Check PostgreSQL and connection settings.")
        return 1
    except (psycopg.Error, RuntimeError):
        logging.error("Database operation failed. Check schema, permissions, and article values.")
        return 1

    if args.command == "historical":
        print(f"Inserted historical articles: {inserted_count}")
        print(f"Elapsed seconds: {time.monotonic() - started:.3f}")
        return 0

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
