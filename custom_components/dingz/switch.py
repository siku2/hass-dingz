from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import api
from .helpers import DelayedCoordinatorRefreshMixin
from .shared import DingzConfigEntry, Shared, StateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: DingzConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    shared = config_entry.runtime_data

    entities: list[SwitchEntity] = []

    for index, dingz_output in enumerate(shared.config.data.outputs):
        if (
            dingz_output.get("active", False)
            and dingz_output.get("type") == "power_socket"
        ):
            entities.append(PowerSocket(shared, index))

    async_add_entities(entities)


class PowerSocket(
    CoordinatorEntity[StateCoordinator],
    SwitchEntity,
    DelayedCoordinatorRefreshMixin,
):
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, shared: Shared, index: int) -> None:
        super().__init__(shared.state)
        self.__index = index

        self._attr_unique_id = (
            f"{self.coordinator.shared.mac_addr}-power_socket-{index}"
        )
        self._attr_device_info = shared.child_devices.device_info("output", index)

    @property
    def dingz_dimmer_state(self) -> api.StateDimmer:
        try:
            return self.coordinator.data["dimmers"][self.__index]
        except LookupError:
            return api.StateDimmer()

    @property
    def is_on(self) -> bool | None:
        return self.dingz_dimmer_state.get("on")

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.shared.client.set_dimmer(self.__index, "on")
        await self.delayed_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.shared.client.set_dimmer(self.__index, "off")
        await self.delayed_request_refresh()
