from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue
from yarl import URL

from .const import CONF_BASE_URL, DOMAIN
from .shared import DingzConfigEntry, Shared

_MQTT_CONFIG_UNIQUE_ID_SUFFIXES = ("-mqtt-enable", "-mqtt-uri", "-mqtt-server.crt")

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
]


async def async_setup_entry(hass: HomeAssistant, entry: DingzConfigEntry) -> bool:
    shared = Shared(hass, entry, URL(entry.data[CONF_BASE_URL]))
    entry.async_on_unload(shared.async_unload)
    await shared.async_config_entry_first_refresh()

    entry.runtime_data = shared

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    shared.child_devices.async_remove_stale()
    entry.async_on_unload(
        shared.config.async_add_listener(shared.child_devices.async_update_names)
    )

    return True


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: DingzConfigEntry, device: dr.AnyDeviceEntry
) -> bool:
    if entry.state is not ConfigEntryState.LOADED:
        return True
    return not entry.runtime_data.child_devices.in_use(device)


async def async_unload_entry(hass: HomeAssistant, entry: DingzConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


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

    if entry.minor_version < 3:
        if _remove_mqtt_config_entities(hass, entry):
            async_create_issue(
                hass,
                DOMAIN,
                f"mqtt_config_moved_{entry.entry_id}",
                is_fixable=False,
                is_persistent=True,
                severity=IssueSeverity.WARNING,
                translation_key="mqtt_config_moved",
                translation_placeholders={"title": entry.title},
            )
        hass.config_entries.async_update_entry(entry, minor_version=3)

    return True


def _remove_mqtt_config_entities(hass: HomeAssistant, entry: DingzConfigEntry) -> bool:
    ent_reg = er.async_get(hass)
    removed = False
    for entity in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        if entity.unique_id.endswith(_MQTT_CONFIG_UNIQUE_ID_SUFFIXES):
            ent_reg.async_remove(entity.entity_id)
            removed = True
    return removed
