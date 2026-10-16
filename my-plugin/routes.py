# SPDX-License-Identifier: AGPL-3.0-or-later
"""Server routes for my-plugin.

Demonstrates spec §7 best practices:
  * all work happens inside setup() — nothing at import time;
  * configuration is read tolerantly (missing file => defaults);
  * routes are namespaced under the plugin id;
  * setup() validates before registering any route;
  * settings writes are serialized (asyncio.Lock) and atomic
    (temp file + os.replace), so overlapping updates cannot
    overwrite each other and a failed write cannot corrupt
    the stored configuration.
"""

import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

PLUGIN_ID = "my-plugin"
MAX_SETTINGS_BODY_BYTES = 16 * 1024
_DEFAULTS = {
    "color": "indigo",
    "intensity": 5,
    "enable_animations": True,
}
_COLORS = frozenset({"indigo", "crimson", "emerald", "amber"})


def _is_valid_setting(name: str, value: object) -> bool:
    """Return whether a setting value matches the template schema."""
    if name == "color":
        return isinstance(value, str) and value in _COLORS
    if name == "intensity":
        return type(value) is int and 0 <= value <= 10
    if name == "enable_animations":
        return type(value) is bool
    return False


def _write_settings_atomically(config_file: Path, settings: dict) -> None:
    """Persist settings so the destination only ever holds a complete file.

    Writes to a temporary file in the same directory, flushes it to disk, then
    atomically replaces the destination with os.replace. A failure at any point
    leaves the previous configuration intact and removes the temporary file.
    """
    config_file.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=config_file.parent, prefix=f".{config_file.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(settings, handle, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, config_file)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def setup(app: FastAPI, context: dict) -> None:
    """Register routes for my-plugin.

    Args:
        app: FastAPI application instance
        context: dict with config_dir and log keys
    """
    config_dir = Path(context["config_dir"])
    log = context.get("log") or logging.getLogger(f"feedBack.plugin.{PLUGIN_ID}")
    config_file = config_dir / f"{PLUGIN_ID}.json"

    # Serializes the whole read-merge-write for concurrent requests on this
    # event loop. See the README for the multi-process limitation.
    settings_lock = asyncio.Lock()

    def _read() -> dict:
        """Read persisted settings, tolerating a missing or corrupt file."""
        if not config_file.exists():
            return dict(_DEFAULTS)
        try:
            data = json.loads(config_file.read_text(encoding="utf-8"))
            # Merge with defaults to handle missing keys in old configs
            if not isinstance(data, dict):
                return dict(_DEFAULTS)
            settings = dict(_DEFAULTS)
            for key, value in data.items():
                if _is_valid_setting(key, value):
                    settings[key] = value
            return settings
        except (OSError, ValueError) as exc:
            log.warning("%s: unreadable config, using defaults: %s", PLUGIN_ID, exc)
            return dict(_DEFAULTS)

    # Validate configuration before registering any route.
    # If your plugin needs to check external resources, do it here.
    try:
        _read()  # Verify we can read the config
        log.info("%s: configuration validated", PLUGIN_ID)
    except Exception as exc:
        log.error("%s: configuration validation failed: %s", PLUGIN_ID, exc)
        raise

    # Everything below only runs after the plugin has validated its own state.

    @app.get(f"/api/plugins/{PLUGIN_ID}/settings")
    def get_settings() -> JSONResponse:
        """Get the current settings."""
        return JSONResponse(_read())

    @app.post(f"/api/plugins/{PLUGIN_ID}/settings")
    async def set_settings(request: Request) -> JSONResponse:
        """Update settings.

        Accepts a bounded JSON object containing recognized settings. Missing
        keys retain their previous values.
        """
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                content_length_value = int(content_length)
                if content_length_value < 0:
                    return JSONResponse(
                        {"error": "invalid Content-Length header"}, status_code=400
                    )
                if content_length_value > MAX_SETTINGS_BODY_BYTES:
                    return JSONResponse(
                        {"error": "request body too large"}, status_code=413
                    )
            except ValueError:
                return JSONResponse(
                    {"error": "invalid Content-Length header"}, status_code=400
                )

        body = bytearray()
        try:
            async for chunk in request.stream():
                if len(body) + len(chunk) > MAX_SETTINGS_BODY_BYTES:
                    return JSONResponse(
                        {"error": "request body too large"}, status_code=413
                    )
                body.extend(chunk)
            incoming = json.loads(body)
        except (UnicodeDecodeError, ValueError):
            return JSONResponse(
                {"error": "invalid JSON body"}, status_code=400
            )

        if not isinstance(incoming, dict):
            return JSONResponse(
                {"error": "body must be a JSON object"}, status_code=400
            )

        unknown_keys = incoming.keys() - _DEFAULTS.keys()
        if unknown_keys:
            return JSONResponse(
                {"error": "body contains unknown settings"}, status_code=400
            )
        if not all(_is_valid_setting(key, value) for key, value in incoming.items()):
            return JSONResponse(
                {"error": "body contains invalid setting values"}, status_code=400
            )

        def _merge_and_persist() -> dict:
            """Merge incoming settings with existing ones and persist. Runs
            off the event loop (asyncio.to_thread below) since _read() and
            the write are blocking filesystem calls, and set_settings must
            stay `async def` to stream the request body above."""
            merged = {**_read(), **incoming}
            _write_settings_atomically(config_file, merged)
            return merged

        try:
            # Hold the lock across the full read-merge-write so concurrent
            # subset updates observe each other's changes instead of
            # overwriting them (last writer wins on stale data). The lock
            # only covers this process; see the README for multi-process
            # deployments.
            async with settings_lock:
                merged = await asyncio.to_thread(_merge_and_persist)
            log.info("%s: settings updated", PLUGIN_ID)
        except Exception as exc:
            log.error("%s: failed to write settings: %s", PLUGIN_ID, exc)
            return JSONResponse(
                {"error": f"failed to save settings: {exc}"}, status_code=500
            )

        return JSONResponse(merged)

    log.info("%s: routes registered", PLUGIN_ID)
