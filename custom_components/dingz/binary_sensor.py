from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import api
from .const import DOMAIN
from .helpers import CoordinatedNotificationStateEntity, UserAssignedNameMixin
from .shared import InternalNotification, PirNotification, Shared, StateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    shared: Shared = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[BinarySensorEntity] = []
    for index, dingz_input in enumerate(shared.config.data.inputs):
        if dingz_input.get("active", False):
            entities.append(Input(shared.state, index=index))

    try:
        pirs = shared.state.data["sensors"]["pirs"]
    except LookupError:
        pirs = []
    for index, dingz_pir in enumerate(pirs):
        if dingz_pir and dingz_pir.get("enabled", False):
            entities.append(Motion(shared, index=index))

    async_add_entities(entities)


class Input(
    CoordinatorEntity[StateCoordinator], BinarySensorEntity, UserAssignedNameMixin
):
    _attr_translation_key = "input"

    def __init__(self, coordinator: StateCoordinator, *, index: int) -> None:
        super().__init__(coordinator)
        self.__index = index

        self._attr_unique_id = f"{self.coordinator.shared.mac_addr}-input-{index}"
        self._attr_device_info = self.coordinator.shared.device_info

    @property
    def dingz_input_config(self) -> api.InputConfig:
        try:
            return self.coordinator.shared.config.data.inputs[self.__index]
        except LookupError:
            return api.InputConfig()

    @property
    def comp_index(self) -> int:
        return self.__index

    @property
    def user_given_name(self) -> str | None:
        return self.dingz_input_config.get("name")

    @property
    def device_class(self) -> BinarySensorDeviceClass | None:
        try:
            input_ty = self.dingz_input_config["input"]["type"]
        except LookupError:
            return None

        if input_ty.startswith("pir_"):
            return BinarySensorDeviceClass.MOTION
        elif input_ty == "garage_door_state":
            return BinarySensorDeviceClass.GARAGE_DOOR
        else:
            return None

    @property
    def is_on(self) -> bool | None:
        try:
            raw = self.coordinator.data["sensors"]["input_state"]
        except LookupError:
            return None

        try:
            invert = self.dingz_input_config["input"]["invert"]
        except LookupError:
            invert = False
        return raw != invert


class Motion(CoordinatedNotificationStateEntity, BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.MOTION

    def __init__(self, shared: Shared, *, index: int) -> None:
        super().__init__(shared)
        self.__index = index
        self.__motion: bool | None = None

        self._attr_unique_id = f"{self.coordinator.shared.mac_addr}-motion-{index}"
        self._attr_device_info = self.coordinator.shared.device_info
        self._attr_translation_key = f"motion_{index}"

    @callback
    def handle_notification(self, notification: InternalNotification) -> None:
        if (
            isinstance(notification, PirNotification)
            and notification.index == self.__index
        ):
            self.__motion = notification.event_type != "n"
            self.async_write_ha_state()

    @callback
    def handle_state_update(self) -> None:
        self.__motion = self.dingz_pir.get("motion")

    @property
    def dingz_pir(self) -> api.SensorPir:
        try:
            raw = self.coordinator.data["sensors"]["pirs"][self.__index]
        except LookupError:
            return api.SensorPir()
        if raw is None:
            return api.SensorPir()
        return raw

    @property
    def is_on(self) -> bool | None:
        return self.__motion


class MqttOnline(CoordinatedNotificationStateEntity, BinarySensorEntity):
    pass
