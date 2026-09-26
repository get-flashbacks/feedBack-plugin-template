# feedBack Plugin Template — AI Agent Guide

## This repo is a template, not a plugin

**Nothing in `my-plugin/` runs as-is inside feedBack.** `my-plugin` is not
a real plugin id — it's a placeholder directory meant to be copied,
renamed, and rewritten. Until that happens:

- `my-plugin/plugin.json`'s `id: "my-plugin"` and the folder name
  `my-plugin/` are meant to be changed together (the folder name **must**
  equal the manifest `id`, case-sensitive — a mismatch is a silent skip at
  plugin discovery in every real feedBack host).
- Every route in `routes.py` is namespaced `/api/plugins/my-plugin/...` and
  needs the same rename.
- The counter/settings behavior in `screen.js`/`settings.html` is a demo
  of the mechanics (client screen ↔ server-persisted settings ↔ namespaced
  routes), not a feature worth keeping — replace it with whatever the real
  plugin actually does.
- `plugin.json` declares `"type": "visualization"`, but nothing here
  implements the `setRenderer` viz-renderer contract (no
  `window.feedBackViz_<id>` factory, no `contextType`/`init`/`draw`/
  `resize`/`destroy`). If the real plugin isn't a highway visualization,
  drop or change `type`; if it is one, the renderer contract has to be
  built from scratch — this template doesn't demonstrate it.

If you're asked to "fix" or "improve" something in `my-plugin/` in the
abstract, without a rename already having happened, the most useful thing
is usually to ask what the real plugin is meant to be, since almost every
identifier in this tree is a placeholder.

## What feedBack is

feedBack is a self-hosted web app for browsing, playing, and practicing
interactive music notation (guitar/bass/keys tab, imported from Guitar Pro
or MusicXML, or authored directly in its own open `.sloppak`/feedpak
format). It's a Docker-deployed FastAPI backend + vanilla-JS frontend, with
an extensive first- and third-party plugin ecosystem under `plugins/`. A
plugin is a directory with a `plugin.json` manifest that can declare a
client screen (`script`), a settings panel (`settings.html` + backend
persistence), namespaced server routes (`routes.py`), and/or (for
visualization plugins) a `setRenderer` factory that takes over the main
note highway's drawing. Core discovers and loads plugins by directory name
matching manifest `id`; there's no compiled/bundled plugin format — plain
files loaded at runtime.

- **Canonical app repo:** `got-feedBack/feedBack`. **This org's fork:**
  `get-flashbacks/feedBack` (personal fork with fork-specific features).
- **The authoritative plugin contract** lives in
  [`got-feedBack/feedback-plugin-spec`](https://github.com/got-feedBack/feedback-plugin-spec)
  (spec) — this repo's own README already states the spec takes precedence
  over anything here if the two conflict. Read the spec before trusting
  this template's conventions for anything non-obvious.
- feedBack's own `CLAUDE.md` (in the core repo) documents the full plugin
  contract in far more depth than this template attempts to demonstrate:
  the `setRenderer` visualization lifecycle, capability domains
  (`capabilities.visualization.settings` for per-instance settings,
  chart-transform providers, library providers), `context["load_sibling"]`
  for safe cross-file imports, backend plugin logging, keyboard shortcuts,
  detachable panes, and the v3 player-chrome contract. This template only
  demonstrates the smallest possible slice (screen + settings + routes) —
  don't assume it's a complete reference for anything beyond that slice.

## Files

| File | Purpose |
|---|---|
| `my-plugin/plugin.json` | Manifest — id `my-plugin`, nav entry, script/styles/settings/routes, type, icon, minHost |
| `my-plugin/screen.js` | Client screen logic — finds its root by `plugin-<id>`, wires up an example counter, loads persisted settings |
| `my-plugin/settings.html` | Settings panel markup, grouped under `settings.category` |
| `my-plugin/routes.py` | FastAPI `setup(app, context)` — registers GET/POST `/api/plugins/my-plugin/settings` with schema validation and persistence |
| `my-plugin/assets/plugin.css` | Styling scoped to the plugin |
| `my-plugin/README.md` | Per-plugin documentation for whoever copies this template |

## Actual API shape (of the demo, before renaming)

- **Routes:** `GET /api/plugins/my-plugin/settings`, `POST /api/plugins/my-plugin/settings`
- **Settings schema:** `{color: "indigo"|"crimson"|"emerald"|"amber", intensity: int 0-10, enable_animations: bool}`
- **GET response:** current settings, merged with defaults for any missing keys
- **POST body:** a JSON object containing a subset of recognized settings; unknown keys or invalid values return `400`
- **POST limits:** request body capped at `MAX_SETTINGS_BODY_BYTES` (16 KiB); oversized or malformed bodies return `413`/`400`
- **Persistence:** settings are written to `<config_dir>/my-plugin.json` off the event loop via `asyncio.to_thread`

## Key conventions (feedBack plugin contract)

- **plugin.json id must match directory name** — `my-plugin` == `my-plugin/`
- **Nav screen** uses `"nav": { "label": "My Plugin", "screen": "plugin-my-plugin" }`
- **screen.js finds its own root** via `document.getElementById('plugin-<id>')` — the Host injects markup into that container
- **Settings persist server-side**, not in browser storage — always go through the plugin's own routes
- **routes.py exports `setup(app, context)`** — receives the FastAPI app and a context dict with `config_dir` and `log`
- **Configuration validation happens once in `setup()`**, before any route is registered, so a broken config fails plugin load loudly rather than failing silently on first request
- **API path** is `/api/plugins/<plugin_id>/<route>`
- **No build step** — vanilla JS, no npm

## Known issues / code notes

- `screen.js` uses a `window[\`__${PLUGIN_ID}_setup\`]` guard to avoid double-initializing on re-hydration.
- `loadSettings()` fails soft on fetch errors (`console.warn`) rather than throwing, so a settings-load failure degrades the screen instead of crashing it.
- `_is_valid_setting()` in `routes.py` uses `type(value) is int` / `type(value) is bool` (not `isinstance`) specifically to reject `bool` being accepted where `int` is expected (Python's `bool` is an `int` subclass).

## Verification checklist

1. Plugin loads without server errors (`setup()` validates config before registering routes)
2. Nav entry "My Plugin" appears in sidebar
3. Clicking the counter button increments the on-screen counter
4. GET `/api/plugins/my-plugin/settings` returns defaults on first load
5. POSTing a valid settings subset persists and is reflected on next GET
6. POSTing an unknown key or invalid value returns `400`
7. Oversized POST body returns `413`

## Common pitfalls

- **Folder name must equal `plugin.json` id**, including case
- **Route collisions** — always prefix with `/api/plugins/<id>/`
- **FastAPI POST routes** need `from fastapi import Request` and `async def route(request: Request)` reading the body via a bounded stream, not `await request.json()` directly, if you want the size cap to apply before full deserialization
