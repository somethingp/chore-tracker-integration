"""WebSocket API for Chore Tracker."""
from __future__ import annotations

import time
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, callback
from homeassistant.components import websocket_api
import homeassistant.helpers.config_validation as cv

from . import DOMAIN


def async_register_commands(hass: HomeAssistant) -> None:
    """Register WebSocket commands."""
    websocket_api.async_register_command(hass, ws_get_chores)
    websocket_api.async_register_command(hass, ws_add_chore)
    websocket_api.async_register_command(hass, ws_delete_chore)
    websocket_api.async_register_command(hass, ws_complete_chore)
    websocket_api.async_register_command(hass, ws_undo_chore)


def _get_store_data(hass: HomeAssistant) -> dict:
    return hass.data[DOMAIN]["data"]


async def _save(hass: HomeAssistant) -> None:
    store = hass.data[DOMAIN]["store"]
    await store.async_save(hass.data[DOMAIN]["data"])


def _find_chore(data: dict, chore_id: int) -> dict | None:
    return next((c for c in data["chores"] if c["id"] == chore_id), None)


# ── get_chores ────────────────────────────────────────────────────────────────

@websocket_api.websocket_command({
    vol.Required("type"): "chore_tracker/get_chores",
})
@callback
def ws_get_chores(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Return all chores."""
    data = _get_store_data(hass)
    connection.send_result(msg["id"], data)


# ── add_chore ─────────────────────────────────────────────────────────────────

@websocket_api.websocket_command({
    vol.Required("type"): "chore_tracker/add_chore",
    vol.Required("name"): cv.string,
    vol.Required("freq_days"): vol.All(int, vol.Range(min=1)),
})
@websocket_api.async_response
async def ws_add_chore(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Add a new chore."""
    data = _get_store_data(hass)
    new_chore = {
        "id": data["nextId"],
        "name": msg["name"].strip(),
        "freqDays": msg["freq_days"],
        "lastDone": None,
        "lastBy": None,
        "history": [],
    }
    data["chores"].append(new_chore)
    data["nextId"] += 1
    await _save(hass)
    connection.send_result(msg["id"], new_chore)


# ── delete_chore ──────────────────────────────────────────────────────────────

@websocket_api.websocket_command({
    vol.Required("type"): "chore_tracker/delete_chore",
    vol.Required("chore_id"): int,
})
@websocket_api.async_response
async def ws_delete_chore(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Delete a chore."""
    data = _get_store_data(hass)
    before = len(data["chores"])
    data["chores"] = [c for c in data["chores"] if c["id"] != msg["chore_id"]]
    if len(data["chores"]) == before:
        connection.send_error(msg["id"], "not_found", "Chore not found")
        return
    await _save(hass)
    connection.send_result(msg["id"], {"success": True})


# ── complete_chore ────────────────────────────────────────────────────────────

@websocket_api.websocket_command({
    vol.Required("type"): "chore_tracker/complete_chore",
    vol.Required("chore_id"): int,
    vol.Required("user"): cv.string,
})
@websocket_api.async_response
async def ws_complete_chore(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Mark a chore as completed."""
    data = _get_store_data(hass)
    chore = _find_chore(data, msg["chore_id"])
    if not chore:
        connection.send_error(msg["id"], "not_found", "Chore not found")
        return

    chore["history"] = (chore.get("history") or [])
    chore["history"].append({"ts": chore["lastDone"], "by": chore["lastBy"]})
    chore["history"] = chore["history"][-20:]
    chore["lastDone"] = int(time.time() * 1000)
    chore["lastBy"] = msg["user"].strip() or "Unknown"

    await _save(hass)
    connection.send_result(msg["id"], chore)


# ── undo_chore ────────────────────────────────────────────────────────────────

@websocket_api.websocket_command({
    vol.Required("type"): "chore_tracker/undo_chore",
    vol.Required("chore_id"): int,
})
@websocket_api.async_response
async def ws_undo_chore(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Undo the last completion of a chore."""
    data = _get_store_data(hass)
    chore = _find_chore(data, msg["chore_id"])
    if not chore:
        connection.send_error(msg["id"], "not_found", "Chore not found")
        return
    if not chore.get("history"):
        connection.send_error(msg["id"], "nothing_to_undo", "No history to undo")
        return

    prev = chore["history"].pop()
    chore["lastDone"] = prev["ts"]
    chore["lastBy"] = prev["by"]

    await _save(hass)
    connection.send_result(msg["id"], chore)
