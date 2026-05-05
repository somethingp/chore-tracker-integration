"""Chore Tracker integration for Home Assistant."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.storage import Store

_LOGGER = logging.getLogger(__name__)

DOMAIN = "chore_tracker"
STORAGE_KEY = "chore_tracker_data"
STORAGE_VERSION = 1

# Read version from manifest so it's always in sync
_MANIFEST = json.loads((Path(__file__).parent / "manifest.json").read_text())
INTEGRATION_VERSION = _MANIFEST.get("version", "0.0.0")

DEFAULT_CHORES = [
    {"id": 1, "name": "Vacuum living room",  "freqDays": 7,  "lastDone": None, "lastBy": None, "history": []},
    {"id": 2, "name": "Take out trash",       "freqDays": 3,  "lastDone": None, "lastBy": None, "history": []},
    {"id": 3, "name": "Clean kitchen",        "freqDays": 2,  "lastDone": None, "lastBy": None, "history": []},
    {"id": 4, "name": "Wipe bathroom",        "freqDays": 7,  "lastDone": None, "lastBy": None, "history": []},
    {"id": 5, "name": "Mop floors",           "freqDays": 14, "lastDone": None, "lastBy": None, "history": []},
    {"id": 6, "name": "Change bed sheets",    "freqDays": 7,  "lastDone": None, "lastBy": None, "history": []},
]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Chore Tracker from a config entry."""

    # ── 1. Register card JS with Lovelace ────────────────────────────────────
    from .frontend import JSModuleRegistration
    registrar = JSModuleRegistration(hass, INTEGRATION_VERSION)
    await registrar.async_register()

    # ── 2. Load or initialise chore storage ──────────────────────────────────
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    data = await store.async_load()

    if data is None:
        data = {
            "chores": DEFAULT_CHORES,
            "nextId": len(DEFAULT_CHORES) + 1,
        }
        await store.async_save(data)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["store"] = store
    hass.data[DOMAIN]["data"] = data

    # ── 3. Register WebSocket commands ───────────────────────────────────────
    from . import websocket_api
    websocket_api.async_register_commands(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.pop(DOMAIN, None)
    return True
