from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_HS_COLOR,
    ATTR_TRANSITION,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import api
from .const import DOMAIN
from .shared import Shared, StateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    shared: Shared = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[LightEntity] = [FrontLed(shared.state)]
    async_add_entities(entities)


class FrontLed(CoordinatorEntity[StateCoordinator], LightEntity):
    def __init__(self, coordinator: StateCoordinator) -> None:
        super().__init__(coordinator)

        self._attr_has_entity_name = True
        self._attr_unique_id = f"{self.coordinator.shared.mac_addr}-front_led"
        self._attr_device_info = coordinator.shared.device_info
        self._attr_translation_key = "front"

        self._attr_supported_color_modes = {
            ColorMode.HS,
        }
        self._attr_color_mode = ColorMode.HS
        self._attr_supported_features = LightEntityFeature.TRANSITION

    @property
    def dingz_hsv_tuple(self) -> tuple[int, int, int] | None:
        try:
            raw = self.coordinator.data["led"]["hsv"]
        except LookupError:
            return None
        try:
            parts = tuple(map(int, raw.split(";")))
        except ValueError:
            return None
        if len(parts) != 3:
            return None
        return parts

    @property
    def brightness(self) -> int | None:
        hsv = self.dingz_hsv_tuple
        if hsv is None:
            return None
        return 255 * hsv[2] // 100

    @property
    def hs_color(self) -> tuple[float, float] | None:
        hsv = self.dingz_hsv_tuple
        if hsv is None:
            return None
        return hsv[0:2]

    @property
    def is_on(self) -> bool | None:
        try:
            return self.coordinator.data["led"]["on"]
        except LookupError:
            return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        try:
            brightness = kwargs[ATTR_BRIGHTNESS]
        except LookupError:
            brightness = self.brightness
        if brightness is None:
            brightness = 255

        try:
            h, s = kwargs[ATTR_HS_COLOR]
        except LookupError:
            hs = self.hs_color
            if hs is None:
                # default to white
                h, s = (0.0, 100.0)
            else:
                h, s = hs

        await self.coordinator.shared.client.set_led(
            api.SetLedState(
                action="on",
                color=f"{int(h)};{int(s)};{100 * brightness // 255}",
                mode="hsv",
                ramp=int(1000 * kwargs.get(ATTR_TRANSITION, 0.01)),
            )
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.shared.client.set_led(
            api.SetLedState(
                action="off",
                ramp=int(1000 * kwargs.get(ATTR_TRANSITION, 0.01)),
            )
        )
        await self.coordinator.async_request_refresh()
