# feedBack Plugin Template — AI Agent Guide

## This repo is a template, not a plugin

`my-plugin` is not a real plugin id — it's a placeholder directory meant to
be copied, renamed, and rewritten. As shipped it does mount as a working
demo (the counter screen, settings panel, and settings routes all function),
so you can install it and watch it run before renaming. Treat every
identifier as a placeholder regardless:

- `my-plugin/plugin.json`'s `id: "my-plugin"` and the folder name
  `my-plugin/` are meant to be changed together. The plugin-spec (see
  below) states a folder/id mismatch is discovery-fatal, but the shipped
  `get-flashbacks/feedBack` Host is more permissive: the loader registers
  a plugin by its manifest `id` regardless of folder name, and a
  mismatch only affects `bundled: true` duplicate-resolution behavior —
  it isn't a silent skip there. Match them anyway; the spec is stricter,
  and relying on the Host's leniency is not a documented contract.
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
  [`get-flashbacks/feedback-plugin-spec`](https://github.com/get-flashbacks/feedback-plugin-spec)
  — this org's own normative fork of the upstream
  [`got-feedBack/feedback-plugin-spec`](https://github.com/got-feedBack/feedback-plugin-spec).
  This repo's own README already states the spec takes precedence over
  anything here if the two conflict. Read the spec before trusting this
  template's conventions for anything non-obvious.
- feedBack's own `CLAUDE.md` (in the core repo) documents the full plugin
  contract in far more depth than this template attempts to demonstrate:
  the `setRenderer` visualization lifecycle, capability domains
  (`capabilities.visualization.settings` for per-instance settings,
  chart-transform providers, library providers), `context["load_sibling"]`
  for safe cross-file imports, backend plugin logging, keyboard shortcuts,
  detachable panes, and the v3 player-chrome contract. This template only
  demonstrates the smallest possible slice (screen + settings + routes) —
  don't assume it's a complete reference for anything beyond that slice.

## File map, API shape, conventions, checklist, pitfalls

@AGENTS.md

That file has the file table, the demo's actual API shape, the feedBack
plugin-contract conventions, known code notes, the verification
checklist, and common pitfalls — this file doesn't repeat that content.
Two corrections to it, both load-bearing enough to call out here rather
than silently fix in place:

- **The container-mount convention** ("screen.js finds its own root via
  `document.getElementById('plugin-<id>')`") is gated on the manifest
  declaring a top-level `screen` key (the Host's `has_screen` gate —
  `plugins/__init__.py`'s `"has_screen": bool(manifest.get("screen"))`,
  consumed by `static/js/plugin-loader.js`'s container-creation site).
  `script` is injected independently of `has_screen`, so a script-only
  manifest runs `screen.js` against a DOM where that container was never
  created. This template now declares `"screen": "screen.html"` and ships
  the file, so `plugin-my-plugin` is created and the example mounts. Note
  the current Host hardcodes the fetch path — it always requests
  `/api/plugins/<id>/screen.html` and ignores the manifest value — so the
  markup file has to be named `screen.html`.
- **The folder/id mismatch consequence** ("a mismatch is a silent skip at
  plugin discovery") is spec language, not what the shipped
  `get-flashbacks/feedBack` Host actually does — see the note in "This
  repo is a template, not a plugin" above.
