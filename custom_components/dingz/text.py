from homeassistant.components.text import TextEntity, TextEntityDescription
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

    entities: list[TextEntity] = [
        MqttJsonPath(
            shared.config,
            TextEntityDescription(
                key="uri",
                entity_category=EntityCategory.CONFIG,
                translation_key="mqtt_uri",
            ),
        ),
        MqttJsonPath(
            shared.config,
            TextEntityDescription(
                key="server.crt",
                entity_category=EntityCategory.CONFIG,
                translation_key="mqtt_server_crt",
            ),
            none_if_empty=True,
        ),
    ]

    async_add_entities(entities)


class MqttJsonPath(CoordinatorEntity[ConfigCoordinator], TextEntity):
    def __init__(
        self,
        coordinator: ConfigCoordinator,
        desc: TextEntityDescription,
        *,
        none_if_empty: bool = False,
    ) -> None:
        super().__init__(coordinator)

        self._attr_has_entity_name = True
        self._attr_unique_id = f"{self.coordinator.shared.mac_addr}-mqtt-{desc.key}"
        self._attr_device_info = self.coordinator.shared.device_info
        self.entity_description = desc

        self.__path = ["mqtt", *compile_json_path(desc.key)]
        self.__none_if_empty = none_if_empty

    @property
    def native_value(self) -> str | None:
        value = json_path_lookup(self.coordinator.data.services, self.__path)
        if value is None and self.__none_if_empty:
            value = ""
        return value

    async def async_set_value(self, value: str | None) -> None:
        value = value.strip() if value else None
        if self.__none_if_empty and value == "":
            value = None

        config = self.coordinator.data.services.get("mqtt", api.ServicesConfigMqtt())
        config[self.entity_description.key] = value
        await self.coordinator.shared.client.update_mqtt_service_config(config)
        await self.coordinator.async_request_refresh()
