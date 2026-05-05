"""Chore Tracker integration for Home Assistant."""
from __future__ import annotations

import logging
import time
from pathlib import Path

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.storage import Store
from homeassistant.components.http import StaticPathConfig

_LOGGER = logging.getLogger(__name__)

DOMAIN = "chore_tracker"
STORAGE_KEY = "chore_tracker_data"
STORAGE_VERSION = 1

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
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Chore Tracker from a config entry."""

    # ── 1. Serve the card JS as a static file ────────────────────────────────
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(CARD_FILE), cache_headers=False)]
    )

    # ── 2. Register card with Lovelace resources ─────────────────────────────
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

    # ── 4. Register WebSocket commands ───────────────────────────────────────
    from . import websocket_api
    websocket_api.async_register_commands(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.pop(DOMAIN, None)
    return True


async def _async_register_lovelace_resource(hass: HomeAssistant) -> None:
    """Write the card URL into .storage/lovelace_resources."""
    try:
        lovelace_store = Store(hass, 1, "lovelace_resources")
        data = await lovelace_store.async_load() or {"items": []}
        items = data.setdefault("items", [])

        # Avoid duplicates
        for item in items:
            if CARD_URL in item.get("url", ""):
                return

        items.append({
            "id": DOMAIN,
            "type": "module",
            "url": f"{CARD_URL}?v={int(time.time())}",
        })
        await lovelace_store.async_save(data)
        _LOGGER.info("Chore Tracker: registered Lovelace card resource")

    except Exception as err:
        _LOGGER.warning(
            "Chore Tracker: could not register Lovelace resource automatically (%s). "
            "Add it manually: URL=%s, type=module",
            err, CARD_URL,
        )
