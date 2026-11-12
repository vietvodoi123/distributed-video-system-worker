import argparse
import os
import sys
import time
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from cleaner import SpamCleaner


def main():
    parser = argparse.ArgumentParser(
        description="Batch clean chapters in PostgreSQL using SpamCleaner"
    )
    parser.add_argument(
        "--db-url",
        default=os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@host.docker.internal:5432/app_db",
        ),
        help="PostgreSQL connection URL",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Number of chapters per DB transaction batch (default: 500)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Maximum chapters to process (0 = all remaining uncleaned chapters)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Re-process chapters that already have cleaned_text",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.80,
        help="Confidence threshold for removing/stripping spam (default: 0.80)",
    )
    args = parser.parse_args()

    cleaner = SpamCleaner(full_threshold=args.threshold, tail_threshold=args.threshold)

    where_clause = "WHERE raw_text IS NOT NULL AND raw_text <> ''"
    if not args.overwrite:
        where_clause += " AND (cleaned_text IS NULL OR cleaned_text = '')"

    count_sql = f"SELECT COUNT(*) AS cnt FROM chapters {where_clause}"

    with psycopg.connect(args.db_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(count_sql)
            total_target = cur.fetchone()["cnt"]

    if args.limit > 0:
        total_target = min(total_target, args.limit)

    print(f"[*] Starting batch cleaner...")
    print(f"    Target chapters: {total_target:,}")
    print(f"    Batch size: {args.batch_size}")
    print(f"    Threshold: {args.threshold}")
    print(f"    Overwrite existing: {args.overwrite}\n")

    if total_target == 0:
        print("[+] No chapters to process. All done!")
        return

    processed = 0
    total_removed = 0
    total_stripped = 0
    t0 = time.perf_counter()

    select_sql = f"""
        SELECT id, raw_text
        FROM chapters
        {where_clause}
        ORDER BY id
        LIMIT %s
    """

    while processed < total_target:
        current_limit = min(args.batch_size, total_target - processed)
        with psycopg.connect(args.db_url, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(select_sql, (current_limit,))
                batch = cur.fetchall()

            if not batch:
                break

            updates = []
            for row in batch:
                res = cleaner.clean(row["raw_text"])
                updates.append((res["cleaned_text"], row["id"]))
                total_removed += len(res["removed_lines"])
                total_stripped += len(res["stripped_tails"])

            # Bulk update within one transaction
            with conn.cursor() as cur:
                cur.executemany(
                    "UPDATE chapters SET cleaned_text = %s WHERE id = %s",
                    updates,
                )
            conn.commit()

        processed += len(batch)
        elapsed = time.perf_counter() - t0
        speed = processed / max(elapsed, 0.001)
        remaining = (total_target - processed) / max(speed, 0.001)

        print(
            f"[{processed:6d}/{total_target:6d}] "
            f"({processed / total_target * 100:5.1f}%) | "
            f"Speed: {speed:5.1f} ch/s | "
            f"ETA: {remaining / 60:4.1f} min | "
            f"Spam removed: {total_removed} lines, {total_stripped} tails"
        )

    total_time = time.perf_counter() - t0
    print(f"\n[+] Finished processing {processed:,} chapters in {total_time:.1f}s!")
    print(f"    Avg speed: {processed / max(total_time, 0.001):.1f} chapters/second")
    print(f"    Total full lines removed: {total_removed:,}")
    print(f"    Total inline tails stripped: {total_stripped:,}")


if __name__ == "__main__":
    main()
