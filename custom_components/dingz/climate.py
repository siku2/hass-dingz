import logging
from typing import Any

from homeassistant.components.climate import (
    ATTR_TEMPERATURE,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import api
from .const import DOMAIN
from .helpers import DelayedCoordinatorRefreshMixin
from .shared import Shared, StateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    shared: Shared = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[ClimateEntity] = []

    try:
        # for some reason it's the 'active' field here instead of 'enabled'
        thermostat_enabled = shared.state.data["thermostat"]["active"]
    except LookupError:
        thermostat_enabled = False

    if thermostat_enabled:
        entities.append(Climate(shared.state))

    async_add_entities(entities)


class Climate(
    CoordinatorEntity[StateCoordinator], ClimateEntity, DelayedCoordinatorRefreshMixin
):
    def __init__(self, coordinator: StateCoordinator) -> None:
        super().__init__(coordinator)

        self._attr_has_entity_name = True
        self._attr_unique_id = coordinator.shared.mac_addr
        self._attr_device_info = coordinator.shared.device_info
        self._attr_name = None  # since there's only one thermostat, use the device name

        self._attr_temperature_unit = "°C"
        self._attr_target_temperature_step = 1.0  # from web frontend
        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE

    @property
    def current_temperature(self) -> float | None:
        try:
            return self.coordinator.data["thermostat"]["temp"]
        except LookupError:
            return False

    @property
    def target_temperature(self) -> float | None:
        try:
            return self.coordinator.data["thermostat"]["target_temp"]
        except LookupError:
            return None

    @property
    def max_temp(self) -> float:
        try:
            return self.coordinator.data["thermostat"]["max_target_temp"]
        except LookupError:
            return 120  # taken from web frontend

    @property
    def min_temp(self) -> float:
        try:
            return self.coordinator.data["thermostat"]["min_target_temp"]
        except LookupError:
            return -55  # taken from web frontend

    @property
    def hvac_mode(self) -> HVACMode | None:
        try:
            raw = self.coordinator.data["thermostat"]["mode"]
        except LookupError:
            return None
        return dingz_to_hvac_mode(raw)

    @property
    def hvac_modes(self) -> list[HVACMode]:
        return [HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT]

    @property
    def hvac_action(self) -> HVACAction | None:
        try:
            raw = self.coordinator.data["thermostat"]["state"]
        except LookupError:
            return None
        return dingz_to_hvac_action(raw)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        await self.coordinator.shared.client.update_thermostat_config(
            api.ThermostatConfig(
                enable=hvac_mode != HVACMode.OFF,
                free_cooling=hvac_mode != HVACMode.OFF,
                cooling=hvac_mode == HVACMode.COOL,
            )
        )
        await self.delayed_request_refresh()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        config = api.ThermostatConfig()

        if value := kwargs.get(ATTR_TEMPERATURE):
            config["target_temp"] = value

        if not config:
            return

        await self.coordinator.shared.client.update_thermostat_config(config)
        await self.delayed_request_refresh()


def dingz_to_hvac_mode(value: api.ThermostatModeEnum) -> HVACMode | None:
    match value:
        case "cooling":
            return HVACMode.COOL
        case "heating":
            return HVACMode.HEAT
        case "off":
            return HVACMode.OFF

    _LOGGER.warning(f"invalid HVAC mode: {value!r}")
    return None


def dingz_to_hvac_action(value: api.ThermostatStateEnum) -> HVACAction | None:
    match value:
        case "cooling":
            return HVACAction.COOLING
        case "heating":
            return HVACAction.HEATING
        case "off":
            return HVACAction.OFF

    _LOGGER.warning(f"invalid HVAC action: {value!r}")
    return None
