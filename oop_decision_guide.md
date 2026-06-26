# Module 7: When to Use OOP in Python — A Decision Guide

> *"Python is not Java. It is also not Haskell. It is a pragmatic multi-paradigm language, and using the wrong paradigm for the job is a form of technical debt."*

---

## Table of Contents

1. [The Core Question](#1-the-core-question)
2. [Decision Criteria: When OOP Pays Off](#2-decision-criteria-when-oop-pays-off)
3. [Decision Criteria: When OOP Gets in the Way](#3-decision-criteria-when-oop-gets-in-the-way)
4. [Worked Examples: OOP is Clearly Right](#4-worked-examples-oop-is-clearly-right)
5. [Worked Examples: Procedural is Clearly Cleaner](#5-worked-examples-procedural-is-clearly-cleaner)
6. [Worked Examples: It Depends](#6-worked-examples-it-depends)
7. [The @dataclass Discussion](#7-the-dataclass-discussion)
8. [Encapsulation in Python](#8-encapsulation-in-python)
9. [Inheritance vs. Composition](#9-inheritance-vs-composition)
10. [Anti-Pattern Register](#10-anti-pattern-register)
11. [Quick-Reference Decision Flowchart](#11-quick-reference-decision-flowchart)
12. [Summary](#12-summary)

---

## 1. The Core Question

Before writing `class`, ask yourself one question:

**Does this thing have *both* state that changes over time *and* behavior that operates on that state?**

If the answer is no — if you only have data, or only have logic — a class is probably the wrong tool. A function transforms input into output. A dict or dataclass holds named data. A module groups related functions. Classes are for *objects*: things that know things *and* do things, whose internal state evolves as the program runs.

The multi-paradigm nature of Python means you pay a real cost for every class you write: more lines to read, an indirection layer between the caller and the logic, and a namespace decision (method or function?). That cost has to be justified. The sections below show you when it is.

---

## 2. Decision Criteria: When OOP Pays Off

### 2.1 State and Behavior Travel Together

The clearest sign a class is warranted: you keep passing the same bundle of data into related functions.

```python
# Smell: data and behavior keep showing up together, but separated
def connect(host, port, timeout):   ...
def send(host, port, timeout, msg): ...
def close(host, port):              ...
```

When that happens, the data *wants* to be the object and the functions *want* to be methods:

```python
class Connection:
    def __init__(self, host, port, timeout=30): ...
    def send(self, msg): ...
    def close(self): ...
```

**Rule of thumb:** If the same 3+ variables appear in the signature of 3+ related functions, those variables belong in `__init__`.

---

### 2.2 You Need Multiple Instances of the Same Shape

Functions are singletons. You cannot have two independent copies of a function's local state running simultaneously. If you need ten independent socket connections, ten open files, or ten game characters — each with its own internal state — you need instances.

---

### 2.3 Polymorphism Simplifies a Decision Tree

When you find yourself writing `if type == "pdf": ... elif type == "docx": ...` in multiple places, polymorphism is trying to emerge. A `Document` base class with a `.render()` method and `PDF` / `Docx` subclasses lets call sites become a single `doc.render()` — the type decision moves to object-construction time and disappears from business logic.

---

### 2.4 Long-Lived Objects That Accumulate State

Short-lived transformations (parse this string, compute this value) are well-served by functions. Long-lived objects — an HTTP session, a database connection pool, a game entity that gains experience over hundreds of turns — need somewhere to keep state between calls. A class instance is that place.

---

### 2.5 You're Modeling a Domain with Identity

If you're building something where individual "things" have an identity that persists across operations — a `User`, a `BankAccount`, a `ShoppingCart` — classes map naturally onto that mental model. The object is the domain entity.

---

## 3. Decision Criteria: When OOP Gets in the Way

### 3.1 One-Off Scripts

A 40-line script that downloads a file, parses it, and prints a summary has no reason to define a class. It will never be instantiated twice. There is no state to manage. Writing `class Main:` with a single `run()` method and then calling `Main().run()` is pure ceremony.

---

### 3.2 Pure Transformations (Stateless Logic)

If a function takes input, computes output, and has no side effects, it is already the right abstraction. `parse_date(s)`, `normalize_phone(number)`, `calculate_tax(amount, rate)` — these are functions. Wrapping them in a class adds nothing.

---

### 3.3 Configuration and Constant Data

Data that doesn't change and has no behavior is not an object. A module-level dict or a `@dataclass(frozen=True)` communicates your intent better than a class with only `__init__` and no methods.

---

### 3.4 When a Module Already Provides the Namespace

Python modules *are* namespaces. `math.sin`, `os.path.join`, `json.loads` — these are functions living in modules, not methods on objects. If you're grouping related utilities with no shared state, a module is correct and a class is extra.

---

### 3.5 Simple Pipelines

Data-in, data-out pipelines — ETL steps, CLI filters, functional transformations — are usually cleaner as a chain of functions or a generator pipeline. Classes introduce mutable state where none is needed.

---

## 4. Worked Examples: OOP is Clearly Right

*See companion files: `oop_right_examples.py`*

### Example 1 — Rate-Limited API Client

**Problem:** You need to talk to a third-party REST API that enforces 100 requests/minute. Multiple parts of your application make requests, and all of them must share the same rate-limit budget.

**Why OOP:** Shared mutable state (request count, timestamp window, the underlying HTTP session) is the defining trait of this problem. The alternative — a module-level counter and a collection of functions — is just a class without the syntax, and a worse one.

```python
# See oop_right_examples.py → RateLimitedClient
client = RateLimitedClient(base_url="https://api.example.com", rpm_limit=100)
data = client.get("/users/42")   # rate limit tracked internally
```

**The tell:** You cannot write this cleanly as a pure function because the function would need to remember things between calls.

---

### Example 2 — Game Character

**Problem:** A text RPG where characters have health, mana, and an inventory. They can take damage, cast spells, pick up items, and die.

**Why OOP:** Each character is an independent entity with its own evolving state. You'll create many of them. Their behavior (`.attack()`, `.heal()`, `.pick_up()`) is inseparable from their state (`.health`, `.inventory`).

```python
# See oop_right_examples.py → Character
hero = Character("Aria", health=100, mana=50)
enemy = Character("Goblin", health=30, mana=0)
hero.attack(enemy, damage=15)
```

---

### Example 3 — File Format Polymorphism

**Problem:** Your application exports reports to PDF, CSV, and HTML. The export logic differs per format, but the call site just wants `report.export(path)`.

**Why OOP:** This is the textbook polymorphism case. A `ReportExporter` base class with concrete subclasses eliminates type-dispatch code from every call site.

```python
# See oop_right_examples.py → ReportExporter hierarchy
exporter = PDFExporter(template="modern")
exporter.export(report_data, path="q3_report.pdf")
```

---

### Example 4 — Connection Pool

**Problem:** A web server needs to reuse database connections across thousands of requests, checking connections in and out.

**Why OOP:** The pool has persistent state (available connections, borrowed connections, pool size limits) and behavior that mutates that state over its entire lifetime. This is structurally impossible to express cleanly without an object.

```python
# See oop_right_examples.py → ConnectionPool
pool = ConnectionPool(dsn="postgresql://...", min_size=5, max_size=20)
with pool.acquire() as conn:
    conn.execute("SELECT 1")
```

---

## 5. Worked Examples: Procedural is Clearly Cleaner

*See companion files: `procedural_right_examples.py`*

### Example 5 — CSV Statistics

**Problem:** Read a CSV file of sales records, compute total revenue, average order value, and top 5 products.

**Why Procedural:** This is a pure pipeline. Data goes in, numbers come out. There is no state to maintain between calls, no identity to preserve, no polymorphism to exploit.

```python
# See procedural_right_examples.py
records = load_csv("sales.csv")
summary = compute_summary(records)
print_report(summary)
```

A `SalesAnalyzer` class here would be a container for three functions that are only ever called once, in sequence. That is a module, not a class.

---

### Example 6 — CLI Argument Validation

**Problem:** A CLI tool that validates user-supplied arguments (date format, positive integer, valid file path).

**Why Procedural:** Each validator is an independent, stateless transformation: string in, validated value or error out. There is no shared state between them, no reason to instantiate anything.

```python
# See procedural_right_examples.py
date = parse_date(args.start)        # raises ValueError if invalid
count = parse_positive_int(args.n)
path = resolve_existing_file(args.input)
```

---

### Example 7 — String Normalization Pipeline

**Problem:** Clean up user-submitted product titles: strip whitespace, title-case, remove special characters, truncate to 80 chars.

**Why Procedural:** A function composition or a simple pipeline. The transformations are stateless and composable. A `TitleNormalizer` class would just be a wrapper around one function.

```python
# See procedural_right_examples.py
def normalize_title(raw: str) -> str:
    return truncate(remove_special(title_case(raw.strip())), limit=80)
```

---

### Example 8 — One-Off Data Migration Script

**Problem:** A script run once to migrate user records from a legacy schema to a new one.

**Why Procedural:** This script runs once, from top to bottom. Wrapping it in a class adds a `self` parameter to every function and a `Migration().run()` call at the bottom, with no benefit. When the problem is a script, write a script.

```python
# See procedural_right_examples.py
if __name__ == "__main__":
    old_records = fetch_legacy_users(old_db)
    new_records = [transform_user(r) for r in old_records]
    insert_users(new_db, new_records)
    print(f"Migrated {len(new_records)} users.")
```

---

## 6. Worked Examples: It Depends

*See companion files: `it_depends_examples.py`*

### Example 9 — Configuration Loader

**Problem:** Load configuration from a YAML file, provide defaults, and allow other modules to read config values.

**The tension:** Pure configuration data suggests a dict or `@dataclass(frozen=True)`. But if you need lazy loading, environment variable overrides, reload-on-signal, or caching — behavior appears, and a class starts to make sense.

**Procedural version** (simpler, fine for small projects):
```python
CONFIG = load_config("config.yaml")   # returns a dict with defaults merged
```

**OOP version** (justified when behavior accumulates):
```python
config = Config("config.yaml")
config.reload()                         # re-reads from disk
debug = config.get("app.debug", False)  # dotted key access with default
```

**Decision axis:** Does this config object *do* things beyond store-and-retrieve? If yes, class. If no, dict or frozen dataclass.

---

### Example 10 — HTTP Request Handler

**Problem:** Process an incoming HTTP request: parse headers, route to a handler, build a response.

**The tension:** Each individual operation (parse headers, match route, serialize response) is a pure function. But the *request lifecycle* — the thing that accumulates parsed state as it passes through middleware — benefits from an object.

**Procedural version** (fine for simple frameworks or scripts):
```python
def handle(raw_request: bytes) -> bytes:
    request = parse_request(raw_request)
    handler = route(request.path, request.method)
    response = handler(request)
    return serialize_response(response)
```

**OOP version** (justified when middleware, hooks, or per-request state accumulate):
```python
class Request:
    def __init__(self, raw): ...
    @property
    def json(self): ...          # lazy-parsed, cached
    def get_header(self, name): ...
```

**Decision axis:** Is request state shared across many call sites *within a single request's lifetime*? If so, the request object earns its keep by avoiding parameter-passing spaghetti.

---

## 7. The @dataclass Discussion

### When `@dataclass` Replaces a Hand-Written `__init__` (Almost Always, for Record-Like Classes)

If your class is primarily a named container for typed fields — a record, a value object, a DTO — `@dataclass` replaces the boilerplate `__init__`, `__repr__`, and `__eq__` with a single decorator:

```python
# Before: hand-written boilerplate
class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    def __repr__(self):
        return f"Point(x={self.x}, y={self.y})"
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

# After: @dataclass
from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float
```

For immutable records, add `frozen=True`:

```python
@dataclass(frozen=True)
class Color:
    r: int
    g: int
    b: int
```

`frozen=True` makes instances hashable (usable as dict keys or in sets) and signals to readers that this is a value object, not a mutable entity.

For ordered comparison (sorting by fields), add `order=True`:

```python
@dataclass(order=True)
class Version:
    major: int
    minor: int
    patch: int
```

### When `@dataclass` Doesn't Work: Custom Validation in `__init__`

`@dataclass` generates `__init__` for you. If you need to *validate or transform* arguments before storing them, you have two options:

**Option A — `__post_init__`:** Runs after the generated `__init__` assigns fields. Good for validation that raises on bad input.

```python
@dataclass
class PositivePoint:
    x: float
    y: float

    def __post_init__(self):
        if self.x < 0 or self.y < 0:
            raise ValueError(f"Coordinates must be non-negative, got ({self.x}, {self.y})")
```

**Option B — Hand-written `__init__`:** Necessary when you need to transform the incoming data (coerce types, derive computed fields at init time from values that should *not* be stored as fields).

```python
class BoundingBox:
    def __init__(self, points: list[tuple[float, float]]):
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        self.min_x = min(xs)
        self.max_x = max(xs)
        self.min_y = min(ys)
        self.max_y = max(ys)
        # storing 'points' itself would be redundant
```

**Decision tree:**

```
Does your class primarily hold named data?
├── YES → use @dataclass
│   ├── Need validation? → add __post_init__
│   ├── Need immutability? → frozen=True
│   └── Need ordering? → order=True
└── NO (complex init logic, transformation, non-trivial behavior)
    └── write __init__ by hand
```

### `@dataclass` vs. `typing.NamedTuple`

Both produce immutable record-like objects. The differences:

| | `@dataclass(frozen=True)` | `NamedTuple` |
|---|---|---|
| Mutable version available | Yes (drop `frozen`) | No |
| Inheritable | Yes | Limited |
| `isinstance` checks | Works normally | Works normally |
| Unpacking (`x, y = point`) | No | Yes |
| Dict conversion | `dataclasses.asdict()` | `point._asdict()` |

Use `NamedTuple` when you want positional unpacking or need to pass the object to code that expects a tuple. Use `@dataclass` for everything else.

---

## 8. Encapsulation in Python

### "We're All Consenting Adults"

Python's encapsulation model is cultural, not enforced. The language trusts developers to respect conventions rather than using access-control keywords like Java's `private` or `protected`. This is a deliberate design choice that prioritizes pragmatism over ceremony.

The convention is the **single leading underscore** (`_name`):

```python
class Cache:
    def __init__(self):
        self._store = {}     # internal implementation detail
        self._hits = 0       # not part of the public API

    def get(self, key):
        result = self._store.get(key)
        if result is not None:
            self._hits += 1
        return result
```

A single leading underscore is a **signal to other developers**: "this is an implementation detail; you can access it if you truly need to (testing, debugging, emergency), but don't depend on it in normal usage." It is not enforced — Python will not stop you from reading `cache._store` — but it clearly communicates intent.

**This is sufficient for almost all production Python code.**

### Double Underscore Name Mangling (`__name`) — Almost Never Appropriate

Double leading underscores trigger Python's name mangling: `__attr` on class `Foo` becomes `_Foo__attr` in the bytecode. This was designed for a narrow purpose: **preventing accidental attribute collisions in deep inheritance hierarchies**. Specifically, it protects a base class's internal attributes from being unintentionally overridden by subclasses.

```python
class Base:
    def __init__(self):
        self.__state = "base"    # stored as _Base__state

class Child(Base):
    def __init__(self):
        super().__init__()
        self.__state = "child"   # stored as _Child__state — no collision
```

Outside of that specific scenario — a library base class that ships to third-party developers who will subclass it — double underscores are almost always the wrong choice. They make debugging harder (the attribute name you see in code isn't the name stored on the object), they break straightforward introspection, and they signal a level of "keep out" that is contrary to Python's philosophy.

**Practical guidance:**

- Public API → no underscore
- Internal implementation detail → single underscore (`_name`)
- Base class protecting attributes from subclass collision → double underscore (`__name`)
- Simulating Java-style `private` → **do not use `__name`; use `_name` instead**

---

## 9. Inheritance vs. Composition

### The Modern Python Community Preference

The contemporary Python community — and the broader software engineering community — has largely settled on a simple heuristic:

> **Favor composition over inheritance.**

This doesn't mean inheritance is wrong. It means that inheritance is a *powerful* tool with a *narrow* valid use case, and it is routinely overused by developers coming from Java-heavy backgrounds.

### When Inheritance Is Appropriate: True Is-A Relationships

Inheritance is correct when you can honestly complete this sentence without hedging:

> "A `[Subclass]` *is a* `[Superclass]`."

- A `Dog` *is an* `Animal` ✓
- A `SavingsAccount` *is a* `BankAccount` ✓
- A `PDFExporter` *is a* `ReportExporter` ✓ (when the base defines the export interface)

The Liskov Substitution Principle gives you a concrete test: **every place the base class is used, you must be able to substitute the subclass without breaking anything.** If you can't, the inheritance relationship is wrong.

```python
# Legitimate inheritance: PDFExporter IS-A ReportExporter
class ReportExporter:
    def export(self, data, path: str) -> None:
        raise NotImplementedError

class PDFExporter(ReportExporter):
    def export(self, data, path: str) -> None:
        # concrete PDF-writing logic
        ...
```

### When to Compose Instead

When the relationship is "has-a" or "uses-a" or "is implemented in terms of," use composition:

```python
# Wrong: Employee IS-NOT-A Database
class Employee(Database):          # BAD: inheriting for reuse
    def save(self):
        self.execute("INSERT ...")

# Right: Employee HAS-A database connection
class Employee:
    def __init__(self, db: Database):
        self._db = db              # GOOD: compose the capability in

    def save(self):
        self._db.execute("INSERT ...")
```

Composition produces more flexible code: you can swap `self._db` for a test double, a different database driver, or an in-memory store without touching `Employee`. With inheritance, you're locked in.

### The Warning Against Deep Class Hierarchies

Each additional level of inheritance adds to the cognitive load of understanding any single class. When you read a method on a class three levels deep, you must mentally trace through three `__init__` calls, three `super()` chains, and the MRO to understand what `self` actually looks like at runtime.

**A hierarchy more than two levels deep is a design smell.** If you find yourself writing `class C(B)` where `B(A)` and `A(Base)`, ask whether composition would be cleaner.

Mixins — small, focused classes that add a single capability — are a partial exception, but even mixin-heavy code can become difficult to reason about. Prefer explicit composition when the team isn't deeply familiar with MRO.

```python
# Three-level hierarchy → fragile, hard to follow
class Vehicle: ...
class MotorVehicle(Vehicle): ...
class Car(MotorVehicle): ...        # already deep
class ElectricCar(Car): ...         # now we're in trouble

# Composition alternative
class ElectricCar:
    def __init__(self):
        self.drivetrain = ElectricDrivetrain()
        self.body = CarBody()
        self.battery = Battery(capacity_kwh=75)
```

---

## 10. Anti-Pattern Register

### Anti-Pattern 1: Java-in-Python — Excessive Getters and Setters

Java enforces encapsulation through access modifiers (`private int x`) and requires getters/setters (`getX()`, `setX()`) to provide controlled access. In Python, where attributes are public by convention, wrapping every attribute in a getter/setter pair is pure noise.

```python
# ANTI-PATTERN: Java transplanted into Python
class Rectangle:
    def __init__(self, width, height):
        self._width = width
        self._height = height

    def get_width(self):
        return self._width

    def set_width(self, value):
        self._width = value

    def get_height(self):
        return self._height

    def set_height(self, value):
        self._height = value
```

The Python way: start with a plain attribute. Add `@property` only when you need to add logic (validation, caching, side effects) at access time.

```python
# IDIOMATIC: plain attributes until behavior is needed
class Rectangle:
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height

    @property
    def area(self) -> float:
        return self.width * self.height

# Add @property only when validation is required
class SafeRectangle:
    def __init__(self, width: float, height: float):
        self.width = width     # setter called, triggers validation
        self.height = height

    @property
    def width(self) -> float:
        return self._width

    @width.setter
    def width(self, value: float) -> None:
        if value <= 0:
            raise ValueError(f"Width must be positive, got {value}")
        self._width = value
```

---

### Anti-Pattern 2: Unnecessary Class Hierarchies

Building hierarchies before the use cases exist produces abstractions that don't quite fit anything:

```python
# ANTI-PATTERN: hierarchy built speculatively
class BaseProcessor:
    def process(self, data): raise NotImplementedError

class TextProcessor(BaseProcessor):
    def process(self, data): ...

class NumberProcessor(BaseProcessor):
    def process(self, data): ...
```

If you have exactly one caller that calls `.process()` on one concrete type, the base class serves no purpose. Add abstractions when you have the second or third concrete case — not before.

---

### Anti-Pattern 3: Classes That Should Be Modules

A class with only static or class methods, no instance state, and no instantiation is a module disguised as a class:

```python
# ANTI-PATTERN: a module wearing a class costume
class MathUtils:
    @staticmethod
    def add(a, b): return a + b

    @staticmethod
    def multiply(a, b): return a * b

    @staticmethod
    def clamp(value, lo, hi): return max(lo, min(hi, value))

MathUtils.add(1, 2)   # caller has to write this
```

This forces callers to write `MathUtils.add(1, 2)` instead of just `add(1, 2)`, for no benefit. A module provides the namespace without the class overhead:

```python
# IDIOMATIC: math_utils.py
def add(a, b): return a + b
def multiply(a, b): return a * b
def clamp(value, lo, hi): return max(lo, min(hi, value))

# caller:
from math_utils import add, clamp
```

---

### Anti-Pattern 4: `__init__` That Does Real Work

`__init__` should initialize state. It should not make network calls, read files, compute expensive results, or raise domain-specific exceptions for anything other than invalid arguments. When `__init__` does real work, the object is difficult to test, mock, or construct in a partially-initialized state.

```python
# ANTI-PATTERN: constructor that fetches data
class UserProfile:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.data = requests.get(f"/api/users/{user_id}").json()  # WRONG

# IDIOMATIC: separate construction from loading
class UserProfile:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.data = None

    @classmethod
    def load(cls, user_id: int) -> "UserProfile":
        profile = cls(user_id)
        profile.data = requests.get(f"/api/users/{user_id}").json()
        return profile
```

The `@classmethod` factory pattern makes loading explicit, testable, and optional.

---

### Anti-Pattern 5: Subclassing for Code Reuse Alone

Inheriting from a class to get access to its methods — without an is-a relationship — creates brittle coupling. If the base class changes, your subclass breaks, even though you had no conceptual relationship with it.

```python
# ANTI-PATTERN: inheriting for convenience
class MyList(list):
    def sum_all(self):
        return sum(self)    # could just as easily be a function

# IDIOMATIC: function or composition
def sum_all(items):
    return sum(items)
```

Inheriting from built-in types (`list`, `dict`) is occasionally legitimate (building a specialized container type), but should never be done just to borrow implementation.

---

## 11. Quick-Reference Decision Flowchart

```
START: I need to write some Python code.
│
├── Does it have BOTH state that changes AND behavior on that state?
│   ├── NO → Write functions. Consider a module for namespace.
│   └── YES ↓
│
├── Will I need MULTIPLE INDEPENDENT INSTANCES?
│   ├── NO → Could be a module with a single instance, or still consider class.
│   └── YES → Strong signal for a class. ↓
│
├── Is it primarily a DATA RECORD (fields + maybe a few methods)?
│   ├── YES → Use @dataclass
│   │         ├── Immutable? → frozen=True
│   │         ├── Need validation? → __post_init__
│   │         └── Complex init transformation? → write __init__ by hand
│   └── NO → Write a regular class. ↓
│
├── Does the class INHERIT from something?
│   ├── Can I say "[Child] IS-A [Parent]" honestly? → Inheritance OK
│   └── NO → Use COMPOSITION instead (has-a)
│
└── Review the anti-pattern register:
    ├── Am I writing getters/setters for every attribute? → STOP
    ├── Is this a class with only static methods? → Use a module
    ├── Is __init__ making network calls? → Extract to @classmethod factory
    └── Is the hierarchy more than 2 levels deep? → Flatten with composition
```

---

## 12. Summary

Python rewards the developer who picks the right tool for the job. The table below distills the full guide into a scannable reference.

| Situation | Recommended Approach |
|---|---|
| Pure data transformation | Functions |
| Related utilities, no shared state | Module |
| Named data record, no complex init | `@dataclass` |
| Named data record, immutable | `@dataclass(frozen=True)` |
| Named data record, complex init logic | Hand-written class |
| Object with evolving state + behavior | Regular class |
| Multiple independent instances needed | Regular class |
| Polymorphic dispatch across types | Inheritance (is-a) or Protocol |
| Reusing code from another class | Composition (has-a) |
| One-off scripts | Top-level functions, no class |
| Configuration data | Dict, frozen dataclass, or simple class |
| Deep hierarchy (>2 levels) | Refactor to composition |
| Static-only utility class | Module |

The single most important mental shift from Java to Python: **start with functions.** Reach for a class when state and behavior are genuinely inseparable, when you need multiple independent instances, or when polymorphism will simplify your call sites. Let the problem tell you when an object is needed — don't impose one.

---

*Companion files: `oop_right_examples.py`, `procedural_right_examples.py`, `it_depends_examples.py`*
