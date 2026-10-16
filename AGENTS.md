# feedBack Plugin Template — Agent Guide

## What this template does

A reference implementation demonstrating the fundamental feedBack plugin contract: a client screen, a server-persisted settings panel, and namespaced server routes. It is meant to be copied and renamed, not used as-is.

## Files

| File | Purpose |
|---|---|
| `my-plugin/plugin.json` | Manifest — id `my-plugin`, nav entry, script/screen/styles/settings/routes, type, icon, minHost |
| `my-plugin/screen.html` | Client screen markup — mounted into `plugin-my-plugin` by the Host, holds the counter and settings hooks `screen.js` queries |
| `my-plugin/screen.js` | Client screen logic — finds its root by `plugin-<id>`, wires up an example counter, loads persisted settings |
| `my-plugin/settings.html` | Settings panel markup, grouped under `settings.category` |
| `my-plugin/routes.py` | FastAPI `setup(app, context)` — registers GET/POST `/api/plugins/my-plugin/settings` with schema validation and serialized, atomic persistence |
| `my-plugin/assets/plugin.css` | Styling scoped to the plugin |
| `my-plugin/README.md` | Per-plugin documentation for whoever copies this template |
| `tests/` | pytest suite for the manifest/screen contract and the settings routes |
| `requirements-dev.txt` | Test-only dependencies (`fastapi`, `httpx`, `pytest`) |

## Actual API shape

- **Routes:** `GET /api/plugins/my-plugin/settings`, `POST /api/plugins/my-plugin/settings`
- **Settings schema:** `{color: "indigo"|"crimson"|"emerald"|"amber", intensity: int 0-10, enable_animations: bool}`
- **GET response:** current settings, merged with defaults for any missing keys
- **POST body:** a JSON object containing a subset of recognized settings; unknown keys or invalid values return `400`
- **POST limits:** request body capped at `MAX_SETTINGS_BODY_BYTES` (16 KiB); oversized or malformed bodies return `413`/`400`
- **Persistence:** settings are written to `<config_dir>/my-plugin.json` off the event loop via `asyncio.to_thread`; concurrent writes are serialized by an `asyncio.Lock` and applied atomically (temp file + `os.replace`), so a failed write preserves the last valid config

## Key conventions (feedBack plugin contract)

- **plugin.json id must match directory name** — `my-plugin` == `my-plugin/`
- **Nav screen** uses `"nav": { "label": "My Plugin", "screen": "plugin-my-plugin" }`
- **Screen markup** is declared with a top-level `screen` key and lives in `screen.html`; the Host creates the `plugin-<id>` container from that key and injects the markup, then runs `script`. The current Host hardcodes the fetch path (`/api/plugins/<id>/screen.html`) and ignores the manifest value, so the file must be named `screen.html`.
- **screen.js finds its own root** via `document.getElementById('plugin-<id>')` — the Host injects markup into that container
- **Settings persist server-side**, not in browser storage — always go through the plugin's own routes
- **routes.py exports `setup(app, context)`** — receives the FastAPI app and a context dict with `config_dir` and `log`
- **Configuration validation happens once in `setup()`**, before any route is registered, so a broken config fails plugin load loudly rather than failing silently on first request
- **API path** is `/api/plugins/<plugin_id>/<route>`
- **No build step** — vanilla JS, no npm; the Python tests run under `pytest` (see `requirements-dev.txt`)

## Known issues / code notes

- `screen.js` uses a `window[\`__${PLUGIN_ID}_setup\`]` guard to avoid double-initializing on re-hydration.
- `loadSettings()` fails soft on fetch errors (`console.warn`) rather than throwing, so a settings-load failure degrades the screen instead of crashing it.
- `_is_valid_setting()` in `routes.py` uses `type(value) is int` / `type(value) is bool` (not `isinstance`) specifically to reject `bool` being accepted where `int` is expected (Python's `bool` is an `int` subclass).
- `routes.py` serializes the whole read–merge–write with an `asyncio.Lock` and persists via `_write_settings_atomically()` (temp file in the same directory + `os.replace`). The lock is per-process only — multiple workers sharing a `config_dir` would need a cross-process lock; `os.replace` still prevents torn files. The guarantee also assumes each handler runs to completion: cancelling the task mid-`asyncio.to_thread` releases the lock while the worker thread finishes anyway.
- The test fixture uses `with TestClient(app) as client:` on purpose: every request must share one event loop, otherwise a per-request loop rejects the `asyncio.Lock` bound by the first request.

## Verification checklist

Automated (the same checks `custom-checks.yml` runs):

```bash
pip install -r requirements-dev.txt
pytest -q
```

Against a running Host with `my-plugin/` installed:

1. Plugin loads without server errors (`setup()` validates config before registering routes)
2. Nav entry "My Plugin" appears in sidebar
3. Clicking the counter button increments the on-screen counter
4. GET `/api/plugins/my-plugin/settings` returns defaults on first load
5. POSTing a valid settings subset persists and is reflected on next GET
6. POSTing an unknown key or invalid value returns `400`
7. Oversized POST body returns `413`
8. Concurrent POSTs to different settings keys all persist — no lost updates (the `asyncio.Lock` in `routes.py` serializes them)

## Common pitfalls

- **Folder name must equal `plugin.json` id**, including case
- **Route collisions** — always prefix with `/api/plugins/<id>/`
- **FastAPI POST routes** need `from fastapi import Request` and `async def route(request: Request)` reading the body via a bounded stream, not `await request.json()` directly, if you want the size cap to apply before full deserialization
