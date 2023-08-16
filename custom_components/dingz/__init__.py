from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from yarl import URL

from .const import DOMAIN
from .shared import Shared

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.EVENT,
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.TEXT,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    shared = Shared(hass, URL(entry.data["base_url"]))
    await shared.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = shared

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        shared: Shared | None = hass.data[DOMAIN].pop(entry.entry_id)
        if shared:
            await shared.unload()

    return unload_ok
