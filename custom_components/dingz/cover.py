import logging
from typing import Any

from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import api
from .const import DOMAIN
from .helpers import (
    CoordinatedNotificationStateEntity,
    DelayedCoordinatorRefreshMixin,
    UserAssignedNameMixin,
)
from .shared import InternalNotification, MotorMotion, MotorStateNotification, Shared

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    shared: Shared = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[CoverEntity] = []

    try:
        blinds = shared.state.data["blinds"]
    except LookupError:
        blinds = []

    for index, _dingz_blind in enumerate(blinds):
        entities.append(Blind(shared, index=index))

    async_add_entities(entities)


class Blind(
    CoordinatedNotificationStateEntity,
    CoverEntity,
    UserAssignedNameMixin,
    DelayedCoordinatorRefreshMixin,
):
    _attr_translation_key = "blind"
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.SET_POSITION
        | CoverEntityFeature.STOP
        | CoverEntityFeature.OPEN_TILT
        | CoverEntityFeature.CLOSE_TILT
        | CoverEntityFeature.SET_TILT_POSITION
    )

    def __init__(self, shared: Shared, *, index: int) -> None:
        super().__init__(shared)
        self.__index = index
        self.__blind_state = api.StateBlind()

        self._attr_unique_id = f"f{shared.mac_addr}-{index}"
        self._attr_device_info = shared.device_info

    @property
    def dingz_blind_config(self) -> api.BlindConfig:
        try:
            return self.coordinator.shared.config.data.blinds[self.__index]
        except LookupError:
            return api.BlindConfig()

    @property
    def comp_index(self) -> int:
        return self.__index

    @property
    def user_given_name(self) -> str | None:
        return self.dingz_blind_config.get("name")

    @property
    def current_cover_position(self) -> int | None:
        return self.__blind_state.get("position")

    @property
    def current_cover_tilt_position(self) -> int | None:
        return self.__blind_state.get("lamella")

    @property
    def is_opening(self) -> bool | None:
        return self.__blind_state.get("moving") == "up"

    @property
    def is_closing(self) -> bool | None:
        return self.__blind_state.get("moving") == "down"

    @property
    def is_closed(self) -> bool | None:
        if (pos := self.current_cover_position) is not None:
            return pos == 0
        return None

    @callback
    def handle_notification(self, notification: InternalNotification) -> None:
        if not (
            isinstance(notification, MotorStateNotification)
            and notification.index == self.__index
        ):
            return

        self.__blind_state["lamella"] = notification.lamella
        self.__blind_state["position"] = notification.position
        match notification.motion:
            case MotorMotion.OPENING:
                self.__blind_state["moving"] = "up"
            case MotorMotion.CLOSING:
                self.__blind_state["moving"] = "down"
            case MotorMotion.STOPPED:
                self.__blind_state["moving"] = "stop"
            case _:
                pass

        self.async_write_ha_state()

    @callback
    def handle_state_update(self) -> None:
        try:
            state = self.coordinator.data["blinds"][self.__index]
        except LookupError:
            return
        self.__blind_state = state.copy()

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self.coordinator.shared.client.move_blind(self.__index, "up")
        await self.delayed_request_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self.coordinator.shared.client.move_blind(self.__index, "down")
        await self.delayed_request_refresh()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        await self.coordinator.shared.client.move_blind(self.__index, "stop")
        await self.delayed_request_refresh()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        await self.coordinator.shared.client.move_blind_position(
            self.__index, blind=kwargs[ATTR_POSITION]
        )
        await self.delayed_request_refresh()

    async def async_open_cover_tilt(self, **kwargs: Any) -> None:
        await self.coordinator.shared.client.move_blind_position(
            self.__index, lamella=100
        )
        await self.delayed_request_refresh()

    async def async_close_cover_tilt(self, **kwargs: Any) -> None:
        await self.coordinator.shared.client.move_blind_position(
            self.__index, lamella=0
        )
        await self.delayed_request_refresh()

    async def async_set_cover_tilt_position(self, **kwargs: Any) -> None:
        await self.coordinator.shared.client.move_blind_position(
            self.__index, lamella=kwargs[ATTR_TILT_POSITION]
        )
        await self.delayed_request_refresh()
