from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue
from yarl import URL

from .const import CONF_BASE_URL, DOMAIN
from .shared import DingzConfigEntry, Shared

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.COVER,
    Platform.EVENT,
    Platform.FAN,
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.TEXT,
]


async def async_setup_entry(hass: HomeAssistant, entry: DingzConfigEntry) -> bool:
    shared = Shared(hass, entry, URL(entry.data[CONF_BASE_URL]))
    await shared.async_config_entry_first_refresh()

    entry.runtime_data = shared

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    shared.child_devices.async_remove_stale()
    entry.async_on_unload(
        shared.config.async_add_listener(shared.child_devices.async_update_names)
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: DingzConfigEntry) -> bool:
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.unload()

    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, entry: DingzConfigEntry) -> bool:
    if entry.minor_version < 2:
        async_create_issue(
            hass,
            DOMAIN,
            f"output_energy_dropped_{entry.entry_id}",
            is_fixable=False,
            is_persistent=True,
            severity=IssueSeverity.WARNING,
            translation_key="output_energy_dropped",
        )
        hass.config_entries.async_update_entry(entry, minor_version=2)

    return True
