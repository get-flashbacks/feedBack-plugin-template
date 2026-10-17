# feedBack Plugin Template — AI Agent Guide

## This repo is a template, not a plugin

`my-plugin` is not a real plugin id — it's a placeholder directory meant to
be copied, renamed, and rewritten. As shipped it does mount as a working
demo (the counter screen, settings panel, and settings routes all function),
so you can install it and watch it run before renaming. Treat every
identifier as a placeholder regardless:

- `my-plugin/plugin.json`'s `id: "my-plugin"` and the folder name
  `my-plugin/` are meant to be changed together. The spec requires them to
  match; the shipped Host is more permissive. See `AGENTS.md` →
  *Spec vs. shipped Host* for the exact behavior and *Renaming this template
  into a real plugin* for the full checklist.
- Every route in `routes.py` is namespaced `/api/plugins/my-plugin/...` and
  needs the same rename.
- The counter/settings behavior in `screen.js`/`settings.html` is a demo
  of the mechanics (client screen ↔ server-persisted settings ↔ namespaced
  routes), not a feature worth keeping — replace it with whatever the real
  plugin actually does.
- `plugin.json` declares `"type": "utility"` to match what the example
  actually is (a settings screen, not a note-highway renderer). The
  `visualization` type is reserved for plugins implementing the
  `setRenderer` contract (a `window.feedBackViz_<id>` factory with
  `contextType`/`init`/`draw`/`resize`/`destroy`); this template doesn't
  demonstrate that, so set `type` back to `visualization` only if your real
  plugin builds that renderer from scratch.

If you're asked to "fix" or "improve" something in `my-plugin/` in the
abstract, without a rename already having happened, the most useful thing
is usually to ask what the real plugin is meant to be, since almost every
identifier in this tree is a placeholder.

## The authoritative development guide

`@AGENTS.md`

`AGENTS.md` is the single source of truth for this repo: the file table, the
demo's actual API shape, the feedBack plugin-contract conventions, the
spec-vs-Host differences (including the folder/id and screen-gate rules), the
copy/rename checklist, the verification and completion criteria, and common
pitfalls. This file does not restate or correct it — read `AGENTS.md` before
acting on anything in this repo.

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
note highway's drawing. Core registers each plugin by its manifest `id`
regardless of folder name; there's no build step — plugins are plain
files loaded at runtime.

- **Canonical app repo:** `got-feedBack/feedBack`. **This org's fork:**
  `get-flashbacks/feedBack` (personal fork with fork-specific features).
- **The authoritative plugin contract** lives in
  [`get-flashbacks/feedBack-plugin-spec`](https://github.com/get-flashbacks/feedBack-plugin-spec)
  — this org's own normative fork of the upstream
  [`got-feedBack/feedBack-plugin-spec`](https://github.com/got-feedBack/feedBack-plugin-spec).
  This repo's own README already states the spec takes precedence over
  anything here if the two conflict. Read the spec before trusting this
  template's conventions for anything non-obvious. `AGENTS.md` pins the
  spec and Host revisions this template was audited against.
- feedBack's own `CLAUDE.md` (in the core repo) documents the full plugin
  contract in far more depth than this template attempts to demonstrate:
  the `setRenderer` visualization lifecycle, capability domains
  (`capabilities.visualization.settings` for per-instance settings,
  chart-transform providers, library providers), `context["load_sibling"]`
  for safe cross-file imports, backend plugin logging, keyboard shortcuts,
  detachable panes, and the v3 player-chrome contract. This template only
  demonstrates the smallest possible slice (screen + settings + routes) —
  don't assume it's a complete reference for anything beyond that slice.
