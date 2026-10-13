"""Shared fixtures for the template's plugin-contract tests.

The suite discovers the plugin directory by scanning for a ``plugin.json``
instead of hard-coding ``my-plugin``, so a copy that has already been renamed
still runs. Everything else — the manifest, the routes path, the route prefix —
is derived from the manifest.
"""

import importlib.util
import json
import logging
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent


def _plugin_dirs() -> list[Path]:
    return sorted(p.parent for p in REPO_ROOT.glob("*/plugin.json"))


@pytest.fixture(scope="session")
def plugin_dir() -> Path:
    dirs = _plugin_dirs()
    assert len(dirs) == 1, f"expected exactly one plugin directory, found {dirs}"
    return dirs[0]


@pytest.fixture(scope="session")
def manifest(plugin_dir: Path) -> dict:
    return json.loads((plugin_dir / "plugin.json").read_text(encoding="utf-8"))


@pytest.fixture()
def routes_module(plugin_dir: Path, manifest: dict):
    spec = importlib.util.spec_from_file_location(
        "plugin_under_test_routes", plugin_dir / manifest["routes"]
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def client(plugin_dir: Path, manifest: dict, routes_module, tmp_path: Path) -> TestClient:
    app = FastAPI()
    routes_module.setup(
        app, {"config_dir": tmp_path, "log": logging.getLogger("plugin-tests")}
    )
    return TestClient(app)


@pytest.fixture()
def settings_url(manifest: dict) -> str:
    return f"/api/plugins/{manifest['id']}/settings"
