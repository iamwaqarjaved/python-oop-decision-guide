"""
procedural_right_examples.py
=============================
Module 7 companion: four problems where procedural code is clearly cleaner.

These examples deliberately avoid defining any classes. Each problem
is solved with functions (and occasionally module-level constants),
demonstrating that classes are not always the right abstraction.
"""

from __future__ import annotations

import csv
import io
import re
import sys
from pathlib import Path
from typing import TypedDict


# ============================================================
# Example 5 — CSV Sales Statistics
# ============================================================
# This is a pure pipeline: data in → numbers out.
# There is no state to maintain between calls, no identity to
# preserve, and no polymorphism to exploit. A SalesAnalyzer class
# here would be a container for three functions called once, in
# sequence — that is a module, not a class.
# ============================================================

class SaleRecord(TypedDict):
    product: str
    category: str
    units: int
    unit_price: float


def load_csv(source: str | io.StringIO) -> list[SaleRecord]:
    """Parse CSV rows into typed dicts. Returns an empty list on failure."""
    if isinstance(source, str):
        reader = csv.DictReader(open(source, newline="", encoding="utf-8"))
    else:
        reader = csv.DictReader(source)

    records: list[SaleRecord] = []
    for row in reader:
        try:
            records.append(SaleRecord(
                product=row["product"].strip(),
                category=row.get("category", "Uncategorized").strip(),
                units=int(row["units"]),
                unit_price=float(row["unit_price"]),
            ))
        except (KeyError, ValueError):
            continue   # skip malformed rows silently
    return records


def compute_summary(records: list[SaleRecord]) -> dict:
    """Derive aggregate statistics from a list of sale records."""
    if not records:
        return {}

    revenues = {r["product"]: r["units"] * r["unit_price"] for r in records}
    total = sum(revenues.values())
    avg_order = total / len(records)
    top_5 = sorted(revenues, key=revenues.__getitem__, reverse=True)[:5]

    return {
        "total_revenue": round(total, 2),
        "average_order_value": round(avg_order, 2),
        "record_count": len(records),
        "top_products": [(p, round(revenues[p], 2)) for p in top_5],
    }


def print_report(summary: dict) -> None:
    """Format and print the summary to stdout."""
    if not summary:
        print("No data to report.")
        return

    print("=" * 40)
    print("SALES SUMMARY")
    print("=" * 40)
    print(f"Records analysed : {summary['record_count']}")
    print(f"Total revenue    : ${summary['total_revenue']:,.2f}")
    print(f"Average order    : ${summary['average_order_value']:,.2f}")
    print("\nTop products by revenue:")
    for rank, (product, rev) in enumerate(summary["top_products"], 1):
        print(f"  {rank}. {product:<25} ${rev:,.2f}")


# --- demo ---
SAMPLE_CSV = """\
product,category,units,unit_price
Widget A,Hardware,40,30.00
Widget B,Hardware,25,34.00
Gadget X,Electronics,10,120.00
Gadget Y,Electronics,8,95.00
Doohickey,Misc,200,4.50
Thingamajig,Misc,55,12.99
"""

if __name__ == "__main__":
    source = io.StringIO(SAMPLE_CSV)
    records = load_csv(source)
    summary = compute_summary(records)
    print_report(summary)
    print()


# ============================================================
# Example 6 — CLI Argument Validation
# ============================================================
# Each validator is an independent, stateless transformation:
# string in, validated value or raised exception out.
# There is no shared state, no reason to instantiate anything.
# ============================================================

from datetime import date as Date

def parse_date(value: str) -> Date:
    """Parse YYYY-MM-DD; raise ValueError with a clear message on failure."""
    try:
        year, month, day = value.split("-")
        return Date(int(year), int(month), int(day))
    except (ValueError, AttributeError):
        raise ValueError(
            f"Invalid date {value!r}. Expected YYYY-MM-DD (e.g. 2024-03-15)."
        )


def parse_positive_int(value: str, name: str = "value") -> int:
    """Parse a string as a positive integer; raise ValueError otherwise."""
    try:
        n = int(value)
    except (ValueError, TypeError):
        raise ValueError(f"{name} must be an integer, got {value!r}")
    if n <= 0:
        raise ValueError(f"{name} must be positive, got {n}")
    return n


def resolve_existing_file(path_str: str) -> Path:
    """Resolve path string; raise FileNotFoundError if it doesn't exist."""
    path = Path(path_str).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.is_file():
        raise ValueError(f"Path is not a regular file: {path}")
    return path


def validate_email(value: str) -> str:
    """Very basic email format check; raises ValueError on failure."""
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    if not re.match(pattern, value):
        raise ValueError(f"Invalid email address: {value!r}")
    return value.lower()


# --- demo ---
if __name__ == "__main__":
    tests = [
        ("parse_date", parse_date, ["2024-06-15", "not-a-date", "2024-13-01"]),
        ("parse_positive_int", lambda v: parse_positive_int(v, "count"), ["10", "-3", "zero"]),
        ("validate_email", validate_email, ["user@example.com", "bad-email", "@nodomain"]),
    ]
    for name, fn, cases in tests:
        print(f"\n--- {name} ---")
        for case in cases:
            try:
                print(f"  {case!r:20} → {fn(case)}")
            except (ValueError, FileNotFoundError) as e:
                print(f"  {case!r:20} ✗ {e}")


# ============================================================
# Example 7 — String Normalization Pipeline
# ============================================================
# A chain of pure, composable transformations. Each step takes a
# string and returns a string. No state, no identity, no class needed.
# ============================================================

def strip_whitespace(s: str) -> str:
    return " ".join(s.split())


def to_title_case(s: str) -> str:
    # Don't capitalize articles/prepositions mid-title
    LOWERCASE_WORDS = {"a", "an", "the", "and", "but", "or", "for",
                       "in", "on", "at", "to", "of", "with"}
    words = s.split()
    result = []
    for i, word in enumerate(words):
        if i == 0 or word.lower() not in LOWERCASE_WORDS:
            result.append(word.capitalize())
        else:
            result.append(word.lower())
    return " ".join(result)


def remove_special_chars(s: str) -> str:
    """Keep letters, digits, spaces, hyphens, and apostrophes."""
    return re.sub(r"[^\w\s\-']", "", s)


def truncate(s: str, limit: int = 80) -> str:
    if len(s) <= limit:
        return s
    # truncate to the last full word within limit
    truncated = s[:limit].rsplit(" ", 1)[0]
    return truncated + "…"


def normalize_title(raw: str) -> str:
    """Full normalization pipeline: strip → remove specials → title-case → truncate."""
    return truncate(to_title_case(remove_special_chars(strip_whitespace(raw))))


# --- demo ---
if __name__ == "__main__":
    samples = [
        "  hello   WORLD  ",
        "the quick brown fox jumps over the lazy dog — a tale of canines",
        "product!!! name ### with $pecial ch@racters & stuff",
        "A" * 100,
    ]
    print("\n--- normalize_title ---")
    for s in samples:
        print(f"  IN : {s[:50]!r}")
        print(f"  OUT: {normalize_title(s)!r}")
        print()


# ============================================================
# Example 8 — One-Off Data Migration Script
# ============================================================
# This script runs once, top to bottom. It is a script.
# A class wrapper adds nothing but ceremony: a __init__ that takes
# no interesting arguments, a single run() method, and a
# Migration().run() call at the bottom.
# ============================================================

# Simulated "legacy" and "new" databases as in-memory dicts
_LEGACY_DB: list[dict] = [
    {"id": 1, "full_name": "Alice Smith", "email_address": "alice@example.com", "admin": "Y"},
    {"id": 2, "full_name": "Bob Jones",   "email_address": "bob@example.com",   "admin": "N"},
    {"id": 3, "full_name": "Carol White", "email_address": "carol@example.com", "admin": "Y"},
]
_NEW_DB: list[dict] = []


def fetch_legacy_users(db: list[dict]) -> list[dict]:
    """Read all records from the legacy schema."""
    return list(db)


def transform_user(record: dict) -> dict:
    """Map from legacy schema to new schema."""
    first, *rest = record["full_name"].split(" ", 1)
    return {
        "id": record["id"],
        "first_name": first,
        "last_name": rest[0] if rest else "",
        "email": record["email_address"].lower(),
        "is_admin": record["admin"] == "Y",
    }


def insert_users(db: list[dict], records: list[dict]) -> None:
    """Write transformed records to the new store."""
    db.extend(records)


def log_migration(count: int, errors: int) -> None:
    status = "SUCCESS" if errors == 0 else f"PARTIAL ({errors} errors)"
    print(f"[Migration] {status} — {count} records migrated.")


# --- demo (stands in for __main__ guard in a real script) ---
if __name__ == "__main__":
    legacy_records = fetch_legacy_users(_LEGACY_DB)
    errors = 0
    new_records = []
    for r in legacy_records:
        try:
            new_records.append(transform_user(r))
        except Exception as e:
            print(f"  Skipping record {r.get('id')}: {e}")
            errors += 1

    insert_users(_NEW_DB, new_records)
    log_migration(len(new_records), errors)

    print("\nNew DB contents:")
    for user in _NEW_DB:
        print(f"  {user}")
