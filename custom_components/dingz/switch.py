from typing import Any

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import api
from .const import DOMAIN
from .helpers import compile_json_path, json_path_lookup
from .shared import ConfigCoordinator, Shared


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    shared: Shared = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[SwitchEntity] = [
        MqttJsonPath(
            shared.config,
            SwitchEntityDescription(
                key="enable",
                entity_category=EntityCategory.CONFIG,
                device_class=SwitchDeviceClass.SWITCH,
                translation_key="mqtt_enable",
            ),
        ),
    ]

    async_add_entities(entities)


class MqttJsonPath(CoordinatorEntity[ConfigCoordinator], SwitchEntity):
    def __init__(
        self,
        coordinator: ConfigCoordinator,
        desc: SwitchEntityDescription,
    ) -> None:
        super().__init__(coordinator)

        self._attr_has_entity_name = True
        self._attr_unique_id = f"{self.coordinator.shared.mac_addr}-mqtt-{desc.key}"
        self._attr_device_info = self.coordinator.shared.device_info
        self.entity_description = desc

        self.__path = ["mqtt", *compile_json_path(desc.key)]

    @property
    def is_on(self) -> bool | None:
        value = json_path_lookup(self.coordinator.data.services, self.__path)
        return value

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set(False)

    async def _set(self, value: bool) -> None:
        config = self.coordinator.data.services.get("mqtt", api.ServicesConfigMqtt())
        config[self.entity_description.key] = value
        await self.coordinator.shared.client.update_mqtt_service_config(config)
        await self.coordinator.async_request_refresh()
