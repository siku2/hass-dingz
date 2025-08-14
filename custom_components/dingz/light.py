from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_HS_COLOR,
    ATTR_TRANSITION,
    LightEntity,
)
from homeassistant.components.light.const import (
    ColorMode,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import api
from .const import DOMAIN
from .helpers import (
    CoordinatedNotificationStateEntity,
    DelayedCoordinatorRefreshMixin,
    UserAssignedNameMixin,
)
from .shared import (
    InternalNotification,
    LightStateNotification,
    Shared,
    StateCoordinator,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    shared: Shared = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[LightEntity] = [FrontLed(shared.state)]

    for index, dingz_output in enumerate(shared.config.data.outputs):
        if dingz_output.get("active", False) and dingz_output.get("type") == "light":
            entities.append(Dimmer(shared, index))
    if shared.config.data.device.get("ddi_base", False):
        for index, ddi in enumerate(shared.config.data.ddi_channels):
            if ddi.get("en", False):
                entities.append(Ddi(shared, index))

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


class Dimmer(
    CoordinatedNotificationStateEntity,
    LightEntity,
    UserAssignedNameMixin,
    DelayedCoordinatorRefreshMixin,
):
    _attr_supported_features = LightEntityFeature.TRANSITION

    def __init__(self, shared: Shared, index: int) -> None:
        super().__init__(shared)
        self.__index = index

        self._attr_unique_id = f"{self.coordinator.shared.mac_addr}-dimmer-{index}"
        self._attr_device_info = shared.device_info
        self._attr_translation_key = "dimmer"

    @property
    def dingz_output_config(self) -> api.OutputConfig:
        try:
            return self.coordinator.shared.config.data.outputs[self.__index]
        except LookupError:
            return api.OutputConfig()

    @property
    def dingz_dimmable(self) -> bool:
        try:
            return self.dingz_output_config["light"]["dimmable"]
        except LookupError:
            return False

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
    def color_mode(self) -> ColorMode | str | None:
        return ColorMode.BRIGHTNESS if self.dingz_dimmable else ColorMode.ONOFF

    @property
    def supported_color_modes(self) -> set[ColorMode] | set[str] | None:
        return {ColorMode.BRIGHTNESS} if self.dingz_dimmable else {ColorMode.ONOFF}

    @callback
    def handle_notification(self, notification: InternalNotification) -> None:
        if not (
            isinstance(notification, LightStateNotification)
            and notification.index == self.__index
        ):
            return
        match notification.turn:
            case "on":
                self._attr_is_on = True
            case "off":
                self._attr_is_on = False

        self._attr_brightness = 255 * notification.brightness // 100
        self.async_write_ha_state()

    @callback
    def handle_state_update(self) -> None:
        self._attr_is_on = self.dingz_dimmer_state.get("on")
        if (output := self.dingz_dimmer_state.get("output")) is not None:
            self._attr_brightness = 255 * output // 100

    async def async_turn_on(self, **kwargs: Any) -> None:
        try:
            brightness = kwargs[ATTR_BRIGHTNESS]
        except LookupError:
            value = None
        else:
            value = 100 * brightness // 255

        await self.coordinator.shared.client.set_dimmer(
            self.__index, "on", value=value, time=kwargs.get(ATTR_TRANSITION)
        )
        await self.delayed_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.shared.client.set_dimmer(
            self.__index, "off", time=kwargs.get(ATTR_TRANSITION)
        )
        await self.delayed_request_refresh()


class Ddi(
    CoordinatedNotificationStateEntity,
    LightEntity,
    UserAssignedNameMixin,
    DelayedCoordinatorRefreshMixin,
):
    _attr_supported_features = LightEntityFeature.TRANSITION

    def __init__(self, shared: Shared, index: int) -> None:
        super().__init__(shared)
        self.__index = index

        self._attr_unique_id = f"{self.coordinator.shared.mac_addr}-ddi-{index}"
        self._attr_device_info = shared.device_info
        self._attr_translation_key = "ddi"

        self._attr_min_color_temp_kelvin = 2700
        # TODO: why does the api return 404 for values > 6500?
        self._attr_max_color_temp_kelvin = 6500

    @property
    def dingz_ddi_channel_config(self) -> api.DdiChannelConfig:
        try:
            return self.coordinator.shared.config.data.ddi_channels[self.__index]
        except LookupError:
            return api.DdiChannelConfig()

    @property
    def dingz_ddi_channel_state(self) -> api.StateDdiChannel:
        try:
            return self.coordinator.data["ddi_channels"][self.__index]
        except LookupError:
            return api.StateDdiChannel()

    @property
    def comp_index(self) -> int:
        return self.__index

    @property
    def user_given_name(self) -> str | None:
        return self.dingz_ddi_channel_config.get("name")

    @property
    def color_mode(self) -> ColorMode:
        # DDI always supports brightness
        return (
            ColorMode.COLOR_TEMP
            if self.dingz_ddi_channel_state.get("ct_enabled", False)
            else ColorMode.BRIGHTNESS
        )

    @property
    def supported_color_modes(self) -> set[ColorMode] | set[str] | None:
        return {ColorMode.COLOR_TEMP}

    @callback
    def handle_notification(self, notification: InternalNotification) -> None:
        # TODO: implement
        return
        # if not (
        #     isinstance(notification, LightStateNotification)
        #     and notification.index == self.__index
        # ):
        #     return
        # match notification.turn:
        #     case "on":
        #         self._attr_is_on = True
        #     case "off":
        #         self._attr_is_on = False

        # self._attr_brightness = 255 * notification.brightness // 100
        # self.async_write_ha_state()

    @callback
    def handle_state_update(self) -> None:
        channel_state = self.dingz_ddi_channel_state
        self._attr_is_on = channel_state.get("on")
        if (output := channel_state.get("brightness")) is not None:
            self._attr_brightness = 255 * output // 100
        if (temp := channel_state.get("colour_temperature_k")) is not None:
            self._attr_color_temp_kelvin = temp

    async def async_turn_on(self, **kwargs: Any) -> None:
        color_temperature = kwargs.get(ATTR_COLOR_TEMP_KELVIN)
        brightness = kwargs.get(ATTR_BRIGHTNESS)

        try:
            brightness = kwargs[ATTR_BRIGHTNESS]
        except LookupError:
            brightness = None
        else:
            brightness = 100 * brightness // 255

        if brightness is None and color_temperature is not None:
            # TODO: ct cannot be set without brightness
            brightness = self.dingz_ddi_channel_state.get("brightness")
            # If it's still None, we'll let the device deal with it.

        await self.coordinator.shared.client.set_ddi_channel(
            self.__index,
            "on",
            brightness=brightness,
            color_temperature=color_temperature,
            time=kwargs.get(ATTR_TRANSITION),
        )
        await self.delayed_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.shared.client.set_ddi_channel(
            self.__index,
            "off",
            time=kwargs.get(ATTR_TRANSITION),
        )
        await self.delayed_request_refresh()
