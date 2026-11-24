from typing import TYPE_CHECKING, Literal

from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import ChildDeviceInfo

from .const import DOMAIN

if TYPE_CHECKING:
    from .shared import Shared

type ChildDeviceKind = Literal["output", "blind", "ddi"]

_OUTPUT_TYPES_WITH_NAME = ("light", "fan", "power_socket")


class ChildDevices:
    def __init__(self, shared: Shared) -> None:
        self._shared = shared
        self._parent_device_id: str | None = None

    @callback
    def register_parent(self) -> None:
        shared = self._shared
        parent = dr.async_get(shared.hass).async_get_or_create_from_info(
            config_entry_id=shared.entry.entry_id,
            device_info=shared.device_info,
        )
        self._parent_device_id = parent.id

    def device_info(self, kind: ChildDeviceKind, index: int) -> ChildDeviceInfo:
        assert self._parent_device_id is not None
        name, translation_key = self._name_and_translation_key(kind, index)
        identifiers = {self._identifier(kind, index)}
        if name:
            return ChildDeviceInfo(
                identifiers=identifiers,
                parent_device_id=self._parent_device_id,
                name=name,
            )
        return ChildDeviceInfo(
            identifiers=identifiers,
            parent_device_id=self._parent_device_id,
            translation_key=translation_key,
            translation_placeholders={"position": str(index + 1)},
        )

    @callback
    def async_update_names(self) -> None:
        dev_reg = dr.async_get(self._shared.hass)
        for kind, index in self._expected_keys():
            dev_reg.async_get_or_create_child_from_info(
                config_entry_id=self._shared.entry.entry_id,
                device_info=self.device_info(kind, index),
            )

    @callback
    def async_remove_stale(self) -> None:
        dev_reg = dr.async_get(self._shared.hass)
        expected = {
            self._identifier(kind, index) for kind, index in self._expected_keys()
        }
        for device in dr.async_child_entries_for_config_entry(
            dev_reg, self._shared.entry.entry_id
        ):
            if device.identifiers.isdisjoint(expected):
                dev_reg.async_remove_device(device.id)

    def _identifier(self, kind: ChildDeviceKind, index: int) -> tuple[str, str]:
        return (DOMAIN, f"{self._shared.mac_addr}-{kind}-{index}")

    def _expected_keys(self) -> list[tuple[ChildDeviceKind, int]]:
        shared = self._shared
        keys: list[tuple[ChildDeviceKind, int]] = [
            ("output", index)
            for index, output in enumerate(shared.config.data.outputs)
            if output.get("active", False)
        ]
        keys.extend(
            ("blind", index)
            for index in range(len(shared.state.data.get("blinds", [])))
        )
        if shared.config.data.device.get("ddi_base", False):
            keys.extend(
                ("ddi", index)
                for index, ddi in enumerate(shared.config.data.ddi_channels)
                if ddi.get("en", False)
            )
        return keys

    def _name_and_translation_key(
        self, kind: ChildDeviceKind, index: int
    ) -> tuple[str | None, str]:
        config = self._shared.config.data
        try:
            match kind:
                case "output":
                    output = config.outputs[index]
                    output_type = output.get("type")
                    if output_type in _OUTPUT_TYPES_WITH_NAME:
                        return output.get("name"), f"output_{output_type}"
                    return output.get("name"), "output"
                case "blind":
                    return config.blinds[index].get("name"), "blind"
                case "ddi":
                    return config.ddi_channels[index].get("name"), "ddi"
        except LookupError:
            return None, kind
