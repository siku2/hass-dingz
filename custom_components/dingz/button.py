from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .shared import DingzConfigEntry, Shared


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: DingzConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    shared = config_entry.runtime_data

    entities: list[ButtonEntity] = [
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

    def __init__(self, shared: Shared, desc: ButtonEntityDescription) -> None:
        self.shared = shared

        self._attr_has_entity_name = True
        self._attr_unique_id = f"{shared.mac_addr}-{desc.key}"
        self._attr_device_info = shared.device_info
        self.entity_description = desc

    async def async_press(self) -> None:
        method = getattr(self.shared.client, self.entity_description.key)
        assert callable(method)
        await method()


class ResetPirTime(ButtonEntity):
    shared: Shared

    def __init__(self, shared: Shared, index: int) -> None:
        self.shared = shared
        self.__index = index

        self._attr_has_entity_name = True
        self._attr_unique_id = f"{shared.mac_addr}-reset-pir-{index}"
        self._attr_device_info = shared.device_info
        self._attr_translation_key = f"reset_pir_time_{index}"

    async def async_press(self) -> None:
        await self.shared.client.reset_pir_time(self.__index)
        await self.shared.state.async_request_refresh()
