"""
it_depends_examples.py
======================
Module 7 companion: two problems where the right answer depends on context.

For each problem we show both a procedural version and an OOP version,
explain what drives the decision, and identify the axis that tips the balance.
"""

from __future__ import annotations

import os
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ============================================================
# Example 9 — Configuration Loader
# ============================================================
#
# THE TENSION
# -----------
# Pure configuration data (key-value pairs) suggests a dict or
# frozen dataclass — no behavior, no mutable state. But once you add
# lazy loading, environment variable overrides, dotted key access,
# or reload-on-demand, *behavior* appears and a class earns its place.
#
# DECISION AXIS
# -------------
# Does this config object DO anything beyond store-and-retrieve?
#   • NO  → dict or frozen dataclass (Version A below)
#   • YES → class (Version B below)
# ============================================================

# ---- Version A: procedural (simpler, right for small projects) ------

DEFAULT_CONFIG = {
    "app": {
        "debug": False,
        "host": "0.0.0.0",
        "port": 8000,
    },
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "myapp",
    },
}

SAMPLE_CONFIG_JSON = json.dumps({
    "app": {"debug": True, "port": 9000},
    "database": {"name": "myapp_dev"},
})


def load_config_procedural(json_source: str | None = None) -> dict:
    """
    Load config from a JSON string, merge over defaults.
    Environment variables (APP_DEBUG, APP_PORT) override file values.

    Returns a plain dict. Callers just do config["app"]["port"].
    Simple, transparent, zero indirection. Right when config is
    static after startup.
    """
    import copy
    config = copy.deepcopy(DEFAULT_CONFIG)

    if json_source:
        user_config = json.loads(json_source)
        # shallow-merge each top-level section
        for section, values in user_config.items():
            if section in config and isinstance(values, dict):
                config[section].update(values)
            else:
                config[section] = values

    # environment overrides
    if "APP_DEBUG" in os.environ:
        config["app"]["debug"] = os.environ["APP_DEBUG"].lower() in ("1", "true", "yes")
    if "APP_PORT" in os.environ:
        config["app"]["port"] = int(os.environ["APP_PORT"])

    return config


# --- procedural demo ---
if __name__ == "__main__":
    print("=== Config: procedural version ===")
    cfg = load_config_procedural(SAMPLE_CONFIG_JSON)
    print(f"debug={cfg['app']['debug']}, port={cfg['app']['port']}")
    print(f"db name={cfg['database']['name']}")
    print()


# ---- Version B: OOP (justified when behavior accumulates) -----------

class Config:
    """
    Configuration object with dotted key access, lazy loading,
    environment overrides, and reload capability.

    The class is justified here because:
    1. .get("app.debug", False) — behavior beyond plain dict lookup
    2. .reload()               — long-lived object that re-reads disk
    3. .set() with persistence — state mutation with side effects
    4. Instance can be injected as a dependency and mocked in tests

    If you only need #1, a simple helper function works instead.
    When you need 2-4, the class pays for itself.
    """

    def __init__(self, source: str | dict | None = None) -> None:
        self._data: dict = {}
        self._source = source
        self._load()

    # ---- public API ------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Dotted key access: config.get('app.debug', False)."""
        parts = key.split(".")
        node = self._data
        for part in parts:
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def set(self, key: str, value: Any) -> None:
        """Dotted key write: config.set('app.port', 9000)."""
        parts = key.split(".")
        node = self._data
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value

    def reload(self) -> None:
        """Re-read from the original source and re-apply env overrides."""
        print("[Config] Reloading configuration...")
        self._load()

    def as_dict(self) -> dict:
        """Return a shallow copy of the underlying dict."""
        import copy
        return copy.deepcopy(self._data)

    # ---- internal --------------------------------------------------

    def _load(self) -> None:
        import copy
        self._data = copy.deepcopy(DEFAULT_CONFIG)

        if isinstance(self._source, dict):
            for section, values in self._source.items():
                if section in self._data and isinstance(values, dict):
                    self._data[section].update(values)
                else:
                    self._data[section] = values
        elif isinstance(self._source, str):
            try:
                user_config = json.loads(self._source)
                for section, values in user_config.items():
                    if section in self._data and isinstance(values, dict):
                        self._data[section].update(values)
                    else:
                        self._data[section] = values
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid config JSON: {exc}") from exc

        self._apply_env_overrides()

    def _apply_env_overrides(self) -> None:
        if "APP_DEBUG" in os.environ:
            self.set("app.debug", os.environ["APP_DEBUG"].lower() in ("1", "true", "yes"))
        if "APP_PORT" in os.environ:
            self.set("app.port", int(os.environ["APP_PORT"]))

    def __repr__(self) -> str:
        return f"Config(debug={self.get('app.debug')}, port={self.get('app.port')})"


# --- OOP demo ---
if __name__ == "__main__":
    print("=== Config: OOP version ===")
    config = Config(SAMPLE_CONFIG_JSON)
    print(config)
    print(f"db.name = {config.get('database.name')}")
    print(f"missing key = {config.get('does.not.exist', 'fallback')}")
    config.set("app.port", 7000)
    print(f"after set: port = {config.get('app.port')}")
    config.reload()
    print(f"after reload: port = {config.get('app.port')}")
    print()


# ============================================================
# Example 10 — HTTP Request Handler
# ============================================================
#
# THE TENSION
# -----------
# Individual operations (parse headers, match route, serialize
# response) are pure functions. But the *request lifecycle* —
# accumulating parsed state as a request passes through middleware —
# benefits from an object that holds that state without threading it
# as parameters through every function call.
#
# DECISION AXIS
# -------------
# Is request state shared across many call sites WITHIN a single
# request's lifetime?
#   • NO  → pure functions suffice (Version A below)
#   • YES → a Request object eliminates parameter-passing spaghetti
#           (Version B below)
# ============================================================

# ---- Version A: procedural (fine for simple, shallow handlers) ------

def parse_headers_proc(raw: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            headers[key.strip().lower()] = value.strip()
    return headers


def parse_query_string_proc(qs: str) -> dict[str, str]:
    if not qs:
        return {}
    params: dict[str, str] = {}
    for pair in qs.split("&"):
        if "=" in pair:
            k, _, v = pair.partition("=")
            params[k] = v
    return params


def build_response_proc(status: int, body: str,
                        content_type: str = "text/plain") -> bytes:
    STATUS_TEXTS = {200: "OK", 201: "Created", 400: "Bad Request",
                    404: "Not Found", 500: "Internal Server Error"}
    status_text = STATUS_TEXTS.get(status, "Unknown")
    headers = (
        f"HTTP/1.1 {status} {status_text}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body.encode())}\r\n"
        f"\r\n"
    )
    return (headers + body).encode()


def handle_request_proc(raw_request: str) -> bytes:
    """Simple handler that passes data through functions explicitly.

    Fine when: one handler, shallow middleware stack, simple routing.
    Gets messy when: middleware needs to annotate the request, many
    handlers share parsed state, or the call chain grows deep.
    """
    lines = raw_request.splitlines()
    request_line = lines[0] if lines else ""
    parts = request_line.split()
    method = parts[0] if len(parts) > 0 else "GET"
    path_qs = parts[1] if len(parts) > 1 else "/"

    path, _, qs = path_qs.partition("?")
    headers = parse_headers_proc("\n".join(lines[1:]))
    params = parse_query_string_proc(qs)

    # simple routing
    if path == "/health":
        return build_response_proc(200, "OK")
    elif path == "/echo":
        return build_response_proc(200, str(params))
    else:
        return build_response_proc(404, f"Not Found: {path}")


# --- procedural demo ---
if __name__ == "__main__":
    print("=== HTTP Handler: procedural version ===")
    raw = "GET /echo?greeting=hello&name=world HTTP/1.1\r\nHost: localhost\r\n"
    response = handle_request_proc(raw)
    print(response.decode()[:200])
    print()


# ---- Version B: OOP (justified when state accumulates across middleware) ---

class Request:
    """
    Represents a single HTTP request's lifetime.

    Justified because:
    1. Lazy parsing — headers and JSON body are expensive to parse;
       we only parse what the handler actually accesses.
    2. Middleware annotations — middleware can attach attributes
       (e.g., request.user = authenticated_user) without changing
       every function signature.
    3. Shared state — many handlers need .method, .path, .headers,
       .json without re-parsing raw bytes each time.

    Without this object, every middleware function would need to
    accept and return (method, path, headers, body, user, ...) as
    a growing parameter tuple — which is just an object without syntax.
    """

    def __init__(self, raw: str) -> None:
        self._raw = raw
        self._headers: dict[str, str] | None = None
        self._params: dict[str, str] | None = None
        self._body_cache: str | None = None

        lines = raw.splitlines()
        request_line = lines[0] if lines else ""
        parts = request_line.split()
        self.method = parts[0] if len(parts) > 0 else "GET"
        path_qs = parts[1] if len(parts) > 1 else "/"
        self.path, _, self._raw_qs = path_qs.partition("?")

        # middleware can attach arbitrary state
        self.user: str | None = None
        self.trace_id: str | None = None

    @property
    def headers(self) -> dict[str, str]:
        """Lazy: only parsed if accessed."""
        if self._headers is None:
            lines = self._raw.splitlines()
            self._headers = parse_headers_proc("\n".join(lines[1:]))
        return self._headers

    @property
    def params(self) -> dict[str, str]:
        """Lazy: query string parsed only on first access."""
        if self._params is None:
            self._params = parse_query_string_proc(self._raw_qs)
        return self._params

    @property
    def content_type(self) -> str:
        return self.headers.get("content-type", "")

    def get_header(self, name: str, default: str = "") -> str:
        return self.headers.get(name.lower(), default)

    def __repr__(self) -> str:
        return f"Request({self.method} {self.path})"


class Response:
    def __init__(self, status: int = 200, body: str = "",
                 content_type: str = "text/plain") -> None:
        self.status = status
        self.body = body
        self.content_type = content_type

    def to_bytes(self) -> bytes:
        return build_response_proc(self.status, self.body, self.content_type)


# Middleware as simple callables that mutate the request
def auth_middleware(request: Request) -> None:
    """Attach user info to the request object."""
    token = request.get_header("authorization")
    request.user = "alice" if token == "Bearer secret" else None


def trace_middleware(request: Request) -> None:
    """Attach a trace ID (normally from headers or generated)."""
    import uuid
    request.trace_id = request.get_header("x-trace-id") or str(uuid.uuid4())[:8]


def handle_request_oop(raw: str) -> bytes:
    """Handler using Request object — middleware annotations are clean."""
    request = Request(raw)

    # run middleware stack — each step can annotate request freely
    auth_middleware(request)
    trace_middleware(request)

    # routing
    if request.path == "/health":
        return Response(200, "OK").to_bytes()
    elif request.path == "/echo":
        return Response(200, str(request.params)).to_bytes()
    elif request.path == "/me":
        if not request.user:
            return Response(401, "Unauthorized").to_bytes()
        return Response(200, f"Hello, {request.user}!").to_bytes()
    else:
        return Response(404, f"Not Found: {request.path}").to_bytes()


# --- OOP demo ---
if __name__ == "__main__":
    print("=== HTTP Handler: OOP version ===")

    # authenticated request
    raw_auth = (
        "GET /me HTTP/1.1\r\n"
        "Authorization: Bearer secret\r\n"
        "Host: localhost\r\n"
    )
    print(handle_request_oop(raw_auth).decode()[:200])

    # unauthenticated request
    raw_anon = "GET /me HTTP/1.1\r\nHost: localhost\r\n"
    print(handle_request_oop(raw_anon).decode()[:200])

    # echo with params
    raw_echo = "GET /echo?a=1&b=2 HTTP/1.1\r\nHost: localhost\r\n"
    print(handle_request_oop(raw_echo).decode()[:200])
