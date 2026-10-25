"""Inspect the local article database and generate synthetic article datasets."""

import argparse
import logging
import math
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


def nonnegative_int(value: str) -> int:
    """Parse an operation count.

    Args:
        value: Command-line count.

    Returns:
        An integer greater than or equal to zero.

    Raises:
        argparse.ArgumentTypeError: If the count is invalid.
    """
    try:
        number = int(value)
        if number >= 0:
            return number
    except ValueError:
        pass
    raise argparse.ArgumentTypeError("must be a nonnegative integer")


def duration_minutes(value: str) -> float:
    """Parse a finite, positive duration in minutes.

    Args:
        value: Command-line duration.

    Returns:
        Duration in minutes, including fractional minutes for short exercises.

    Raises:
        argparse.ArgumentTypeError: If the duration is invalid.
    """
    try:
        minutes = float(value)
        if math.isfinite(minutes) and minutes > 0 and math.isfinite(minutes * 60):
            return minutes
    except ValueError:
        pass
    raise argparse.ArgumentTypeError("must be a finite positive number of minutes")


def simulate_operation(
    connection: psycopg.Connection, rng: random.Random, operation: str,
    author_id: int, number: int,
) -> tuple[int, datetime]:
    """Perform one lifecycle operation in the caller's transaction.

    Args:
        connection: Open database connection.
        rng: Random generator used for synthetic article text.
        operation: insert, update, soft_delete, or hard_delete.
        author_id: Author for new articles.
        number: Sequence number for a new article.

    Returns:
        Affected article ID and its operation timestamp. For hard deletes this
        is the database execution time, not a stored updated_at value.

    Raises:
        RuntimeError: If no active article is available.
        ValueError: If the operation is unknown.
        psycopg.Error: If the database rejects the operation.
    """
    if operation == "insert":
        article = make_article(number, author_id)
        city = rng.choice(("Jakarta", "Bandung", "Surabaya", "Yogyakarta"))
        topic = rng.choice(("Community", "Technology", "Business", "Culture", "Sports"))
        article["title"] = f"[simulation] {topic} developments in {city} #{number}"
        article["content"] = (
            f"Synthetic report: {topic} developments in {city}. "
            "Residents and local organizations discuss recent changes and upcoming activities. "
            "This article was generated for local pipeline testing."
        )
        article_id = insert_articles(connection, [article])[0]
        return article_id, article["updated_at"]

    if operation not in ("update", "soft_delete", "hard_delete"):
        raise ValueError("Unknown simulation operation")
    active_count = connection.execute(
        "SELECT count(*) FROM public.articles WHERE deleted_at IS NULL"
    ).fetchone()[0]
    if not active_count:
        raise RuntimeError("No active article available for simulation.")
    target = connection.execute(
        "SELECT id, updated_at FROM public.articles WHERE deleted_at IS NULL "
        "ORDER BY id OFFSET %s LIMIT 1 FOR UPDATE", (rng.randrange(active_count),),
    ).fetchone()
    if target is None:
        raise RuntimeError("No active article available for simulation.")
    if operation == "update":
        result = connection.execute(
            "UPDATE public.articles SET title = title || ' [revised]', "
            "content = content || E'\\nEditorial update: new context added for local simulation.', "
            "updated_at = greatest(clock_timestamp(), updated_at + interval '1 microsecond') "
            "WHERE id = %s RETURNING id, updated_at", (target[0],),
        ).fetchone()
    elif operation == "soft_delete":
        deleted_at = max(datetime.now(timezone.utc), target[1] + timedelta(microseconds=1))
        result = connection.execute(
            "UPDATE public.articles SET deleted_at = %s, updated_at = %s "
            "WHERE id = %s RETURNING id, updated_at", (deleted_at, deleted_at, target[0]),
        ).fetchone()
    else:
        result = connection.execute(
            "DELETE FROM public.articles WHERE id = %s RETURNING id, clock_timestamp()",
            (target[0],),
        ).fetchone()
    return result


def wait_until(deadline: float) -> None:
    """Wait until a monotonic deadline in interruptible chunks.

    Args:
        deadline: Target from time.monotonic().
    """
    while (remaining := deadline - time.monotonic()) > 0:
        time.sleep(min(remaining, 1.0))


def simulate(settings: dict[str, str | int], args: argparse.Namespace) -> int:
    """Spread requested operations across a real-time window and commit each.

    Args:
        settings: Configured PostgreSQL connection parameters.
        args: Parsed simulation options; duration is in minutes.

    Returns:
        Zero after completion, or 130 after a graceful keyboard interruption.

    Raises:
        RuntimeError: If requested operations cannot use the available articles.
        psycopg.Error: If a database operation fails; prior commits remain.
    """
    rng = random.Random(args.seed)
    remaining = {
        "insert": args.inserts, "update": args.updates,
        "soft_delete": args.soft_deletes, "hard_delete": args.hard_deletes,
    }
    completed = dict.fromkeys(remaining, 0)
    total = sum(remaining.values())
    seconds = args.duration * 60
    started = time.monotonic()
    try:
        with psycopg.connect(**settings, connect_timeout=5, autocommit=True) as connection:
            active = connection.execute(
                "SELECT count(*) FROM public.articles WHERE deleted_at IS NULL"
            ).fetchone()[0]
            if remaining["soft_delete"] + remaining["hard_delete"] > active + remaining["insert"]:
                raise RuntimeError("Not enough active articles for the requested deletes.")
            if remaining["update"] and not active + remaining["insert"]:
                raise RuntimeError("Updates require an active article or a requested insert.")
            print(f"Simulating for {args.duration:g} minutes: {remaining}", flush=True)
            started = time.monotonic()
            for index in range(total):
                wait_until(started + (index + rng.random()) * seconds / total)
                eligible = [op for op, count in remaining.items() if count and (op == "insert" or active)]
                # Keep one active article while edits still need a target.
                if active == 1 and remaining["update"] and not remaining["insert"]:
                    eligible = [op for op in eligible if op not in ("soft_delete", "hard_delete")]
                operation = rng.choices(eligible, weights=[remaining[op] for op in eligible], k=1)[0]
                with connection.transaction():
                    connection.execute("SET LOCAL lock_timeout = '5s'")
                    connection.execute("SET LOCAL statement_timeout = '10s'")
                    article_id, timestamp = simulate_operation(
                        connection, rng, operation, args.author_id, completed["insert"] + 1,
                    )
                completed[operation] += 1
                remaining[operation] -= 1
                active += (operation == "insert") - (operation in ("soft_delete", "hard_delete"))
                print(f"{timestamp.isoformat()} {operation} id={article_id}", flush=True)
            wait_until(started + seconds)
        print("Simulation completed.", flush=True)
        return 0
    except KeyboardInterrupt:
        print("Simulation stopped; completed operations remain committed.", flush=True)
        return 130
    finally:
        print(f"Completed: {completed}; remaining: {remaining}", flush=True)
        print(f"Elapsed seconds: {time.monotonic() - started:.3f}", flush=True)


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
    simulation_command = commands.add_parser("simulate", help="Simulate live article changes.")
    simulation_command.add_argument("--duration", type=duration_minutes, required=True, help="Run duration in minutes; 60 means one hour.")
    simulation_command.add_argument("--inserts", type=nonnegative_int, default=60)
    simulation_command.add_argument("--updates", type=nonnegative_int, default=30)
    simulation_command.add_argument("--soft-deletes", type=nonnegative_int, default=10)
    simulation_command.add_argument("--hard-deletes", type=nonnegative_int, default=0,
                                    help="Permanently remove active articles (default: 0).")
    simulation_command.add_argument("--author-id", type=positive_int, default=1)
    simulation_command.add_argument("--seed", type=int)
    args = parser.parse_args(argv)
    if args.command == "simulate" and not (
        args.inserts + args.updates + args.soft_deletes + args.hard_deletes
    ):
        parser.error("simulate requires at least one operation")
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
        if args.command == "simulate":
            return simulate(settings, args)
        elif args.command == "check":
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
    except RuntimeError as error:
        logging.error("%s", error)
        return 1
    except psycopg.Error:
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
