from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import api
from .const import DOMAIN
from .shared import Shared


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    shared: Shared = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[ButtonEntity] = [
        Action(
            shared,
            ButtonEntityDescription(
                key="save_default_config",
                entity_category=EntityCategory.CONFIG,
                translation_key="save_default_config",
            ),
            # config timestamp is stored in state
            refresh_state=True,
        ),
        Action(
            shared,
            ButtonEntityDescription(
                key="reboot",
                device_class=ButtonDeviceClass.RESTART,
                entity_category=EntityCategory.DIAGNOSTIC,
                translation_key="reboot",
            ),
        ),
    ]

    try:
        pirs = shared.state.data["sensors"]["pirs"]
    except LookupError:
        pirs = []
    for index, dingz_pir in enumerate(pirs):
        if dingz_pir and dingz_pir.get("enabled", False):
            entities.append(ResetPirTime(shared, index=index))

    async_add_entities(entities)


class Action(ButtonEntity):
    shared: Shared

    def __init__(
        self,
        shared: Shared,
        desc: ButtonEntityDescription,
        *,
        refresh_state: bool = False,
        refresh_config: bool = False,
    ) -> None:
        self.shared = shared

        self._attr_has_entity_name = True
        self._attr_unique_id = f"{shared.mac_addr}-{desc.key}"
        self._attr_device_info = shared.device_info
        self.entity_description = desc

        self.__refresh_state = refresh_state
        self.__refresh_config = refresh_config

    async def async_press(self) -> None:
        method = getattr(self.shared.client, self.entity_description.key)
        assert callable(method)
        await method()

        if self.__refresh_state:
            await self.shared.state.async_request_refresh()
        if self.__refresh_config:
            await self.shared.config.async_request_refresh()


class ResetPirTime(ButtonEntity):
    shared: Shared

    def __init__(self, shared: Shared, index: int) -> None:
        self.shared = shared
        self.__index = index

        self._attr_has_entity_name = True
        self._attr_unique_id = f"{shared.mac_addr}-reset-pir-{index}"
        self._attr_device_info = shared.device_info
        self._attr_translation_key = f"reset_pir_time_{index}"

    @property
    def dingz_pir(self) -> api.SensorPir:
        try:
            raw = self.shared.state.data["sensors"]["pirs"][self.__index]
        except LookupError:
            return api.SensorPir()
        if raw is None:
            return api.SensorPir()
        return raw

    async def async_press(self) -> None:
        await self.shared.client.reset_pir_time(self.__index)
        await self.shared.state.async_request_refresh()
