import dataclasses
import enum
import logging
import typing
from collections.abc import Awaitable
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from yarl import URL

from . import api
from .const import DOMAIN
from .helpers import get_device_name

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.UPDATE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = Coordinator(hass, URL(entry.data["host"]))
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

class Coordinator(DataUpdateCoordinator[api.State]):
    client: api.Client
    device_info: DeviceInfo
    unique_id_prefix: str

    def __init__(
        self,
        hass: HomeAssistant,
        base_url: URL,
    ) -> None:
        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=30)
        )

        self.client = api.Client(async_get_clientsession(hass), base_url)
        self.device_info = DeviceInfo(manufacturer="iolo AG")
        self.unique_id_prefix = ""

    async def _async_update_data(self) -> api.State:
        try:
            state = await self.client.get_state()
        except Exception as exc:
            raise UpdateFailed(f"state: {exc}") from exc
        return state
