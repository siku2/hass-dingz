import dataclasses
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .const import CONF_BASE_URL
from .shared import DingzConfigEntry

TO_REDACT = {
    CONF_BASE_URL,
    "dns",
    "front_sn",
    "gateway",
    "id",
    "ip",
    "lat",
    "long",
    "mac",
    "mask",
    "puck_sn",
    "rest_password",
    "server.crt",
    "ssid",
    "sunrise",
    "sunset",
    "uri",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: DingzConfigEntry
) -> dict[str, Any]:
    shared = entry.runtime_data
    return async_redact_data(
        {
            "entry": {
                "data": dict(entry.data),
                "options": dict(entry.options),
                "version": entry.version,
                "minor_version": entry.minor_version,
            },
            "state": shared.state.data,
            "config": dataclasses.asdict(shared.config.data),
            "ram": shared.diag.data,
        },
        TO_REDACT,
    )
