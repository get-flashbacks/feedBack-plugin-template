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
- `AGENTS.md` — reference guide for AI assistants/contributors covering the actual API shape, plugin conventions, known code notes, and a verification checklist.
- `CLAUDE.md` — agent guide covering the template-vs-plugin distinction, feedBack app context, and two corrections to `AGENTS.md` (the `screen`-key container gate, and the spec-vs-Host folder/id mismatch behavior).

### Changed

- `my-plugin/plugin.json` `type` is now `"utility"` instead of `"visualization"`, matching what the example actually is; the `visualization` type is reserved for plugins that implement the `setRenderer` note-highway contract.


<!-- Add entries under Added, Changed, Deprecated, Removed, Fixed, or Security as changes land. -->
