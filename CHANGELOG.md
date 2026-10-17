# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `my-plugin/screen.html` and a top-level `screen` manifest key, so the example screen actually mounts — the Host only creates the `plugin-my-plugin` container when `screen` is declared.
- `tests/` and `requirements-dev.txt` — pytest coverage for the manifest/screen contract (declared files exist, the screen path the Host fetches, the nav container id) and the settings routes (GET defaults, valid-subset POST/persistence, invalid/unknown values, malformed JSON, and the 16 KiB body limit).
- `custom-checks.yml` now fails when the `screen` file or nav container reference is missing and runs `pytest`.
- `nav` field in `my-plugin/plugin.json` (`{ "label": "My Plugin", "screen": "plugin-my-plugin" }`) so the plugin registers a sidebar entry.
- `AGENTS.md` — the authoritative development guide: the contract's spec and Host sources with the pinned revisions this template was verified against, the actual API shape, the plugin conventions with the spec-vs-Host differences called out, a copy/rename checklist, known code notes, and verification/completion criteria.
- `CLAUDE.md` — agent guide covering the template-vs-plugin distinction and feedBack app context; it defers to `AGENTS.md` rather than restating or correcting it.

### Changed

- Unified the docs around the actual plugin contract. `AGENTS.md` now folds in and owns the spec-vs-Host notes `CLAUDE.md` previously carried as corrections; the READMEs no longer claim a folder/id mismatch "will not load" (the spec requires them to match, but the shipped Host tolerates a mismatch), name the Host's real plugin-discovery directories, and state the settings store as `<config_dir>/<id>.json`. Spec links use the canonical `get-flashbacks/feedBack-plugin-spec` name. `.gitignore` now ignores the `.venv/` the documented setup creates.
- `my-plugin/plugin.json` `type` is now `"utility"` instead of `"visualization"`, matching what the example actually is; the `visualization` type is reserved for plugins that implement the `setRenderer` note-highway contract.

### Fixed

- `my-plugin/routes.py` now serializes the full read–merge–persist with an `asyncio.Lock` and writes settings atomically (temp file + `os.replace`), so concurrent subset `POST`s no longer overwrite each other and a failed or interrupted write preserves the last valid configuration. Covered by an overlapping-request test and a failed-write test; the single-process scope of the lock is documented in `my-plugin/README.md` and `AGENTS.md`.


<!-- Add entries under Added, Changed, Deprecated, Removed, Fixed, or Security as changes land. -->
