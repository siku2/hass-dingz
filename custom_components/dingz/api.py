from typing import Any, Literal, TypedDict

import aiohttp
from yarl import URL


class Index(TypedDict, total=False):
    relative: int
    absolute: int


class StateDimmer(TypedDict, total=False):
    on: bool
    output: int
    ramp: int
    readonly: bool
    index: Index


class StateLed(TypedDict, total=False):
    on: bool
    hsv: str
    rgb: str
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


OnOffT = Literal["off"] | Literal["on"]


class StateThermostat(TypedDict, total=False):
    active: bool
    state: OnOffT
    mode: OnOffT
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
    blinds: list[Any]
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

class Client:
    _session: aiohttp.ClientSession
    _base_url: URL

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

    async def get_state(self) -> State:
        url = self._base_url / "api/v1/state"
        async with self._session.get(url) as resp:
            return await resp.json()


    async def get_device(self) -> DeviceResponseT:
        url = self._base_url / "api/v1/device"
        async with self._session.get(url) as resp:
            return await resp.json()
