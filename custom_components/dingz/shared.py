import contextlib
import dataclasses
import json
import logging
from collections.abc import Callable
from datetime import timedelta
from enum import IntEnum
from typing import Any, Literal, cast

from homeassistant.components import mqtt
from homeassistant.components.mqtt.subscription import (
    async_prepare_subscribe_topics,
    async_subscribe_topics,
    async_unsubscribe_topics,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from yarl import URL

from . import api
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class Shared:
    hass: HomeAssistant
    client: api.Client

    state: "StateCoordinator"
    config: "ConfigCoordinator"

    def __init__(
        self,
        hass: HomeAssistant,
        base_url: URL,
    ) -> None:
        self.hass = hass
        self.client = api.Client(async_get_clientsession(hass), base_url)
        self.state = StateCoordinator(self)
        self.config = ConfigCoordinator(self)

        self._device_info = DeviceInfo()
        self._mac_addr: str | None = None
        self._notifier = _Notifier()
        self._sub_state = None

    @property
    def device_info(self) -> DeviceInfo:
        return self._device_info

    @property
    def mac_addr(self) -> str:
        assert self._mac_addr is not None
        return self._mac_addr

    async def async_config_entry_first_refresh(self) -> None:
        await self.state.async_config_entry_first_refresh()

        with contextlib.suppress(LookupError):
            self._mac_addr = dr.format_mac(self.state.data["wifi"]["mac"])

        await self.config.async_config_entry_first_refresh()

        self._device_info.update(
            DeviceInfo(
                configuration_url=str(self.client.base_url),
                connections={(dr.CONNECTION_NETWORK_MAC, self.mac_addr)},
                identifiers={(DOMAIN, self.mac_addr)},
                manufacturer="iolo AG",
                model=self.config.data.device.get("puck_hw_model"),
                name=self.config.data.system.get("dingz_name"),
                suggested_area=self.config.data.system.get("room_name"),
                sw_version=self.config.data.device.get("fw_version"),
                hw_version=self.config.data.device.get("hw_version"),
            )
        )

        if mqtt.mqtt_config_entry_enabled(self.hass):
            _LOGGER.info("enabling mqtt integration")
            dingz_id = self.config.data.system.get("id", "")
            self._sub_state = async_prepare_subscribe_topics(
                self.hass,
                self._sub_state,
                {
                    "online": {
                        "topic": f"dingz/{dingz_id}/online",
                        "msg_callback": self._handle_mqtt_online,
                    },
                    "pir": {
                        "topic": f"dingz/{dingz_id}/+/event/pir/+",
                        "msg_callback": self._handle_mqtt_pir,
                    },
                    "button": {
                        "topic": f"dingz/{dingz_id}/+/event/button/+",
                        "msg_callback": self._handle_mqtt_button,
                    },
                    "motor": {
                        "topic": f"dingz/{dingz_id}/+/state/motor/+",
                        "msg_callback": self._handle_mqtt_motor,
                    },
                    "sensor": {
                        "topic": f"dingz/{dingz_id}/+/sensor/+",
                        "msg_callback": self._handle_mqtt_sensor,
                    },
                },
            )
            await async_subscribe_topics(self.hass, self._sub_state)

    async def unload(self) -> None:
        self._sub_state = async_unsubscribe_topics(self.hass, self._sub_state)

    def add_listener(self, callback: "_NotificationCallbackT") -> Callable[[], None]:
        return self._notifier.add_listener(callback)

    async def _handle_mqtt_online(self, msg: mqtt.ReceiveMessage) -> None:
        self._notifier.dispatch(MqttOnlineNotification(online=msg.payload == "true"))

    async def _handle_mqtt_pir(self, msg: mqtt.ReceiveMessage) -> None:
        (_, _, raw) = msg.topic.rpartition("/")
        index = int(raw)
        event_type = cast(_PirEventType, msg.payload)
        self._notifier.dispatch(PirNotification(index=index, event_type=event_type))

    async def _handle_mqtt_button(self, msg: mqtt.ReceiveMessage) -> None:
        (_, _, raw) = msg.topic.rpartition("/")
        index = int(raw)
        self._notifier.dispatch(
            ButtonNotification(index=index, event_type=cast(Any, msg.payload))
        )

    async def _handle_mqtt_motor(self, msg: mqtt.ReceiveMessage) -> None:
        (_, _, raw) = msg.topic.rpartition("/")
        index = int(raw)

        try:
            payload: dict[str, Any] | Any = json.loads(msg.payload)
            if not isinstance(payload, dict):
                raise TypeError()
        except (json.JSONDecodeError, TypeError):
            _LOGGER.error(
                "ignoring broken motor notification (topic = %s): %s",
                msg.topic,
                msg.payload,
            )
            return

        self._notifier.dispatch(
            MotorStateNotification(
                index=index,
                position=payload["position"],
                goal=payload.get("goal"),
                lamella=payload["lamella"],
                motion=MotorMotion(payload["motion"]),
            )
        )

    async def _handle_mqtt_sensor(self, msg: mqtt.ReceiveMessage) -> None:
        (_, _, sensor) = msg.topic.rpartition("/")

        try:
            value = float(msg.payload)
        except ValueError:
            _LOGGER.error(
                "ignoring broken sensor notification (topic = %s): %s",
                msg.topic,
                msg.payload,
            )
            return
        self._notifier.dispatch(
            SimpleSensorStateNotification(sensor=cast(Any, sensor), value=value)
        )


class StateCoordinator(DataUpdateCoordinator[api.State]):
    shared: Shared

    def __init__(
        self,
        shared: Shared,
    ) -> None:
        super().__init__(
            shared.hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=30)
        )
        self.shared = shared

    async def _async_update_data(self) -> api.State:
        try:
            return await self.shared.client.get_state()
        except Exception:
            _LOGGER.exception("update state data failed")
            raise


class ConfigCoordinator(DataUpdateCoordinator[api.FullDeviceConfig]):
    shared: Shared

    def __init__(
        self,
        shared: Shared,
    ) -> None:
        super().__init__(
            shared.hass, _LOGGER, name=DOMAIN, update_interval=timedelta(minutes=5)
        )
        self.shared = shared

    async def _async_update_data(self) -> api.FullDeviceConfig:
        try:
            return await self.shared.client.get_full_device_config()
        except Exception:
            _LOGGER.exception("update config data failed")
            raise


@dataclasses.dataclass(slots=True)
class InternalNotification:
    ...


@dataclasses.dataclass(slots=True, kw_only=True)
class MqttOnlineNotification(InternalNotification):
    online: bool


_PirEventType = Literal["s"] | Literal["ss"] | Literal["n"]


@dataclasses.dataclass(slots=True, kw_only=True)
class PirNotification(InternalNotification):
    index: int
    event_type: _PirEventType


@dataclasses.dataclass(slots=True, kw_only=True)
class ButtonNotification(InternalNotification):
    index: int
    event_type: Literal["p"] | Literal["r"] | Literal["h"] | Literal["m1"] | Literal[
        "m2"
    ] | Literal["m3"] | Literal["m4"] | Literal["m5"]


class MotorMotion(IntEnum):
    STOPPED = 0
    OPENING = 1
    CLOSING = 2
    CALIBRATING = 3


@dataclasses.dataclass(slots=True, kw_only=True)
class MotorStateNotification(InternalNotification):
    index: int
    position: int
    goal: int | None
    lamella: int
    motion: MotorMotion


@dataclasses.dataclass(slots=True, kw_only=True)
class SimpleSensorStateNotification(InternalNotification):
    sensor: Literal["light"] | Literal["temperature"]
    value: float


_NotificationCallbackT = Callable[[InternalNotification], None]


class _Notifier:
    def __init__(self) -> None:
        self._listeners: dict[Callable[[], None], _NotificationCallbackT] = {}

    def add_listener(self, callback: _NotificationCallbackT) -> Callable[[], None]:
        def remove_listener() -> None:
            self._listeners.pop(remove_listener)

        self._listeners[remove_listener] = callback
        return remove_listener

    def dispatch(self, notification: InternalNotification) -> None:
        _LOGGER.debug("dispatching %s", notification)
        for update_callback in list(self._listeners.values()):
            update_callback(notification)
