from homeassistant.components.number import NumberDeviceClass, NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .shared import ConfigCoordinator, Shared


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    shared: Shared = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[NumberEntity] = [
        TemperatureOffset(shared.config),
    ]

    async_add_entities(entities)


class TemperatureOffset(CoordinatorEntity[ConfigCoordinator], NumberEntity):
    def __init__(
        self,
        coordinator: ConfigCoordinator,
    ) -> None:
        super().__init__(coordinator)

        self._attr_has_entity_name = True
        self._attr_unique_id = f"{self.coordinator.shared.mac_addr}-temp-offset"
        self._attr_device_info = self.coordinator.shared.device_info
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_translation_key = "temperature_offset"

        self._attr_device_class = NumberDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = "°C"
        # these values were taken from the dingz frontend
        self._attr_native_step = 0.5
        self._attr_native_min_value = -30
        self._attr_native_max_value = 30

    @property
    def native_value(self) -> float | None:
        try:
            return self.coordinator.data.system["temp_offset"]
        except LookupError:
            return None

    async def async_set_native_value(self, value: float) -> None:
        value = round(value, 1)  # the frontend also rounds to 0.1
        await self.coordinator.shared.client.set_temp_offset(value)
        await self.coordinator.async_request_refresh()
        # also request refresh for state because it holds the room temperature
        await self.coordinator.shared.state.async_request_refresh()
