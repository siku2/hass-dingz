import logging

from homeassistant.components.binary_sensor import BinarySensorEntity

from . import DingzCoordinator, DingzEntity
from .api import State
from .const import DOMAIN

logger = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    c: DingzCoordinator = hass.data[DOMAIN][entry.entry_id]
    state: State = c.data

    entities = [Brightness(c), Temperature(c)]
    if c.device.has_pir:
        pir_config = await c.session.pir_config()
        if pir_config.enabled:
            entities.append(Motion(c))

    if state.sensors.input_state is not None:
        entities.append(Input(c))

    async_add_entities(entities)


class Brightness(DingzEntity):
    @property
    def name(self):
        return f"{super().name} Brightness"

    @property
    def unique_id(self):
        return f"{super().unique_id}-brightness"

    @property
    def state(self):
        return self._dingz_state.sensors.brightness

    @property
    def device_state_attributes(self):
        sensors = self._dingz_state.sensors
        return {"light_state": sensors.light_state}

    @property
    def unit_of_measurement(self):
        return "lx"

    @property
    def device_class(self):
        return "illuminance"


class Motion(DingzEntity, BinarySensorEntity):
    @property
    def name(self):
        return f"{super().name} Motion"

    @property
    def unique_id(self):
        return f"{super().unique_id}-motion"

    @property
    def is_on(self):
        return bool(self._dingz_state.sensors.person_present)

    @property
    def device_state_attributes(self):
        sensors = self._dingz_state.sensors
        return {
            "light_off_timer": sensors.light_off_timer,
            "suspend_timer": sensors.suspend_timer,
        }

    @property
    def device_class(self):
        return "motion"


class Temperature(DingzEntity):
    @property
    def name(self):
        return f"{super().name} Temperature"

    @property
    def unique_id(self):
        return f"{super().unique_id}-temperature"

    @property
    def state(self):
        return self._dingz_state.sensors.room_temperature

    @property
    def device_state_attributes(self):
        sensors = self._dingz_state.sensors
        return {
            "cpu": sensors.cpu_temperature,
            "puck": sensors.puck_temperature,
            "fet": sensors.fet_temperature,
        }

    @property
    def unit_of_measurement(self):
        return "°C"

    @property
    def device_class(self):
        return "temperature"


class Input(DingzEntity, BinarySensorEntity):
    @property
    def name(self):
        return f"{super().name} Input"

    @property
    def unique_id(self):
        return f"{super().unique_id}-input"

    @property
    def is_on(self):
        return bool(self._dingz_state.sensors.input_state)

    @property
    def device_class(self):
        return "power"
