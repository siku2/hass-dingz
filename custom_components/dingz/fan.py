import logging
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .helpers import DelayedCoordinatorRefreshMixin, DingzOutputEntity
from .shared import Shared, StateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    shared: Shared = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[FanEntity] = []

    for index, dingz_output in enumerate(shared.config.data.outputs):
        if dingz_output.get("active", False) and dingz_output.get("type") == "fan":
            entities.append(Fan(shared.state, index=index))

    async_add_entities(entities)


class Fan(
    DingzOutputEntity,
    FanEntity,
    DelayedCoordinatorRefreshMixin,
):
    _attr_translation_key = "fan"

    def __init__(self, coordinator: StateCoordinator, *, index: int) -> None:
        super().__init__(coordinator, index=index)

        self._attr_unique_id = f"f{coordinator.shared.mac_addr}-{index}"
        self._attr_supported_features = (
            FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
        )

    @property
    def is_on(self) -> bool | None:
        return self.dingz_dimmer.get("on")

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        await self.coordinator.shared.client.set_dimmer(self.comp_index, "on")
        await self.delayed_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.shared.client.set_dimmer(self.comp_index, "off")
        await self.delayed_request_refresh()
