import asyncio
import logging
from datetime import timedelta
from typing import cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .api import Device, DingzSession, Info, State, SystemConfig
from .const import DOMAIN, PLATFORMS

logger = logging.getLogger(__name__)


async def async_setup(hass, _config):
    hass.data[DOMAIN] = {}
    return True


class DingzCoordinator(DataUpdateCoordinator):
    data: State
    session: DingzSession
    info: Info
    device: Device
    system_config: SystemConfig

    async def __fetch_data(self) -> None:
        sess = self.session
        info, device, system_config = await asyncio.gather(
            sess.info(), sess.device(), sess.system_config()
        )

        self.info = cast(Info, info)
        self.device = cast(Device, device)
        self.system_config = cast(SystemConfig, system_config)

        await self.async_refresh()

    @classmethod
    async def build(cls, hass, session: DingzSession):
        async def update_state():
            return await session.state()

        coordinator = cls(
            hass,
            logger,
            name="state",
            update_method=update_state,
            update_interval=timedelta(seconds=5),
        )
        coordinator.session = session
        await coordinator.__fetch_data()

        return coordinator


async def setup_coordinator(hass, entry: ConfigEntry):
    host = entry.data["host"]

    session = DingzSession(aiohttp_client.async_get_clientsession(hass), host)
    coordinator = await DingzCoordinator.build(hass, session)
    hass.data[DOMAIN][entry.entry_id] = coordinator


async def async_setup_entry(hass, entry):
    await setup_coordinator(hass, entry)

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(hass, entry):
    for platform in PLATFORMS:
        await hass.config_entries.async_forward_entry_unload(entry, platform)

    return True


class DingzEntity(CoordinatorEntity):
    def __init__(self, coordinator: DingzCoordinator) -> None:
        # HACK: this is just for the type inference
        self.coordinator = coordinator
        super().__init__(coordinator)

    @property
    def _dingz_state(self) -> State:
        return self.coordinator.data

    @property
    def _dingz_session(self) -> DingzSession:
        return self.coordinator.session

    @property
    def device_info(self):
        coordinator = self.coordinator

        identifiers = {(DOMAIN, coordinator.device.front_sn)}
        mac = coordinator.info.mac
        if mac:
            identifiers.add(mac)

        return {
            "identifiers": identifiers,
            "name": coordinator.system_config.dingz_name,
            "manufacturer": "iolo AG",
            "model": coordinator.device.front_hw_model,
            "sw_version": coordinator.info.version,
        }

    @property
    def name(self):
        return self.coordinator.system_config.dingz_name

    @property
    def unique_id(self):
        return f"{DOMAIN}-{self.coordinator.info.mac}"
