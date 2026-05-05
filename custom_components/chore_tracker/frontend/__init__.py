"""Frontend resource registration for Chore Tracker."""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

URL_BASE = "/chore_tracker"
CARD_FILENAME = "chore-tracker-card.js"
FRONTEND_DIR = Path(__file__).parent


class JSModuleRegistration:
    """Registers the card JS with HA's HTTP server and Lovelace resources."""

    def __init__(self, hass: HomeAssistant, version: str) -> None:
        self.hass = hass
        self.version = version
        self._lovelace = hass.data.get("lovelace")

    async def async_register(self) -> None:
        """Register static path and Lovelace resource."""
        await self._register_path()
        lovelace_mode = getattr(
            self._lovelace, "mode",
            getattr(self._lovelace, "resource_mode", "yaml")
        )
        if lovelace_mode == "storage":
            await self._register_lovelace_resource()
        else:
            _LOGGER.info(
                "Chore Tracker: Lovelace is in YAML mode. "
                "Add this resource manually to ui-lovelace.yaml: "
                "url: %s/%s?v=%s type: module",
                URL_BASE, CARD_FILENAME, self.version,
            )

    async def _register_path(self) -> None:
        """Serve the card JS file."""
        await self.hass.http.async_register_static_paths([
            StaticPathConfig(
                f"{URL_BASE}/{CARD_FILENAME}",
                str(FRONTEND_DIR / CARD_FILENAME),
                cache_headers=False,
            )
        ])
        _LOGGER.debug("Chore Tracker: serving card at %s/%s", URL_BASE, CARD_FILENAME)

    async def _register_lovelace_resource(self) -> None:
        """Add the card to Lovelace resources if not already present."""
        try:
            resources = self._lovelace.resources
            await resources.async_load()

            url = f"{URL_BASE}/{CARD_FILENAME}"

            # Check if already registered
            for item in resources.async_items():
                if url in item.get("url", ""):
                    _LOGGER.debug("Chore Tracker: card resource already registered")
                    return

            # Add it
            await resources.async_create_item({
                "res_type": "module",
                "url": f"{url}?v={self.version}",
            })
            _LOGGER.info("Chore Tracker: registered card resource in Lovelace")

        except Exception as err:
            _LOGGER.warning(
                "Chore Tracker: could not auto-register Lovelace resource: %s. "
                "Add manually: URL=%s/%s?v=%s, type=module",
                err, URL_BASE, CARD_FILENAME, self.version,
            )
