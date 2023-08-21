import contextlib

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import api
from .const import DOMAIN
from .helpers import (
    CoordinatedNotificationStateEntity,
    InternalNotificationMixin,
    UserAssignedNameMixin,
)
from .shared import (
    InputStateNotification,
    InternalNotification,
    MqttOnlineNotification,
    PirNotification,
    Shared,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    shared: Shared = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[BinarySensorEntity] = [MqttOnline(shared)]

    for index, dingz_input in enumerate(shared.config.data.inputs):
        if dingz_input.get("active", False):
            entities.append(Input(shared, index=index))

    try:
        pirs = shared.state.data["sensors"]["pirs"]
    except LookupError:
        pirs = []
    for index, dingz_pir in enumerate(pirs):
        if dingz_pir and dingz_pir.get("enabled", False):
            entities.append(Motion(shared, index=index))

    async_add_entities(entities)


class Input(
    CoordinatedNotificationStateEntity, BinarySensorEntity, UserAssignedNameMixin
):
    _attr_translation_key = "input"

    def __init__(self, shared: Shared, *, index: int) -> None:
        super().__init__(shared)
        self.__index = index
        self.__is_on: bool | None = None

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
            return BinarySensorDeviceClass.POWER

    @callback
    def handle_notification(self, notification: InternalNotification) -> None:
        if not (
            isinstance(notification, InputStateNotification)
            and notification.index == self.__index
        ):
            return
        self.__is_on = notification.on
        self.async_write_ha_state()

    @callback
    def handle_state_update(self) -> None:
        with contextlib.suppress(LookupError):
            self.__is_on = self.coordinator.data["sensors"]["input_state"]

    @property
    def is_on(self) -> bool | None:
        return self.__is_on


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
        if not (
            isinstance(notification, PirNotification)
            and notification.index == self.__index
        ):
            return
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


class MqttOnline(InternalNotificationMixin, BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "mqtt_online"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, shared: Shared) -> None:
        super().__init__(shared)
        self.__online = False

        self._attr_unique_id = f"{shared.mac_addr}-mqtt_online"
        self._attr_device_info = shared.device_info

    @callback
    def handle_notification(self, notification: InternalNotification) -> None:
        if not isinstance(notification, MqttOnlineNotification):
            return
        self.__online = notification.online
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool | None:
        return self.__online
