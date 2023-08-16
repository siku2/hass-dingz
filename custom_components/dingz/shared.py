import logging
from datetime import timedelta

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
        # TODO: subscribe to MQTT
        self.client = api.Client(async_get_clientsession(hass), base_url)
        self.state = StateCoordinator(self)
        self.config = ConfigCoordinator(self)

        self._device_info = DeviceInfo()
        self._mac_addr: str | None = None

    @property
    def device_info(self) -> DeviceInfo:
        return self._device_info

    @property
    def mac_addr(self) -> str:
        assert self._mac_addr is not None
        return self._mac_addr

    async def async_config_entry_first_refresh(self) -> None:
        await self.state.async_config_entry_first_refresh()
        await self.config.async_config_entry_first_refresh()


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

    async def update_data_impl(self) -> api.State:
        state = await self.shared.client.get_state()

        try:
            self.shared._mac_addr = dr.format_mac(state["wifi"]["mac"])
        except LookupError:
            pass

        return state

    async def _async_update_data(self) -> api.State:
        try:
            return await self.update_data_impl()
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

    async def update_data_impl(self) -> api.FullDeviceConfig:
        device_config = await self.shared.client.get_full_device_config()

        self.shared._device_info.update(
            DeviceInfo(
                configuration_url=str(self.shared.client.base_url),
                connections={(dr.CONNECTION_NETWORK_MAC, self.shared.mac_addr)},
                identifiers={(DOMAIN, self.shared.mac_addr)},
                manufacturer="iolo AG",
                model=device_config.device.get("puck_hw_model"),
                name=device_config.system.get("dingz_name"),
                suggested_area=device_config.system.get("room_name"),
                sw_version=device_config.device.get("fw_version"),
                hw_version=device_config.device.get("hw_version"),
            )
        )

        return device_config

    async def _async_update_data(self) -> api.FullDeviceConfig:
        try:
            return await self.update_data_impl()
        except Exception:
            _LOGGER.exception("update config data failed")
            raise
