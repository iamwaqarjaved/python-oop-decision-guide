"""
oop_right_examples.py
=====================
Module 7 companion: four problems where OOP is clearly the right choice.

Run each section independently or import as needed.
"""

from __future__ import annotations

import time
import threading
from collections import deque
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Iterator
import contextlib


# ============================================================
# Example 1 — Rate-Limited API Client
# ============================================================
# State: request timestamps, session, base URL
# Behavior: get/post, enforcing a per-minute cap
# Multiple instances: yes — different services, different limits
# Long-lived: yes — shared across the application lifetime
# ============================================================

class RateLimitedClient:
    """HTTP client that enforces a requests-per-minute ceiling.

    The rate limit state (timestamps of recent requests) is inseparable
    from the behavior (throttling before each request). This is the
    clearest signal that a class is warranted: you cannot write
    stateless functions that share the same rate-limit budget.
    """

    def __init__(self, base_url: str, rpm_limit: int = 60) -> None:
        self.base_url = base_url.rstrip("/")
        self._rpm_limit = rpm_limit
        self._timestamps: deque[float] = deque()
        self._lock = threading.Lock()

    # ---- public API ------------------------------------------------

    def get(self, path: str, **kwargs) -> dict:
        self._throttle()
        url = f"{self.base_url}{path}"
        # In production, use requests.get(url, **kwargs).json()
        print(f"GET {url}")
        return {"status": "ok", "path": path}

    def post(self, path: str, data: dict, **kwargs) -> dict:
        self._throttle()
        url = f"{self.base_url}{path}"
        print(f"POST {url} data={data}")
        return {"status": "created"}

    # ---- internal --------------------------------------------------

    def _throttle(self) -> None:
        """Block until making a request would not exceed rpm_limit."""
        with self._lock:
            now = time.monotonic()
            window_start = now - 60.0
            # drop timestamps older than one minute
            while self._timestamps and self._timestamps[0] < window_start:
                self._timestamps.popleft()
            if len(self._timestamps) >= self._rpm_limit:
                sleep_for = 60.0 - (now - self._timestamps[0])
                time.sleep(max(0, sleep_for))
            self._timestamps.append(time.monotonic())

    def __repr__(self) -> str:
        return f"RateLimitedClient(base_url={self.base_url!r}, rpm={self._rpm_limit})"


# --- demo ---
if __name__ == "__main__":
    client = RateLimitedClient("https://api.example.com", rpm_limit=5)
    print(client.get("/users/42"))
    print(client.post("/orders", {"item": "widget", "qty": 3}))


# ============================================================
# Example 2 — Game Character
# ============================================================
# State: health, mana, inventory, level — all evolve at runtime
# Behavior: attack, heal, pick_up, level_up — inseparable from state
# Multiple instances: yes — one per entity on the map
# ============================================================

@dataclass
class Item:
    name: str
    weight: float
    value: int


class Character:
    """A game entity whose state evolves over many turns.

    Each Character is an independent object with its own health,
    mana, inventory, and level. The behavior (attack, heal, level_up)
    reads and mutates that specific instance's state. There is no
    clean way to express this as pure functions — the state *is* the
    character's identity.
    """

    def __init__(self, name: str, health: int = 100, mana: int = 50) -> None:
        self.name = name
        self.health = health
        self.max_health = health
        self.mana = mana
        self.max_mana = mana
        self.level = 1
        self.xp = 0
        self.inventory: list[Item] = []

    # ---- combat ----------------------------------------------------

    def attack(self, target: "Character", damage: int) -> None:
        actual = max(0, damage)
        target.health = max(0, target.health - actual)
        print(f"{self.name} hits {target.name} for {actual} damage "
              f"({target.health}/{target.max_health} HP remaining)")
        if target.health == 0:
            print(f"{target.name} has been defeated!")
            self.gain_xp(target.level * 20)

    def heal(self, amount: int) -> None:
        restored = min(amount, self.max_health - self.health)
        self.health += restored
        print(f"{self.name} heals {restored} HP ({self.health}/{self.max_health})")

    # ---- inventory -------------------------------------------------

    def pick_up(self, item: Item) -> None:
        self.inventory.append(item)
        print(f"{self.name} picks up {item.name}")

    # ---- progression -----------------------------------------------

    def gain_xp(self, amount: int) -> None:
        self.xp += amount
        threshold = self.level * 100
        if self.xp >= threshold:
            self.xp -= threshold
            self._level_up()

    def _level_up(self) -> None:
        self.level += 1
        bonus_hp = 20
        bonus_mana = 10
        self.max_health += bonus_hp
        self.health = self.max_health       # full heal on level-up
        self.max_mana += bonus_mana
        self.mana = self.max_mana
        print(f"*** {self.name} reached level {self.level}! ***")

    def __repr__(self) -> str:
        return (f"Character({self.name!r}, HP={self.health}/{self.max_health}, "
                f"MP={self.mana}/{self.max_mana}, lvl={self.level})")


# --- demo ---
if __name__ == "__main__":
    hero = Character("Aria", health=100, mana=50)
    goblin = Character("Goblin", health=30, mana=0)

    hero.attack(goblin, damage=15)
    hero.attack(goblin, damage=20)
    print(hero)


# ============================================================
# Example 3 — Report Exporter (Polymorphism)
# ============================================================
# State: format-specific config (template, delimiter)
# Behavior: export() — same call site, different implementation
# Polymorphism: eliminates type-dispatch at every call site
# ============================================================

class ReportExporter(ABC):
    """Abstract base — defines the interface, not the implementation.

    Every call site can do `exporter.export(data, path)` without
    knowing or caring which concrete format is in use. The type
    decision happens once, at construction time.
    """

    @abstractmethod
    def export(self, data: list[dict], path: str) -> None: ...

    def _validate_data(self, data: list[dict]) -> None:
        if not data:
            raise ValueError("Cannot export empty dataset")


class CSVExporter(ReportExporter):
    def __init__(self, delimiter: str = ",") -> None:
        self.delimiter = delimiter

    def export(self, data: list[dict], path: str) -> None:
        self._validate_data(data)
        headers = list(data[0].keys())
        lines = [self.delimiter.join(headers)]
        for row in data:
            lines.append(self.delimiter.join(str(row[h]) for h in headers))
        content = "\n".join(lines)
        print(f"[CSV] Writing {len(data)} rows to {path}")
        print(content[:200])   # truncated for demo


class JSONExporter(ReportExporter):
    def __init__(self, indent: int = 2) -> None:
        self.indent = indent

    def export(self, data: list[dict], path: str) -> None:
        import json
        self._validate_data(data)
        content = json.dumps(data, indent=self.indent)
        print(f"[JSON] Writing {len(data)} records to {path}")
        print(content[:200])


class MarkdownExporter(ReportExporter):
    def export(self, data: list[dict], path: str) -> None:
        self._validate_data(data)
        headers = list(data[0].keys())
        separator = "| " + " | ".join("---" for _ in headers) + " |"
        header_row = "| " + " | ".join(headers) + " |"
        rows = ["| " + " | ".join(str(row[h]) for h in headers) + " |"
                for row in data]
        print(f"[Markdown] Writing to {path}")
        print("\n".join([header_row, separator] + rows[:5]))


# --- demo: call site never changes regardless of exporter ---
if __name__ == "__main__":
    sample = [
        {"product": "Widget A", "revenue": 1200, "units": 40},
        {"product": "Widget B", "revenue": 850, "units": 25},
    ]

    for exporter in [CSVExporter(), JSONExporter(), MarkdownExporter()]:
        exporter.export(sample, f"report.{type(exporter).__name__.lower()}")
        print()


# ============================================================
# Example 4 — Connection Pool
# ============================================================
# State: available connections, borrowed connections, size limits
# Behavior: acquire/release with blocking and cleanup
# Long-lived: entire application lifetime
# Multiple instances: possibly (separate pools for read/write replicas)
# ============================================================

class FakeConnection:
    """Stand-in for a real database connection."""
    _counter = 0

    def __init__(self) -> None:
        FakeConnection._counter += 1
        self.id = FakeConnection._counter
        self.closed = False

    def execute(self, sql: str) -> str:
        if self.closed:
            raise RuntimeError("Connection is closed")
        return f"[conn-{self.id}] executed: {sql}"

    def close(self) -> None:
        self.closed = True


class ConnectionPool:
    """Manages a pool of reusable database connections.

    The pool tracks which connections are available and which are
    in use. Without an object to hold this shared mutable state,
    every caller would need to coordinate independently — which is
    exactly the problem a pool exists to solve.
    """

    def __init__(self, min_size: int = 2, max_size: int = 10) -> None:
        self._min_size = min_size
        self._max_size = max_size
        self._available: list[FakeConnection] = []
        self._in_use: set[FakeConnection] = set()
        self._lock = threading.Lock()

        # pre-warm minimum connections
        for _ in range(min_size):
            self._available.append(FakeConnection())

    @contextlib.contextmanager
    def acquire(self) -> Iterator[FakeConnection]:
        conn = self._checkout()
        try:
            yield conn
        finally:
            self._checkin(conn)

    def _checkout(self) -> FakeConnection:
        with self._lock:
            if self._available:
                conn = self._available.pop()
            elif len(self._in_use) < self._max_size:
                conn = FakeConnection()
                print(f"[pool] Created new connection (total: {self.size})")
            else:
                raise RuntimeError("Connection pool exhausted")
            self._in_use.add(conn)
            return conn

    def _checkin(self, conn: FakeConnection) -> None:
        with self._lock:
            self._in_use.discard(conn)
            if not conn.closed:
                self._available.append(conn)

    def close_all(self) -> None:
        with self._lock:
            for conn in self._available + list(self._in_use):
                conn.close()
            self._available.clear()
            self._in_use.clear()

    @property
    def size(self) -> int:
        return len(self._available) + len(self._in_use)

    def __repr__(self) -> str:
        return (f"ConnectionPool(available={len(self._available)}, "
                f"in_use={len(self._in_use)}, max={self._max_size})")


# --- demo ---
if __name__ == "__main__":
    pool = ConnectionPool(min_size=2, max_size=5)
    print(pool)

    with pool.acquire() as conn:
        print(conn.execute("SELECT count(*) FROM users"))

    with pool.acquire() as c1, pool.acquire() as c2:
        print(conn.execute("SELECT 1"))
        print(c2.execute("SELECT 2"))

    pool.close_all()
    print("Pool closed.")
