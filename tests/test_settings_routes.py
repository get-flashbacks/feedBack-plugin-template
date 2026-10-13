"""Behavioral tests for the example's settings routes.

Covers the advertised contract: GET returns defaults, a valid subset POSTs and
persists, and invalid, unknown, malformed, and oversized bodies are rejected
without mutating stored state.
"""

import json
from pathlib import Path

import pytest

DEFAULTS = {"color": "indigo", "intensity": 5, "enable_animations": True}
MAX_BODY_BYTES = 16 * 1024


def test_get_returns_defaults_when_nothing_persisted(client, settings_url) -> None:
    res = client.get(settings_url)
    assert res.status_code == 200
    assert res.json() == DEFAULTS


def test_post_valid_subset_persists_and_merges(
    client, settings_url, manifest: dict, tmp_path: Path
) -> None:
    res = client.post(settings_url, json={"color": "crimson"})
    assert res.status_code == 200
    assert res.json() == {**DEFAULTS, "color": "crimson"}

    assert client.get(settings_url).json() == {**DEFAULTS, "color": "crimson"}

    persisted = json.loads(
        (tmp_path / f"{manifest['id']}.json").read_text(encoding="utf-8")
    )
    assert persisted["color"] == "crimson"


def test_post_full_valid_body_persists(client, settings_url) -> None:
    body = {"color": "amber", "intensity": 0, "enable_animations": False}
    assert client.post(settings_url, json=body).status_code == 200
    assert client.get(settings_url).json() == body


@pytest.mark.parametrize(
    "body",
    [
        {"color": "mauve"},
        {"intensity": 11},
        {"intensity": -1},
        {"intensity": "5"},
        {"intensity": True},
        {"enable_animations": "yes"},
        {"enable_animations": 1},
    ],
)
def test_post_invalid_value_is_rejected(client, settings_url, body: dict) -> None:
    assert client.post(settings_url, json=body).status_code == 400
    assert client.get(settings_url).json() == DEFAULTS


def test_post_unknown_key_is_rejected(client, settings_url) -> None:
    assert client.post(settings_url, json={"bogus": 1}).status_code == 400
    assert client.get(settings_url).json() == DEFAULTS


def test_post_non_object_body_is_rejected(client, settings_url) -> None:
    res = client.post(
        settings_url, content=b"[1, 2, 3]", headers={"content-type": "application/json"}
    )
    assert res.status_code == 400


def test_post_malformed_json_is_rejected(client, settings_url) -> None:
    res = client.post(
        settings_url, content=b"{not json", headers={"content-type": "application/json"}
    )
    assert res.status_code == 400


def test_post_oversized_body_is_rejected(client, settings_url) -> None:
    res = client.post(settings_url, content=b"x" * (MAX_BODY_BYTES + 1))
    assert res.status_code == 413
    assert client.get(settings_url).json() == DEFAULTS


def test_post_oversized_streamed_body_is_rejected(client, settings_url) -> None:
    # A generator body makes httpx use chunked transfer encoding, exercising the
    # streaming size cap rather than the Content-Length fast path.
    def chunks():
        for _ in range(20):
            yield b"x" * 1024

    assert client.post(settings_url, content=chunks()).status_code == 413
