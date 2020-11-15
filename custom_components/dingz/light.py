import logging

from homeassistant.components.light import (
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
    SUPPORT_TRANSITION,
    LightEntity,
)

from . import DingzCoordinator, DingzEntity
from .api import Dimmer, DimmerConfig
from .const import DOMAIN

logger = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    c: DingzCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [LED(c)]

    dimmers = await c.session.dimmer_config()
    for (i, config) in enumerate(dimmers):
        if not config.available:
            continue

        entities.append(DimmerEntity(c, config, i))

    async_add_entities(entities)


class LED(DingzEntity, LightEntity):
    @property
    def name(self):
        return f"{super().name} LED"

    @property
    def entity_picture(self):
        return f"{self._dingz_session.host}/favicon.ico"

    @property
    def brightness(self):
        _, _, v = self._dingz_state.led.hsv_values()
        return (255 * v) // 100

    @property
    def hs_color(self):
        h, s, _ = self._dingz_state.led.hsv_values()
        return [h, s]

    @property
    def is_on(self) -> bool:
        return self._dingz_state.led.on

    @property
    def supported_features(self):
        return SUPPORT_BRIGHTNESS | SUPPORT_COLOR

    @property
    def device_state_attributes(self):
        coordinator = self.coordinator
        state = self._dingz_state
        return {
            "front_color": coordinator.device.front_color,
            "wifi_ssid": state.wifi.ssid,
            "mac": state.wifi.mac,
            # these are only update after reboot
            "last_config_edit": state.config.timestamp_dt,
            "last_system_status": coordinator.system_config.system_status,
        }

    def _build_hsv(self, kwargs):
        brightness = kwargs.get("brightness")
        hs_color = kwargs.get("hs_color")
        if brightness is None and hs_color is None:
            return None

        h, s, v = self._dingz_state.led.hsv_values()
        if hs_color is not None:
            h, s = hs_color
        if brightness is not None:
            v = 100 * brightness / 255

        return h, s, v

    async def async_turn_on(self, **kwargs):
        await self._dingz_session.set_led(state=True, color=self._build_hsv(kwargs))
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self._dingz_session.set_led(state=False)
        await self.coordinator.async_request_refresh()


class DimmerEntity(DingzEntity, LightEntity):
    _config: DimmerConfig
    _index: int

    def __init__(self, coordinator, config, index) -> None:
        super().__init__(coordinator)
        self._config = config
        self._index = index

    @property
    def _dingz_dimmer(self) -> Dimmer:
        return self._dingz_state.dimmers[self._index]

    @property
    def name(self):
        return f"{super().name} {self._config.name}"

    @property
    def unique_id(self):
        return f"{super().unique_id}-{self._index}"

    @property
    def brightness(self):
        return (255 * self._dingz_dimmer.output) // 100

    @property
    def is_on(self) -> bool:
        return self._dingz_dimmer.on

    @property
    def supported_features(self):
        features = 0
        if self._config.dimmable:
            features |= SUPPORT_BRIGHTNESS
        return features

    @property
    def device_state_attributes(self):
        power_outputs = self._dingz_state.sensors.power_outputs
        if power_outputs:
            power_output = round(power_outputs[self._index], 1)
        else:
            power_output = None

        return {
            "output": self._config.output,
            "power": power_output,
        }

    async def async_turn_on(self, **kwargs):
        brightness = kwargs.get("brightness")
        if brightness is not None:
            value = 100 * brightness / 255
        else:
            value = None

        await self._dingz_session.set_dimmer(self._index, True, value=value)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self._dingz_session.set_dimmer(self._index, False)
        await self.coordinator.async_request_refresh()
