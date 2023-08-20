import asyncio
import dataclasses
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any, Literal, TypedDict, cast

import aiohttp
from yarl import URL

_LOGGER = logging.getLogger(__name__)


class Index(TypedDict, total=False):
    relative: int
    absolute: int


class StateDimmer(TypedDict, total=False):
    on: bool
    output: int
    ramp: int
    readonly: bool
    index: Index


class StateBlindPosition(TypedDict, total=False):
    blind: int
    lamella: int


class StateBlind(TypedDict, total=False):
    target: StateBlindPosition
    current: StateBlindPosition
    readonly: bool
    index: Index


class StateLed(TypedDict, total=False):
    on: bool
    hsv: str
    rgb: str
    mode: str
    ramp: int


class SetLedState(TypedDict, total=False):
    action: Literal["on"] | Literal["off"] | Literal["toggle"]
    color: str
    mode: str
    ramp: int


class SensorPir(TypedDict, total=False):
    enabled: bool
    motion: bool
    mode: str
    light_off_timer: int
    suspend_timer: int


class SensorPowerOutput(TypedDict, total=False):
    value: int


class StateSensors(TypedDict, total=False):
    brightness: int
    light_state: str
    light_state_lpf: str
    room_temperature: float
    uncompensated_temperature: float
    temp_offset: float
    cpu_temperature: float
    puck_temperature: float
    fet_temperature: float
    input_state: bool
    pirs: list[SensorPir | None]
    power_outputs: list[SensorPowerOutput]


class StateDynLight(TypedDict, total=False):
    mode: str


ThermostatModeEnum = Literal["off"] | Literal["heating"] | Literal["cooling"]
ThermostatStateEnum = Literal["off"] | Literal["heating"] | Literal["cooling"]


class StateThermostat(TypedDict, total=False):
    active: bool
    state: ThermostatStateEnum
    mode: ThermostatModeEnum
    enabled: bool
    target_temp: int
    min_target_temp: int
    max_target_temp: int
    temp: float


class StateWifi(TypedDict, total=False):
    version: str
    mac: str
    ssid: str
    ip: str
    mask: str
    gateway: str
    dns: str
    static: bool
    connected: bool


class StateConfig:
    timestamp: int


class State(TypedDict, total=False):
    dimmers: list[StateDimmer]
    blinds: list[StateBlind]
    led: StateLed
    sensors: StateSensors
    dyn_light: StateDynLight
    thermostat: StateThermostat
    wifi: StateWifi
    config: StateConfig
    time: str


class Device(TypedDict, total=False):
    type: str
    battery: bool
    reachable: bool
    meshroot: bool
    fw_version: str
    hw_version: str
    fw_version_puck: str
    bl_version_puck: str
    hw_version_puck: str
    hw_id_puck: int
    puck_sn: str
    puck_production_date: Any
    dip_config: int
    dip_static: bool
    dip_misconf: bool
    puck_hw_model: str
    front_hw_model: str
    front_production_date: str
    front_sn: str
    front_color: str
    has_pir: bool
    hash: str


DeviceResponseT = dict[str, Device]


class SystemConfigTempComp(TypedDict, total=False):
    fet_offset: float
    gain_up: float
    gain_down: float
    gain_total: float


class DynLightSunOffset(TypedDict, total=False):
    day: int
    twilight: int
    night: int


class SystemConfigDynLight(TypedDict, total=False):
    enable: bool
    phases: int
    source: str
    sun_offset: DynLightSunOffset


class TimeOfDay(TypedDict, total=False):
    hour: int
    minute: int


class SystemConfig(TypedDict, total=False):
    protected_status: bool
    allow_reset: bool
    allow_wps: bool
    allow_reboot: bool
    allow_remote_reboot: bool
    origin: bool
    upgrade_blink: bool
    reboot_blink: bool
    dingz_name: str
    room_name: str
    id: str
    temp_offset: float
    fet_offset: float
    cpu_offset: float
    temp_comp: SystemConfigTempComp
    sun_offset: float
    tzid: int
    lat: float
    long: float
    dyn_light: SystemConfigDynLight
    wifi_ps: bool
    time: str
    sunrise: TimeOfDay
    sunset: TimeOfDay
    system_status: str


class OutputConfigFeedback(TypedDict, total=False):
    color: str
    brightness: int


class OutputConfigLightDimmerRange(TypedDict, total=False):
    min: int
    max: int


class OutputConfigLightDimmerDynamic(TypedDict, total=False):
    day: int
    twilight: int
    night: int


class OutputConfigLightDimmer(TypedDict, total=False):
    type: str
    use_last_value: bool
    range: OutputConfigLightDimmerRange
    dynamic: OutputConfigLightDimmerDynamic


class OutputConfigLightOnOffGroupOn(TypedDict, total=False):
    day: bool
    twilight: bool
    night: bool


class OutputConfigLightOnOff(TypedDict, total=False):
    group_on: OutputConfigLightOnOffGroupOn


class OutputConfigLight(TypedDict, total=False):
    dimmable: bool
    dimmer: OutputConfigLightDimmer
    onoff: OutputConfigLightOnOff


class OutputConfig(TypedDict, total=False):
    active: bool
    name: str
    type: Literal["light"] | Literal["fan"] | str
    groups: str
    feedback: OutputConfigFeedback
    light: OutputConfigLight
    heater: dict[str, Any]
    pulse: dict[str, Any]
    fan: dict[str, Any]
    garage_door: dict[str, Any]
    valve: dict[str, Any]


class OutputConfigs(TypedDict, total=False):
    outputs: list[OutputConfig]


class InputConfigType(TypedDict, total=False):
    light: bool
    motor: bool


class InputConfigInput(TypedDict, total=False):
    type: Literal["button_push"] | Literal["button_toggle"] | Literal[
        "pir_linked"
    ] | Literal["pir_independent"] | Literal["contact_state"] | Literal[
        "contact_free_cooling"
    ] | Literal[
        "garage_door_state"
    ]
    invert: bool
    contact_free_cooling: Any


class InputConfig(TypedDict, total=False):
    active: bool
    name: str
    icon: int
    mode: Any
    local_type: InputConfigType
    type: InputConfigType
    actions: Any
    outputs: Any
    motors: Any
    feedback: Any
    carousel: bool
    input: InputConfigInput


class InputConfigs(TypedDict, total=False):
    inputs: list[InputConfig]


class ServicesConfigRemoteButtonsTargets(TypedDict, total=False):
    btn1: Any
    btn2: Any
    btn3: Any
    btn4: Any
    input: Any
    pir: Any


class ServicesConfigRemoteButtons(TypedDict, total=False):
    enable: bool
    targets: ServicesConfigRemoteButtonsTargets


ServicesConfigMqtt = TypedDict(
    "ServicesConfigMqtt",
    {
        "uri": str,
        "enable": bool,
        "server.crt": str | None,
    },
    total=False,
)


class ServicesConfig(TypedDict, total=False):
    mystrom: bool
    homekit: bool
    rest_api: bool
    panel: bool
    aws: bool
    discovery: bool
    udp_search: bool
    aws_notifies: bool
    ssdp: bool
    mdns: bool
    mdns_search: bool
    homekit_configured: bool
    cloud_ping: bool
    broadcast_period: int
    mdns_search_period: int
    remote_buttons: ServicesConfigRemoteButtons
    mqtt: ServicesConfigMqtt


class ThermostatConfig(TypedDict, total=False):
    active: bool
    min_target_temp: int
    max_target_temp: int
    target_temp: int
    cooling: bool
    enable: bool
    fahrenheit: bool
    free_cooling: bool
    groups: str
    mode: dict[str, Any]
    feedback: dict[str, Any]
    outputs: list[Any]


class ButtonConfig(TypedDict, total=False):
    active: bool
    name: str
    icon: int
    mode: dict[str, Any]
    local_type: InputConfigType
    type: InputConfigType
    actions: dict[str, Any]
    outputs: dict[str, Any]
    motors: dict[str, Any]
    feedback: dict[str, Any]
    carousel: bool
    button: dict[str, Any]


class ButtonsConfig(TypedDict, total=False):
    dingz_orientation: str
    buttons: list[ButtonConfig]


@dataclasses.dataclass(slots=True, kw_only=True)
class FullDeviceConfig:
    device: Device
    system: SystemConfig
    services: ServicesConfig
    inputs: list[InputConfig]
    outputs: list[OutputConfig]
    buttons: ButtonsConfig


class _ReqThrottleLock(asyncio.Lock):
    throttle_duration: float

    def __init__(self, duration: float) -> None:
        super().__init__()

        self.throttle_duration = duration
        self._last_release_at: float | None = None

    async def acquire(self) -> Literal[True]:
        res = await super().acquire()
        if self._last_release_at:
            passed = time.time() - self._last_release_at
            remaining = self.throttle_duration - passed
            if remaining > 0:
                await asyncio.sleep(remaining)
        return res

    def release(self) -> None:
        self._last_release_at = time.time()
        return super().release()


class Client:
    @property
    def base_url(self) -> URL:
        return self._base_url

    def __init__(
        self,
        session: aiohttp.ClientSession,
        base_url: URL | str,
    ) -> None:
        self._session = session
        self._base_url = URL(base_url)
        self._lock = _ReqThrottleLock(
            0.2
        )  # 200ms for the dingz to recover after every request

    async def _get(
        self, path: str, *, attempts: int = 5, retry_delay: float = 1.0
    ) -> Any:
        url = self._base_url / "api/v1" / path

        async def once() -> Any:
            _LOGGER.debug("fetching from %s", url)
            async with self._session.get(url, raise_for_status=True) as resp:
                return await resp.json()

        async with self._lock:
            return await _repeat(once, attempts=attempts, retry_delay=retry_delay)

    async def _post(
        self,
        path: str,
        data: dict[str, Any] | str,
        *,
        as_query_params: bool = False,
        attempts: int = 3,
        retry_delay: float = 3.0,
    ) -> None:
        url = self._base_url / "api/v1" / path
        kwargs = {}
        if isinstance(data, str):
            kwargs["data"] = data
        elif as_query_params:
            kwargs["params"] = data
        else:
            kwargs["json"] = data

        async def once() -> None:
            _LOGGER.debug("post to %s with payload %s", url, data)
            async with self._session.post(url, **kwargs) as resp:
                resp.raise_for_status()

        async with self._lock:
            return await _repeat(once, attempts=attempts, retry_delay=retry_delay)

    async def _post_services_config(self, config: ServicesConfig) -> None:
        await self._post("services_config", cast(dict[str, Any], config))

    async def _post_system_config(self, config: SystemConfig) -> None:
        await self._post("system_config", cast(dict[str, Any], config))

    async def get_state(self) -> State:
        return await self._get("state")

    async def get_device(self) -> DeviceResponseT:
        return await self._get("device")

    async def get_system_config(self) -> SystemConfig:
        return await self._get("system_config")

    async def get_output_config(self) -> OutputConfigs:
        return await self._get("output_config")

    async def get_input_config(self) -> InputConfigs:
        return await self._get("input_config")

    async def get_services_config(self) -> ServicesConfig:
        return await self._get("services_config")

    async def get_buttons_config(self) -> ButtonsConfig:
        return await self._get("button_config")

    async def get_full_device_config(self) -> FullDeviceConfig:
        devices = await self.get_device()
        device = next(iter(devices.values()), Device())
        system = await self.get_system_config()
        services = await self.get_services_config()
        buttons = await self.get_buttons_config()

        input_config = await self.get_input_config()
        inputs = input_config.get("inputs", [])

        output_config = await self.get_output_config()
        outputs = output_config.get("outputs", [])

        return FullDeviceConfig(
            device=device,
            system=system,
            services=services,
            inputs=inputs,
            outputs=outputs,
            buttons=buttons,
        )

    async def update_mqtt_service_config(self, config: ServicesConfigMqtt) -> None:
        await self._post_services_config(ServicesConfig(mqtt=config))

    async def update_thermostat_config(self, config: ThermostatConfig) -> None:
        await self._post("thermostat_config", cast(dict[str, Any], config))

    async def set_temp_offset(self, offset: float) -> None:
        await self._post_system_config(SystemConfig(temp_offset=offset))

    async def set_led(self, state: SetLedState) -> None:
        # we roll our own encoding here because dingz doesn't support proper form-encoding. semicolons are usually escaped, but dingz can't deal with that at all
        encoded = "&".join(f"{key}={value}" for key, value in state.items())
        await self._post("led/set", encoded)

    async def set_dimmer(
        self,
        index: int,
        action: Literal["on"]
        | Literal["off"]
        | Literal["toggle"]
        | Literal["dim"]
        | Literal["pulse"],
        *,
        value: int | None = None,
        ramp: int | None = None,
        time: float | None = None,
        reset_manual_time: bool | None = None,
    ) -> None:
        params = {
            key: value
            for key, value in (
                ("value", value),
                ("ramp", ramp),
                ("time", time),
                ("reset_manual_time", reset_manual_time),
            )
            if value is not None
        }
        await self._post(f"dimmer/{index}/{action}", params, as_query_params=True)

    async def move_blind(
        self,
        index: int,
        action: Literal["stop"]
        | Literal["up"]
        | Literal["down"]
        | Literal["initialize"]
        | Literal["upstop"]
        | Literal["downstop"]
        | Literal["togglestop"],
        *,
        time: int | None = None,
    ) -> None:
        params = {key: value for key, value in (("time", time),) if value is not None}
        await self._post(f"shade/{index}/{action}", params, as_query_params=True)

    async def move_blind_position(
        self,
        index: int,
        *,
        blind: int | None = None,
        lamella: int | None = None,
    ) -> None:
        params = {
            key: value
            for key, value in (("blind", blind), ("lamella", lamella))
            if value is not None
        }
        await self._post(f"shade/{index}", params, as_query_params=True)

    async def reset_pir_time(self, index: int) -> None:
        await self._post(f"pir/{index}/reset_time", {})

    async def save_default_config(self) -> None:
        await self._post("save_default_config", {})

    async def reboot(self) -> None:
        await self._post("reboot", {})


async def _repeat(
    once_fn: Callable[[], Awaitable[Any]], *, attempts: int, retry_delay: float
) -> Any:
    last_exc = ValueError("no attempts made")
    for _ in range(attempts):
        try:
            return await once_fn()
        except aiohttp.ClientError as exc:
            _LOGGER.debug(f"client error: {exc}")
            last_exc = exc
        await asyncio.sleep(retry_delay)

    raise last_exc
