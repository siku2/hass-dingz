from homeassistant.components.event import EventDeviceClass, EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import api
from .const import DOMAIN
from .helpers import InternalNotificationMixin, UserAssignedNameMixin
from .shared import ButtonNotification, InternalNotification, PirNotification, Shared


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    shared: Shared = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[EventEntity] = []

    try:
        mqtt_enabled = shared.config.data.services["mqtt"]["enable"]
    except LookupError:
        mqtt_enabled = False

    if mqtt_enabled:
        try:
            pirs = shared.state.data["sensors"]["pirs"]
        except LookupError:
            pirs = []
        for index, dingz_pir in enumerate(pirs):
            if dingz_pir and dingz_pir.get("enabled", False):
                entities.append(Pir(shared, index=index))

        try:
            buttons = shared.config.data.buttons["buttons"]
        except LookupError:
            buttons = []
        for index, dingz_button in enumerate(buttons):
            if dingz_button.get("active", False):
                entities.append(Button(shared, index=index))

    async_add_entities(entities)


class Pir(InternalNotificationMixin, EventEntity):
    _attr_has_entity_name = True
    _attr_device_class = EventDeviceClass.MOTION
    _attr_event_types = ["s", "ss", "n"]

    def __init__(self, shared: Shared, index: int) -> None:
        super().__init__(shared)
        self.__index = index

        self._attr_unique_id = f"{shared.mac_addr}-pir-{index}"
        self._attr_device_info = shared.device_info
        self._attr_translation_key = f"pir_{index}"

    @callback
    def handle_notification(self, notification: InternalNotification) -> None:
        if not (
            isinstance(notification, PirNotification)
            and notification.index == self.__index
        ):
            return
        self._trigger_event(notification.event_type)
        self.async_write_ha_state()


class Button(InternalNotificationMixin, EventEntity, UserAssignedNameMixin):
    _attr_translation_key = "button"
    _attr_device_class = EventDeviceClass.BUTTON
    _attr_event_types = [
        "p",
        "r",
        "h",
        "m1",
        "m2",
        "m3",
        "m4",
        "m5",
    ]

    def __init__(self, shared: Shared, index: int) -> None:
        super().__init__(shared)
        self.__index = index

        self._attr_unique_id = f"{shared.mac_addr}-button-{index}"
        self._attr_device_info = shared.device_info

    @property
    def dingz_button_config(self) -> api.ButtonConfig:
        try:
            return self.shared.config.data.buttons["buttons"][self.__index]
        except LookupError:
            return api.ButtonConfig()

    @property
    def comp_index(self) -> int:
        return self.__index

    @property
    def user_given_name(self) -> str | None:
        return self.dingz_button_config.get("name")

    @callback
    def handle_notification(self, notification: InternalNotification) -> None:
        if not (
            isinstance(notification, ButtonNotification)
            and notification.index == self.__index
        ):
            return
        self._trigger_event(notification.event_type)
        self.async_write_ha_state()
