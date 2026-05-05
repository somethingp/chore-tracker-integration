"""Chore Tracker integration for Home Assistant."""
from __future__ import annotations

import logging
import time
from pathlib import Path

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.storage import Store
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace import _LOADED_LOVELACE_MODULES

_LOGGER = logging.getLogger(__name__)

DOMAIN = "chore_tracker"
STORAGE_KEY = "chore_tracker_data"
STORAGE_VERSION = 1

# The card JS is served from /chore_tracker/chore-tracker-card.js
CARD_URL = f"/{DOMAIN}/chore-tracker-card.js"
CARD_FILE = Path(__file__).parent / "www" / "chore-tracker-card.js"

DEFAULT_CHORES = [
    {"id": 1, "name": "Vacuum living room",  "freqDays": 7,  "lastDone": None, "lastBy": None, "history": []},
    {"id": 2, "name": "Take out trash",       "freqDays": 3,  "lastDone": None, "lastBy": None, "history": []},
    {"id": 3, "name": "Clean kitchen",        "freqDays": 2,  "lastDone": None, "lastBy": None, "history": []},
    {"id": 4, "name": "Wipe bathroom",        "freqDays": 7,  "lastDone": None, "lastBy": None, "history": []},
    {"id": 5, "name": "Mop floors",           "freqDays": 14, "lastDone": None, "lastBy": None, "history": []},
    {"id": 6, "name": "Change bed sheets",    "freqDays": 7,  "lastDone": None, "lastBy": None, "history": []},
]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Chore Tracker integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Chore Tracker from a config entry."""

    # ── 1. Serve the card JS as a static file ────────────────────────────────
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(CARD_FILE), cache_headers=False)]
    )
    _LOGGER.debug("Chore Tracker: serving card at %s", CARD_URL)

    # ── 2. Auto-register with Lovelace so it appears without manual resource ─
    await _async_register_lovelace_resource(hass)

    # ── 3. Load or initialise chore storage ──────────────────────────────────
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

    # ── 4. Register WebSocket API commands ───────────────────────────────────
    from . import websocket_api
    websocket_api.async_register_commands(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.data.pop(DOMAIN, None)
    return True


async def _async_register_lovelace_resource(hass: HomeAssistant) -> None:
    """Register the card JS with Lovelace as a module resource."""
    try:
        # HA's Lovelace integration stores resources in .storage/lovelace_resources
        lovelace_store = Store(hass, 1, "lovelace_resources")
        resources_data = await lovelace_store.async_load() or {"items": []}
        items = resources_data.get("items") or []

        # Check if already registered (avoid duplicates)
        for item in items:
            if item.get("url", "").startswith(CARD_URL.split("?")[0]):
                _LOGGER.debug("Chore Tracker card already registered in Lovelace resources")
                return

        # Add the resource with a version bust so updates are picked up
        version = int(time.time())
        items.append({
            "id": DOMAIN,
            "type": "module",
            "url": f"{CARD_URL}?v={version}",
        })
        resources_data["items"] = items
        await lovelace_store.async_save(resources_data)
        _LOGGER.info("Chore Tracker: registered card resource in Lovelace")

    except Exception as err:  # pylint: disable=broad-except
        # Non-fatal — user can add the resource manually if this fails
        _LOGGER.warning(
            "Chore Tracker: could not auto-register Lovelace resource: %s. "
            "Add it manually: URL=%s, type=module",
            err,
            CARD_URL,
        )
