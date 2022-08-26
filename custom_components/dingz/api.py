import abc
import dataclasses
import logging
from datetime import datetime
from typing import List, Optional, Tuple, Union

import aiohttp
from voluptuous.validators import Boolean

logger = logging.getLogger(__name__)


class FromJSON(abc.ABC):
    @classmethod
    def _from_json(cls, data):
        kwargs = {}
        for field in dataclasses.fields(cls):
            key = field.name
            try:
                kwargs[key] = data.pop(key)
            except KeyError:
                continue
        if data:
            logger.warning(f"{cls.__qualname__!r} unhandled keys: {set(data.keys())!r}")
        return cls(**kwargs)

    @classmethod
    def from_json(cls, data: dict):
        try:
            return cls._from_json(data.copy())
        except Exception as e:
            if not getattr(e, "_handled", False):
                logger.error(
                    f"failed to create `{cls.__qualname__}` from JSON: {data!r}"
                )
                e._handled = True

            raise e from None

    @classmethod
    def list_from_json(cls, data: list) -> list:
        return list(map(cls.from_json, data))


@dataclasses.dataclass()
class Index(FromJSON):
    relative: int
    """The relative index.

    Use this index to refer to dimmer for set the dimmer.
    """
    absolute: int
    """The absolute index of dimmer. It refers to hardware output number."""


@dataclasses.dataclass()
class Dimmer(FromJSON):
    on: bool
    """The dimmer turned on/off status."""
    output: int
    """The dim value set on dimer 0..100.

    This value is 0 if the the `on` field is false.
    """
    ramp: int
    """The ramp (how quickly change dim value) set on dimmer 0..255.

    The ramp is always 0 for non dimmable outputs.
    """
    readonly: bool
    """If the dimmer is disabled, for example if the output is configured as input or thermostat is enabled."""
    index: Index

    @classmethod
    def _from_json(cls, data):
        data["index"] = Index.from_json(data["index"])
        return super()._from_json(data)


@dataclasses.dataclass()
class Blind(FromJSON):

    moving: str
    """Moving state."""
    position: int
    """Position of blind 0..100. When you set the blind value this field contains this value."""
    lamella: int
    """position of lamella 0..100. When you set the lamella this filed contains this value."""
    readonly: bool
    """If the shade is disables. The value can have true if the outputs of blind are used by other functionality."""
    index: Index

    @classmethod
    def _from_json(cls, data):
        data["index"] = Index.from_json(data["index"])
        return super()._from_json(data)


@dataclasses.dataclass()
class LED(FromJSON):
    on: bool
    """If the LED is on."""
    hsv: str
    """Color set on LED in HSV format.

    String should be H;S;V, <0...359>;<0..100>;<0..100>.
    """
    rgb: str
    """Color set on LED in RGB format.

    The string is 6 hex digits: RRGGBB.
    """
    mode: str
    """The color mode. It describes the current color format used by LED."""
    ramp: int
    """Defines ramp/fade speed of color change (change from previous to new value)."""

    def hsv_values(self) -> Tuple[float, float, float]:
        h, s, v = map(float, self.hsv.split(";"))
        return h, s, v


@dataclasses.dataclass()
class Sensors(FromJSON):
    brightness: Optional[int]
    """The brightness read by light sensor including compensation of light depending on cover color.

    If there is  error or no light sensor is present the field is set to `None`.
    """
    light_state: Optional[str]
    """The field contains the range in which the illuminance is located.

    It can have values: day, twilight or night. The assignment to the interval depends on the settings in the WebUI/Motion Detector/Thresholds.
    In case of error or light sensor not present the field contain null value.
    """
    cpu_temperature: float
    """The temperature on front CPU."""
    puck_temperature: Optional[float]
    """The temperature on back CPU.

    If there is any error then this field contain null value.
    """
    fet_temperature: Optional[float]
    """The internal puck/base FET temperature.

    If there is any error then this field contain null value.
    """
    person_present: bool
    """The current status of motion."""
    input_state: Optional[bool]
    """If the output 1 is not configured as input then the field contain null value otherwise bool value represent input state (the voltage present on input).

    The input state can be negated in input settings (WebUI/Input/invert).
    """
    power_outputs: Optional[List[float]]
    """This field contain array of objects.

    Each object contain the value field which show the current power provided to device connected to output.
    This field can have the null value in case of any failure.
    """

    room_temperature: Optional[float] = None
    """The compensated temperature in room.

    If there is any error the field is not present.
    """
    uncompensated_temperature: Optional[float] = None
    """The uncompensated temperature in room (measured by temperature sensor).

    If there is any error the field is not present.
    """
    temp_offset: Optional[float] = None
    light_off_timer: Optional[int] = None
    """If the PIR timer is enabled on any output then this field is present and show how much time left to turn off the output."""
    suspend_timer: Optional[int] = None
    """If the PIR timer is enabled on any output then this field is present and show how much time left to turn on the output by PIR sensor will be possible."""

    @classmethod
    def _from_json(cls, data):
        power_outputs = data["power_outputs"]
        if power_outputs:
            try:
                for i, out in enumerate(power_outputs):
                    power_outputs[i] = out["value"]
            except Exception:
                logger.error("failed to handle power outputs")
                raise

        return super()._from_json(data)


@dataclasses.dataclass()
class Thermostat(FromJSON):
    active: bool
    """If the thermostat functionality is enabled."""
    out: int
    """The output index assigned to thermostat."""
    on: bool
    """If the output controlled by thermostat is turn on."""
    enabled: bool
    """It the thermostat is enabled e.g. control output depending of temperature."""
    target_temp: float
    """The target cooling heating temperature."""
    mode: str
    """Mode of thermostat operating."""
    temp: float
    """Current room temperature."""
    min_target_temp: int
    """Minimum target temperature."""
    max_target_temp: int
    """Maximum target temperature."""


@dataclasses.dataclass()
class WiFi(FromJSON):
    version: str
    """The front firmware version."""
    mac: str
    """The MAC address of device."""
    ssid: str
    """The network name to which device is connected."""
    ip: str
    """IP address of device in static IP configuration."""
    mask: str
    """IP mask used in static IP configuration."""
    gateway: str
    """IP address of gateway used in static IP configuration."""
    dns: str
    """The DNS IP address used in static IP configuration."""
    static: bool
    """If the device is connected in static IP mode. If this field is true then ip, mask, gateway, dns fields are set to IPv4 address values."""
    connected: bool
    """If the device is connected to AP."""

    @classmethod
    def _from_json(cls, data):
        try:
            data["gateway"] = data.pop("gw")
        except KeyError:
            pass
        return super()._from_json(data)


@dataclasses.dataclass()
class Config(FromJSON):
    timestamp: int
    """The UNIX timestamp of last configuration change."""

    @property
    def timestamp_dt(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp)


@dataclasses.dataclass()
class State(FromJSON):
    dimmers: List[Dimmer]
    blinds: List[Blind]
    led: LED
    sensors: Sensors
    thermostat: Thermostat
    wifi: WiFi
    config: Config
    # iso timestamps in the form of `yyyy-mm-dd HH:MM:SS`
    time: Optional[str] = None

    @classmethod
    def _from_json(cls, data):
        data["dimmers"] = Dimmer.list_from_json(data["dimmers"])
        data["blinds"] = Blind.list_from_json(data["blinds"])
        data["led"] = LED.from_json(data["led"])
        data["sensors"] = Sensors.from_json(data["sensors"])
        data["thermostat"] = Thermostat.from_json(data["thermostat"])
        data["wifi"] = WiFi.from_json(data["wifi"])
        data["config"] = Config.from_json(data["config"])
        return super()._from_json(data)


DINGZ_INFO_TYPE = 108


@dataclasses.dataclass()
class Info(FromJSON):
    version: str
    """Current firmware version"""
    mac: str
    """MAC address, without any delimiters"""
    type: int
    """Device type it always have value 108"""
    ssid: str
    """SSID of the currently connected network"""
    ip: str
    """Current ip address"""
    mask: str
    """Mask of the current network"""
    gateway: str
    """Gateway of the current network"""
    dns: str
    """DNS of the curent network"""
    static: bool
    """Wether or not the ip address is static"""
    connected: bool
    """Whether or not the device is connected to the internet"""

    @classmethod
    def _from_json(cls, data):
        try:
            data["gateway"] = data.pop("gw")
        except KeyError:
            pass
        return super()._from_json(data)


DIP_4_DIMMER = 3


@dataclasses.dataclass()
class Device(FromJSON):
    type: str
    """The device type, it always have value: "dingz"."""
    battery: bool
    """If the device is powered by batteries, in dingz case it have value "false"."""
    reachable: bool
    """If device is reachable (present), it always have value true."""
    meshroot: bool
    """If device is a root device, that is, the master device."""
    fw_version: str
    """Front firmware version."""
    hw_version: str
    """Front hardware version."""
    fw_version_puck: str
    """Puck/base firmware version."""
    bl_version_puck: str
    """Puck/base bootloader firmware version."""
    hw_version_puck: str
    """Puck/base hardware version."""
    puck_production_date: dict
    """Puck/base year/month/day of production."""
    dip_config: int
    """Puck/base DIP switch configuration.

    3 - 4 DIMMERS
    2 - 1 SHADE and 2 DIMMERS
    1 - 2 DIMMERS and 1 SHADE
    0 - 2 SHADES
    """
    has_pir: bool
    """If device have PIR."""
    hash: str
    """Front firmware signature."""

    hw_id_puck: Optional[str] = None
    """Undocumented field"""
    puck_sn: Optional[str] = None
    """Puck/base serial number."""
    puck_hw_model: Optional[str] = None
    """Puck/base hardware model."""
    front_hw_model: Optional[str] = None
    """Front hardware model."""
    front_production_date: Optional[str] = None
    """Front production date in dot notation."""
    front_sn: Optional[str] = None
    """Front serial number."""
    front_color: Optional[str] = None
    """Front cover color in shortcut format."""

    @property
    def dimmers_only(self) -> bool:
        return self.dip_config == DIP_4_DIMMER


@dataclasses.dataclass()
class TempComp(FromJSON):
    fet_offset: float
    gain_up: float
    gain_down: float
    gain_total: float


@dataclasses.dataclass()
class SystemConfig(FromJSON):
    allow_reset: bool
    """If the factory reset should be possible with the buttons."""
    allow_wps: bool
    """If it should be possible to enable WPS from the buttons."""
    allow_reboot: bool
    """If the restart should be possible from the buttons."""
    broadcast_period: int
    """How often to report a device to the network (5..65535).

    Less broadcasting period causes the applications to find the device slower.
    Unit is second.
    """
    origin: bool
    """Whether the Origin HTTP header should be checked.

    In case of a mismatch, the query rejected.
    """
    upgrade_blink: bool
    """Should the LED flash pink while updating the firmware."""
    reboot_blink: bool
    """Should the LED flash blue after reboot."""
    dingz_name: bool
    """Device name (max 32 chars)"""
    room_name: str
    """Name of the room in which the device is located (max 32 chars)"""
    temp_offset: int
    """Offset of the temperature measured by the device (-10..10)

    Form of compensation.
    """
    time: str
    """This field is read-only and returns the date and time from the device.

    ("YYYY-MM-DD hh:mm:ss")
    """
    system_status: str
    """Specifies the puck status.

    Is there communication with it, are the outputs not overloaded, are the temperature not exceeded.

    Values:
    - "OK"
    - "Puck not responding"
    - "Puck overload"
    - "Puck FETs over temperature"
    """
    fet_offset: int
    """Read only. Temperature offset measured at the output transistors (-100..100)."""
    cpu_offset: int
    """Read only. Temperature offset measured on the puck CPU (-100..100)."""
    token: Optional[str] = None
    """Sets a Token for HTTP requests (max 256 chars).

    If the correct token is not provided, the query will be rejected.
    """
    mdns_search_period: Optional[int] = None
    groups: Optional[List[bool]] = None
    temp_comp: Optional[TempComp] = None

    @classmethod
    def _from_json(cls, data):
        try:
            raw_temp_comp = data.pop("temp_comp")
        except KeyError:
            pass
        else:
            data["temp_comp"] = TempComp.from_json(raw_temp_comp)

        return super()._from_json(data)


DIMMER_NOT_CONNECTED = "not_connected"
DIMMER_NON_DIMMABLE = "non_dimmable"


@dataclasses.dataclass()
class DimmerConfig(FromJSON):
    output: str
    """Define light source type connected to output.

    Values:
    - "halogen"
    - "incandescent"
    - "led"
    - "linear"
    - "ohmic"
    - "pulse"
    - "not_connected"
    """
    name: str
    """Name of dimmer (max 32 chars)."""
    feedback: Optional[str]
    """Signalize by enable LED with specified color when the dimmer is turn on.

    In case of multi dimmers set with feedback color enabled the color will be set to value get from first turned on dimmer.
    """
    feedback_intensity: int
    """Brightness of feedback color (0..100)."""

    @property
    def dimmable(self) -> bool:
        return self.output not in (DIMMER_NOT_CONNECTED, DIMMER_NON_DIMMABLE)

    @property
    def available(self) -> bool:
        return bool(self.name) and self.output != DIMMER_NOT_CONNECTED


BLINDS_NOT_INITIALIZED = "Not initialized"


@dataclasses.dataclass()
class BlindConfig(FromJSON):
    type: str
    """Define light source type connected to output.

    Values:
    - "lamella_90"
    - "canvas"
    """
    name: str
    """Name of blind (max 32 chars)."""

    state: str
    """The state of the blinds.

    Values:
    - "Not initialized"
    - "Initialized"
    - "Initialising"
    - "Unknown"
    """
    shade_up_time: float
    invert_direction: Boolean
    lamella_time: float
    max_value: int
    shade_down_time: float
    min_value: int
    auto_calibration: Boolean

    @property
    def available(self) -> bool:
        return bool(self.name) and self.state != BLINDS_NOT_INITIALIZED


@dataclasses.dataclass()
class PIRConfig(FromJSON):
    @dataclasses.dataclass()
    class Thresholds(FromJSON):
        twilight_to_night: int
        """The light intensity level causing change the light status, if light value is bellow this level the light state go to night."""
        night_to_twilight: int
        """The light intensity level causing change the light status, if light value is above this value and bellow day_to_twilight value then light state move to twilight."""
        day_to_twilight: int
        """The light intensity level causing change the light status, if light value is bellow this value and above night_to_twilight the then light state move to twilight."""
        twilight_to_day: int
        """The light intensity level causing change the light status, if light value is above this value then light state move to day."""

    @dataclasses.dataclass()
    class Dimmer(FromJSON):
        value_night: int
        """The dimmer value set in case of motion and light state night (0..100)."""
        value_twilight: int
        """The dimmer value set in case of motion and light state twilight (0..100)."""
        value_day: int
        """Not used (0..100)."""
        fade_in_time: int
        """How fast brightening the dimmers assigned to input (0..100).

        Unit is 100ms.
        """
        fade_out_time: int
        """How fast darknet the dimmers assigned to input (0..100).

        Unit is 100ms.
        """

    pir_output: Optional[int]
    """The assignation of outputs to PIR (0..255).

    In case of null or 0 value no any output is assigned to the PIR.
    In case of assignation the field should be given as unsigned integer.
    There are two format of assignation notation, one in old scheme allow assign only one output to PIR, second in new bit mask format for multi output assignation.
    In case of single output assignation the value should be in range 1..4 corresponds to output number.
    In case of multi assignation the value should be bit mask with most significant bit set and four less significant bit set for dedicated outputs.
    So LSB bit 0 correspond to output 1, and LSB bit 3 correspond to output 4. MSB bit 7 should be set.
    After translation bit format to unsigned integer the value is in range: 128..143.
    This format can be used also to only one output assignation or no assignation, so is universal and recommended.
    """

    pir_feedback: Optional[str]
    """After violation of PIR blink in selected color.

    Values:
    - "white"
    - "red"
    - "green"
    - "blue"
    """
    feedback_intensity: int
    """Brightness of feedback blink (0..100)."""
    thresholds: Thresholds
    on_time: int
    """The dimmer enabled time after violation of PIR. Time is counting if no motion is detected."""
    off_time: int
    """PIR function inhibit time.

    If button was pressed or any control api for dimmer was used then PIR actions which control the dimmers are blocked.
    Time start counting if no motion is detected.
    """
    dim_value_night: int
    """For backward compatibility set all dimmers values with same dim_value_night value (0..100)."""
    dim_value_twilight: int
    """For backward compatibility set all dimmers values with same dim_value_twilight value (0..100)."""
    fade_in_time: int
    """For backward compatibility set all dimmers values with same fade_in_time value (0..100)."""
    fade_out_time: int
    """For backward compatibility set all dimers values with same fade_out_time value (0..100)."""
    feedback_time: int
    """How long enable LED for feedback specified by pir_feedback (1..255)."""
    dimmer: List[Dimmer]
    enabled: bool
    """If true the PIR function is enabled."""
    backoff_time: int
    """Period of action triggered by PIR (0..600).

    The time starts counting if no motion is detected after time elapse the PIR fall action is triggered.
    """
    light_lpf: bool
    """If true then light lowpass average filter is enable.

    This cause rejection of fast undesirable light changes my corrupted light measurements and go to wrong light status.
    Example dimmer cause illuminate of dingz.
    """

    @classmethod
    def _from_json(cls, data):
        data["thresholds"] = cls.Thresholds.from_json(data["thresholds"])
        data["dimmer"] = (cls.Dimmer.list_from_json(data["dimmer"]),)
        return super()._from_json(data)


@dataclasses.dataclass()
class DingzSession:
    session: aiohttp.ClientSession
    host: str

    async def _get(self, path: str):
        async with self.session.get(f"{self.host}/api/v1{path}") as resp:
            return await resp.json()

    def __post_request(self, path: str, data: Optional[dict]):
        headers = {}
        if data:
            # doing it by hand to avoid percent encoding
            body = "&".join(f"{key}={value}" for key, value in data.items())
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            body = None

        logger.debug("POST %s | %s", path, body)
        return self.session.post(
            f"{self.host}/api/v1{path}",
            data=body,
            headers=headers,
        )

    async def _post_json(self, path: str, **data):
        async with self.__post_request(path, data) as resp:
            logger.debug("response: %s", resp)
            return await resp.json()

    async def _post_plain(self, path: str, **data):
        async with self.__post_request(path, data) as resp:
            logger.debug("response: %s", resp)
            resp.raise_for_status()

    async def info(self) -> Info:
        raw = await self._get("/info")
        return Info.from_json(raw)

    async def device(self) -> Device:
        raw = await self._get("/device")
        if len(raw) > 1:
            logger.warning(f"received more than one device: {raw}")
        try:
            device_raw = next(iter(raw.values()))
        except StopIteration:
            logger.error("empty device response")
            raise

        return Device.from_json(device_raw)

    async def state(self) -> State:
        raw = await self._get("/state")
        return State.from_json(raw)

    async def system_config(self) -> SystemConfig:
        raw = await self._get("/system_config")
        return SystemConfig.from_json(raw)

    async def dimmer_config(self) -> List[DimmerConfig]:
        raw = await self._get("/dimmer_config")
        return DimmerConfig.list_from_json(raw["dimmers"])

    async def blind_config(self) -> List[BlindConfig]:
        raw = await self._get("/blind_config")
        return BlindConfig.list_from_json(raw["blinds"])

    async def pir_config(self) -> PIRConfig:
        raw = await self._get("/pir_config")
        return PIRConfig.from_json(raw)

    async def set_led(
        self, *, state: bool = None, color: Tuple[float, float, float] = None
    ) -> None:
        """
        Args:
            state: Requested state. `None` toggles.
            color: (<0...359>, <0..100>, <0..100>)
        """
        kwargs = {}
        if color:
            h, s, v = map(round, color)
            kwargs["color"] = f"{h % 360};{s};{v}"
            kwargs["mode"] = "hsv"

        action = "toggle" if state is None else "on" if state else "off"

        await self._post_json("/led/set", action=action, **kwargs)

    async def set_dimmer(self, index: int, state: bool, *, value: float = None) -> None:
        kwargs = {}
        if value is not None:
            kwargs["value"] = round(value)
        action = "on" if state else "off"
        await self._post_plain(f"/dimmer/{index}/{action}", **kwargs)

    async def set_blind_position(self, index: int, position: float) -> None:
        kwargs = {}
        kwargs["blind"] = round(position)
        state = await self.state()
        kwargs["lamella"] = state.blinds[index].lamella
        await self._post_plain(f"/shade/{index}", **kwargs)

    async def set_blind_tilt_position(self, index: int, tilt: float) -> None:
        kwargs = {}
        state = await self.state()
        kwargs["blind"] = state.blinds[index].position
        kwargs["lamella"] = round(tilt)
        await self._post_plain(f"/shade/{index}", **kwargs)


    async def blind_down(self, index: int) -> None:
        kwargs = {}
        await self._post_plain(f"/shade/{index}/down", **kwargs)

    async def blind_up(self, index: int) -> None:
        kwargs = {}
        await self._post_plain(f"/shade/{index}/up", **kwargs)

    async def blind_stop(self, index: int) -> None:
        kwargs = {}
        await self._post_plain(f"/shade/{index}/stop", **kwargs)