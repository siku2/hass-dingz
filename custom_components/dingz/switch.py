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
from .helpers import (
    DelayedCoordinatorRefreshMixin,
    UserAssignedNameMixin,
    compile_json_path,
    json_path_lookup,
)
from .shared import ConfigCoordinator, Shared, StateCoordinator


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

    for index, dingz_output in enumerate(shared.config.data.outputs):
        if (
            dingz_output.get("active", False)
            and dingz_output.get("type") == "power_socket"
        ):
            entities.append(PowerSocket(shared, index))

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


class PowerSocket(
    CoordinatorEntity[StateCoordinator],
    SwitchEntity,
    UserAssignedNameMixin,
    DelayedCoordinatorRefreshMixin,
):
    def __init__(self, shared: Shared, index: int) -> None:
        super().__init__(shared.state)
        self.__index = index

        self._attr_unique_id = (
            f"{self.coordinator.shared.mac_addr}-power_socket-{index}"
        )
        self._attr_device_info = shared.device_info
        self._attr_translation_key = "power_socket"

    @property
    def dingz_output_config(self) -> api.OutputConfig:
        try:
            return self.coordinator.shared.config.data.outputs[self.__index]
        except LookupError:
            return api.OutputConfig()

    @property
    def dingz_dimmer_state(self) -> api.StateDimmer:
        try:
            return self.coordinator.data["dimmers"][self.__index]
        except LookupError:
            return api.StateDimmer()

    @property
    def comp_index(self) -> int:
        return self.__index

    @property
    def user_given_name(self) -> str | None:
        return self.dingz_output_config.get("name")

    @property
    def is_on(self) -> bool | None:
        return self.dingz_dimmer_state.get("on")

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.shared.client.set_dimmer(self.__index, "on")
        await self.delayed_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.shared.client.set_dimmer(self.__index, "off")
        await self.delayed_request_refresh()
