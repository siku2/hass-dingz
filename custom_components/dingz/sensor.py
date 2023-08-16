from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt

from . import api
from .const import DOMAIN
from .helpers import UserAssignedNameMixin, compile_json_path, json_path_lookup
from .shared import Shared, StateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    shared: Shared = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[SensorEntity] = [
        JsonPathSensor(
            shared.state,
            SensorEntityDescription(
                key="sensors.brightness",
                device_class=SensorDeviceClass.ILLUMINANCE,
                native_unit_of_measurement="lx",
                state_class=SensorStateClass.MEASUREMENT,
                translation_key="brightness",
            ),
        ),
        JsonPathSensor(
            shared.state,
            SensorEntityDescription(
                key="sensors.light_state",
                device_class=SensorDeviceClass.ENUM,
                options=["day", "night", "twilight"],
                translation_key="light_state",
            ),
        ),
        JsonPathSensor(
            shared.state,
            SensorEntityDescription(
                key="time",
                device_class=SensorDeviceClass.TIMESTAMP,
                translation_key="state_time",
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
            transform_fn=_dt_with_hass_tz,
        ),
        JsonPathSensor(
            shared.state,
            SensorEntityDescription(
                key="config.timestamp",
                device_class=SensorDeviceClass.TIMESTAMP,
                translation_key="config_timestamp",
                entity_category=EntityCategory.CONFIG,
            ),
            transform_fn=lambda raw: dt.utc_from_timestamp(raw),
        ),
    ]

    def dyn_light_enabled() -> bool:
        try:
            return shared.config.data.system["dyn_light"]["enable"]
        except LookupError:
            return False

    entities.append(
        JsonPathSensor(
            shared.state,
            SensorEntityDescription(
                key="dyn_light.mode",
                device_class=SensorDeviceClass.ENUM,
                options=["day", "night", "twilight"],
                translation_key="dyn_light",
            ),
            enabled_fn=dyn_light_enabled,
        )
    )

    for name, is_diag in (
        ("room_temperature", False),
        ("uncompensated_temperature", True),
        ("cpu_temperature", True),
        ("puck_temperature", True),
        ("fet_temperature", True),
    ):
        entities.append(
            JsonPathSensor(
                shared.state,
                SensorEntityDescription(
                    key=f"sensors.{name}",
                    device_class=SensorDeviceClass.TEMPERATURE,
                    native_unit_of_measurement="°C",
                    state_class=SensorStateClass.MEASUREMENT,
                    entity_category=EntityCategory.DIAGNOSTIC if is_diag else None,
                    translation_key=name,
                ),
            )
        )

    for index in range(len(shared.config.data.outputs)):
        entities.append(OutputPower(shared.state, index=index))

    async_add_entities(entities)


def _dt_with_hass_tz(s: str) -> datetime | None:
    parsed = dt.parse_datetime(s)
    if parsed is None:
        return None
    return dt.as_utc(parsed)


class OutputPower(
    CoordinatorEntity[StateCoordinator], SensorEntity, UserAssignedNameMixin
):
    def __init__(self, coordinator: StateCoordinator, *, index: int) -> None:
        super().__init__(coordinator)

        self.__index = index

        key = f"output-power-{index}"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{self.coordinator.shared.mac_addr}-{key}"
        self._attr_device_info = self.coordinator.shared.device_info
        self.entity_description = SensorEntityDescription(
            key=key,
            device_class=SensorDeviceClass.POWER,
            native_unit_of_measurement="W",
            state_class=SensorStateClass.MEASUREMENT,
            translation_key="output_power",
        )

    @property
    def dingz_output(self) -> api.OutputConfig:
        try:
            return self.coordinator.shared.config.data.outputs[self.__index]
        except LookupError:
            return api.OutputConfig()

    @property
    def entity_registry_enabled_default(self) -> bool:
        return self.dingz_output.get("active", False)

    @property
    def comp_index(self) -> int:
        return self.__index

    @property
    def user_given_name(self) -> str | None:
        return self.dingz_output.get("name")

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        try:
            power_outputs = self.coordinator.data["sensors"]["power_outputs"]
            power_output = power_outputs[self.__index]
        except LookupError:
            return None
        return power_output.get("value")


class JsonPathSensor(CoordinatorEntity[StateCoordinator], SensorEntity):
    def __init__(
        self,
        coordinator: StateCoordinator,
        desc: SensorEntityDescription,
        *,
        transform_fn: Callable[[Any], StateType | date | datetime | Decimal]
        | None = None,
        enabled_fn: Callable[[], bool] | None = None,
    ) -> None:
        super().__init__(coordinator)

        self._attr_has_entity_name = True
        self._attr_unique_id = f"{self.coordinator.shared.mac_addr}-{desc.key}"
        self._attr_device_info = self.coordinator.shared.device_info
        self.entity_description = desc

        self.__path = compile_json_path(desc.key)
        self.__transform_fn = transform_fn
        self.__enabled_fn = enabled_fn

    @property
    def entity_registry_enabled_default(self) -> bool:
        if not self.__enabled_fn:
            return super().entity_registry_enabled_default
        return self.__enabled_fn()

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        value = json_path_lookup(self.coordinator.data, self.__path)
        if value is None:
            return None
        if self.__transform_fn:
            return self.__transform_fn(value)
        return value
