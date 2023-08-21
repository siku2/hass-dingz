import abc
import asyncio
from typing import Any, cast

from homeassistant.core import callback
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from . import api
from .shared import InternalNotification, Shared, StateCoordinator


def compile_json_path(raw: str) -> list[str | int]:
    path = cast(list[str | int], raw.split("."))
    for i, seg in enumerate(path):
        if isinstance(seg, str) and seg.isdigit():
            path[i] = int(seg)
    return path


def json_path_lookup(value: Any, path: list[str | int]) -> Any | None:
    try:
        for key in path:
            value = value[key]
    except LookupError:
        return None
    return value


class UserAssignedNameMixin(Entity, abc.ABC):
    _attr_has_entity_name = True

    @property
    @abc.abstractmethod
    def comp_index(self) -> int:
        ...

    @property
    @abc.abstractmethod
    def user_given_name(self) -> str | None:
        ...

    @property
    def name(self) -> str | None:
        tr_key = self._name_translation_key
        if tr_key is None:
            return None

        name = self.user_given_name
        if not name:
            tr_key += "_fallback"

        tr_fmt: str | None = self.platform.platform_translations.get(tr_key)
        if tr_fmt is None:
            return None
        return tr_fmt.format(name=name, position=self.comp_index + 1)


class InternalNotificationMixin(Entity, abc.ABC):
    def __init__(self, shared: Shared) -> None:
        super().__init__()
        self.shared = shared

    @callback
    @abc.abstractmethod
    def handle_notification(self, notification: InternalNotification) -> None:
        ...

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self.shared.add_listener(self.handle_notification))


class DelayedCoordinatorRefreshMixin:
    async def delayed_request_refresh(self) -> None:
        # HACK: dingz takes some time to realize and update its internal state
        await asyncio.sleep(1.0)
        coordinator = cast(DataUpdateCoordinator[Any], self.coordinator)  # type: ignore
        await coordinator.async_request_refresh()


class DingzOutputEntity(CoordinatorEntity[StateCoordinator], UserAssignedNameMixin):
    def __init__(self, coordinator: StateCoordinator, *, index: int) -> None:
        super().__init__(coordinator)
        self.__index = index

        self._attr_device_info = self.coordinator.shared.device_info

    @property
    def comp_index(self) -> int:
        return self.__index

    @property
    def dingz_dimmer(self) -> api.StateDimmer:
        try:
            return self.coordinator.data["dimmers"][self.__index]
        except LookupError:
            return api.StateDimmer()

    @property
    def dingz_output_config(self) -> api.OutputConfig:
        try:
            return self.coordinator.shared.config.data.outputs[self.__index]
        except LookupError:
            return api.OutputConfig()

    @property
    def user_given_name(self) -> str | None:
        return self.dingz_output_config.get("name")


class CoordinatedNotificationStateEntity(
    CoordinatorEntity[StateCoordinator], InternalNotificationMixin, abc.ABC
):
    def __init__(self, shared: Shared) -> None:
        InternalNotificationMixin.__init__(self, shared)
        super().__init__(shared.state)

    @callback
    @abc.abstractmethod
    def handle_state_update(self) -> None:
        ...

    @callback
    def _handle_coordinator_update(self) -> None:
        self.handle_state_update()
        super()._handle_coordinator_update()
