import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import aiohttp_client

from .api import DingzSession, Info, DINGZ_INFO_TYPE
from .const import DOMAIN

logger = logging.getLogger(__name__)

FORM_SCHEMA = vol.Schema({vol.Required("host"): str})


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, info):
        errors = {}
        if info is not None:
            host: str = info["host"].rstrip("/")
            if not host.startswith(("http://", "https://")):
                host = f"http://{host}"

            session = aiohttp_client.async_get_clientsession(self.hass)
            session = DingzSession(session, host)
            try:
                info = await session.info()
            except Exception:
                logger.exception(f"failed to connect to {host!r}")
                errors["host"] = "connect_failed"
            else:
                if info.type == DINGZ_INFO_TYPE:
                    return self.async_create_entry(
                        title=info.mac[-6:], data={"host": host}
                    )
                else:
                    errors["host"] = "invalid_type"

        return self.async_show_form(
            step_id="user", data_schema=FORM_SCHEMA, errors=errors
        )
