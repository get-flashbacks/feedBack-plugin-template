"""Manifest and screen-contract checks.

These fail when the example stops being runnable through the Host's screen
contract: a declared surface whose file is missing, a nav entry pointing at a
container the Host never creates, or screen markup that lacks the hooks
``screen.js`` queries.
"""

from pathlib import Path

HOST_SCREEN_PATH = "screen.html"


def test_every_declared_file_exists(plugin_dir: Path, manifest: dict) -> None:
    for key in ("script", "screen", "styles", "routes"):
        assert key in manifest, f"manifest must declare '{key}'"
        assert (plugin_dir / manifest[key]).is_file(), (
            f"'{key}' points at a missing file: {manifest[key]}"
        )
    assert (plugin_dir / manifest["settings"]["html"]).is_file(), (
        "settings.html points at a missing file"
    )


def test_screen_file_is_the_path_the_host_fetches(
    plugin_dir: Path, manifest: dict
) -> None:
    # The shipped Host hardcodes `/api/plugins/<id>/screen.html` when mounting a
    # screen and ignores the manifest screen value, so the declared file has to
    # be named `screen.html` for the example to actually render.
    assert manifest["screen"] == HOST_SCREEN_PATH
    assert (plugin_dir / HOST_SCREEN_PATH).is_file()


def test_nav_entry_points_at_the_screen_container(manifest: dict) -> None:
    # The Host creates the container as `plugin-<id>`; a nav entry that points
    # anywhere else is a dead sidebar link.
    assert manifest["nav"]["screen"] == f"plugin-{manifest['id']}"


def test_screen_markup_exposes_the_hooks_screen_js_queries(
    plugin_dir: Path, manifest: dict
) -> None:
    html = (plugin_dir / manifest["screen"]).read_text(encoding="utf-8")
    for role in ("increment-button", "counter", "color-display"):
        assert f'data-role="{role}"' in html, f"screen markup is missing data-role={role}"
