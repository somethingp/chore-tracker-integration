"""Config flow for Chore Tracker."""
from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from . import DOMAIN


class ChoreTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Chore Tracker."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        # Only allow one instance
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title="Chore Tracker", data={})

        return self.async_show_form(step_id="user")
