# SPDX-License-Identifier: AGPL-3.0-or-later
"""Server routes for my-plugin.

Demonstrates spec §7 best practices:
  * all work happens inside setup() — nothing at import time;
  * configuration is read tolerantly (missing file => defaults);
  * routes are namespaced under the plugin id;
  * setup() validates before registering any route.
"""

import json
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

PLUGIN_ID = "my-plugin"
_DEFAULTS = {
    "color": "indigo",
    "intensity": 5,
    "enable_animations": True,
}


def setup(app: FastAPI, context: dict) -> None:
    """Register routes for my-plugin.

    Args:
        app: FastAPI application instance
        context: dict with config_dir and log keys
    """
    config_dir = Path(context["config_dir"])
    log = context.get("log") or logging.getLogger(f"feedBack.plugin.{PLUGIN_ID}")
    config_file = config_dir / f"{PLUGIN_ID}.json"

    def _read() -> dict:
        """Read persisted settings, tolerating a missing or corrupt file."""
        if not config_file.exists():
            return dict(_DEFAULTS)
        try:
            data = json.loads(config_file.read_text(encoding="utf-8"))
            # Merge with defaults to handle missing keys in old configs
            return {**_DEFAULTS, **data} if isinstance(data, dict) else dict(_DEFAULTS)
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

        Accepts a JSON object with any keys. Unknown keys are ignored;
        missing keys retain their previous values.
        """
        try:
            incoming = await request.json()
        except Exception as exc:
            return JSONResponse(
                {"error": f"invalid JSON: {exc}"}, status_code=400
            )

        if not isinstance(incoming, dict):
            return JSONResponse(
                {"error": "body must be a JSON object"}, status_code=400
            )

        # Merge incoming settings with existing ones
        merged = {**_read(), **incoming}

        # Persist the merged settings
        try:
            config_dir.mkdir(parents=True, exist_ok=True)
            config_file.write_text(json.dumps(merged, indent=2), encoding="utf-8")
            log.info("%s: settings updated", PLUGIN_ID)
        except Exception as exc:
            log.error("%s: failed to write settings: %s", PLUGIN_ID, exc)
            return JSONResponse(
                {"error": f"failed to save settings: {exc}"}, status_code=500
            )

        return JSONResponse(merged)

    log.info("%s: routes registered", PLUGIN_ID)
