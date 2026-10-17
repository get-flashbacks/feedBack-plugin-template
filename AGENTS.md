# feedBack Plugin Template — Agent Guide

## What this template does

A reference implementation demonstrating the fundamental feedBack plugin contract: a client screen, a server-persisted settings panel, and namespaced server routes. It is meant to be copied and renamed, not used as-is.

This file is the authoritative guide for development in this repo. `CLAUDE.md` covers template-vs-plugin context and points here instead of restating or correcting these rules. The normative plugin contract lives in the spec below.

## Contract sources

The contract has two sources, and they do not always agree:

| Source | Repository | Pinned revision | What it is |
|---|---|---|---|
| Specification (normative) | [`get-flashbacks/feedBack-plugin-spec`](https://github.com/get-flashbacks/feedBack-plugin-spec) — `spec/plugin-spec-v1.md`, `schemas/plugin.schema.json` | [`3d653d1`](https://github.com/get-flashbacks/feedBack-plugin-spec/tree/3d653d1ffedfeed7173f23359e48a964a80d84ac) | The MUST/SHOULD rules a plugin is validated against. |
| Host (observed) | [`get-flashbacks/feedBack`](https://github.com/get-flashbacks/feedBack) — `plugins/__init__.py`, `static/js/plugin-loader.js` | [`ff8984a`](https://github.com/get-flashbacks/feedBack/tree/ff8984ace37714be2eb00c61f1fe4c5b2bd4ecc3) | What the shipped app actually does. |

Both are org forks of the upstream `got-feedBack/*` repos. These revisions are the ones this template was audited against; bump them when you re-verify. To settle a contract question, fetch the named file at the pinned revision and read it rather than trusting prose — for example:

```bash
curl -s https://raw.githubusercontent.com/get-flashbacks/feedBack/ff8984ace37714be2eb00c61f1fe4c5b2bd4ecc3/plugins/__init__.py | grep -n has_screen
```

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

- **`id` is the plugin's identity.** It keys the nav entry, the settings store, the routes namespace, and the `plugin-<id>` screen container. Folder name and manifest `id` should match (see *Spec vs. shipped Host*).
- **Nav screen** uses `"nav": { "label": "My Plugin", "screen": "plugin-my-plugin" }`
- **A screen mounts only when the manifest declares a top-level `screen` key.** The Host creates the `plugin-<id>` container only when `bool(manifest.get("screen"))` (`has_screen`); `script` is injected independently, so a script-only manifest runs `screen.js` against a DOM where that container was never created. The current Host hardcodes the fetch to `/api/plugins/<id>/screen.html` and ignores the manifest value, so the file must be named `screen.html`.
- **screen.js finds its own root** via `document.getElementById('plugin-<id>')` — the Host injects markup into that container
- **Settings persist server-side**, not in browser storage — always go through the plugin's own routes
- **routes.py exports `setup(app, context)`** — receives the FastAPI app and a context dict with `config_dir` and `log`
- **Configuration validation happens once in `setup()`**, before any route is registered, so a broken config fails plugin load loudly rather than failing silently on first request
- **API path** is `/api/plugins/<plugin_id>/<route>`
- **No build step** — vanilla JS, no npm; the Python tests run under `pytest` (see `requirements-dev.txt`)

### Spec vs. shipped Host

The normative rules and the shipped Host do not always agree. When they differ, follow the Host for code that has to run today and the spec for anything that has to stay portable — and say which one you mean.

- **A folder/id mismatch is not discovery-fatal in the shipped Host.** Spec §5.2 says a directory is loaded "only when the directory name equals the manifest `id`", and §4.2 says a Host "MUST NOT treat it as bundled and SHOULD skip or warn". The shipped Host instead registers every subdirectory by its manifest `id` whatever the folder is called (`plugins/__init__.py`), and the folder name only feeds `_is_bundled()` for duplicate resolution. Match them anyway — the spec is stricter, and relying on the Host's leniency is not a documented contract.
- **The screen container is Host-gated.** Spec §6.1 describes mounting "for each ready plugin that declares a `screen`"; the Host implements exactly that (`has_screen == bool(manifest.get("screen"))` in `plugins/__init__.py`). The `screen` value itself is ignored — `plugin-loader.js` always fetches `/api/plugins/<id>/screen.html` — so the markup file must be named `screen.html`.

## Renaming this template into a real plugin

`my-plugin` is a placeholder id. Change every occurrence together, or the screen lookup and the `/api/plugins/<id>/...` routes will point at the old name:

1. Rename the directory to your new id: `git mv my-plugin your-plugin`.
2. `your-plugin/plugin.json` — `id` (must equal the folder name); also `name`, `version`, `description`, `type`, `icon`, and `nav.screen` (stays `plugin-<id>`).
3. `your-plugin/screen.js` — the `PLUGIN_ID` constant.
4. `your-plugin/settings.html` — the `PLUGIN_ID` constant.
5. `your-plugin/routes.py` — the `PLUGIN_ID` constant (it derives the route namespace).

Keep the id lowercase (`^[a-z0-9][a-z0-9_-]*$`). The id is permanent: changing it later orphans users' saved settings. The `tests/` suite discovers the plugin by scanning for `plugin.json` and reads the id from the manifest, so it keeps passing after a rename without edits.

## Known issues / code notes

- `screen.js` uses a `window[\`__${PLUGIN_ID}_setup\`]` guard to avoid double-initializing on re-hydration.
- `loadSettings()` fails soft on fetch errors (`console.warn`) rather than throwing, so a settings-load failure degrades the screen instead of crashing it.
- `_is_valid_setting()` in `routes.py` uses `type(value) is int` / `type(value) is bool` (not `isinstance`) specifically to reject `bool` being accepted where `int` is expected (Python's `bool` is an `int` subclass).
- `routes.py` serializes the whole read–merge–write with an `asyncio.Lock` and persists via `_write_settings_atomically()` (temp file in the same directory + `os.replace`). The lock is per-process only — multiple workers sharing a `config_dir` would need a cross-process lock; `os.replace` still prevents torn files. The guarantee also assumes each handler runs to completion: cancelling the task mid-`asyncio.to_thread` releases the lock while the worker thread finishes anyway.
- The test fixture uses `with TestClient(app) as client:` on purpose: every request must share one event loop, otherwise a per-request loop rejects the `asyncio.Lock` bound by the first request.

## Verification and completion criteria

Exact commands, from the repo root (a venv keeps the test deps out of the system env):

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

A change to this repo is complete when:

1. `pytest -q` passes.
2. The `custom-checks.yml` steps pass locally and in CI on the PR — manifest validation, `node --check my-plugin/screen.js`, and no `print(` in `routes.py`. `custom-checks.yml` carries the exact commands.
3. Every doc claim about the contract still holds against the pinned revisions in *Contract sources*.

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

- **Folder name should equal `plugin.json` id**, including case — the spec requires it, even though the shipped Host tolerates a mismatch (see *Spec vs. shipped Host*)
- **Route collisions** — always prefix with `/api/plugins/<id>/`
- **A script-only manifest renders nothing** — declare a top-level `screen` key and name the file `screen.html` or the Host never creates the container
- **FastAPI POST routes** need `from fastapi import Request` and `async def route(request: Request)` reading the body via a bounded stream, not `await request.json()` directly, if you want the size cap to apply before full deserialization
