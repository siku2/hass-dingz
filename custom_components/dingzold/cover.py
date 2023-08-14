import logging

from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    CoverEntity,
)

from . import DingzCoordinator, DingzEntity
from .api import Blind, BlindConfig
from .const import DOMAIN

logger = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    c: DingzCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    covers = await c.session.blind_config()
    i = 0
    for config in covers:
        if not config.available:
            continue

        entities.append(DingzCoverEntity(c, config, i))
        i = i + 1

    async_add_entities(entities)
    return True


class DingzCoverEntity(DingzEntity, CoverEntity):
    _config: BlindConfig
    _index: int

    def __init__(self, coordinator, config, index) -> None:
        super().__init__(coordinator)
        self._config = config
        self._index = index

    @property
    def _dingz_blind(self) -> Blind:
        return self._dingz_state.blinds[self._index]

    @property
    def name(self):
        return f"{super().name} {self._config.name}"

    @property
    def unique_id(self):
        return f"{super().unique_id}-{self._index}"

    @property
    def is_closed(self) -> bool:
        """Return true if cover is closed."""
        return self.current_cover_position == 0

    @property
    def current_cover_position(self) -> int:
        """Return the current position of cover where 0 means closed and 100 is fully open."""
        return self._dingz_blind.position

    @property
    def current_cover_tilt_position(self) -> int:
        """Return the current position of cover of cover tilt where 0 means closed and 100 is fully open."""
        return self._dingz_blind.lamella

    async def async_close_cover(self, **kwargs):
        """Close cover."""
        await self._dingz_session.blind_down(self._index)
        await self.coordinator.async_request_refresh()

    async def async_open_cover(self, **kwargs):
        """Close cover."""
        await self._dingz_session.blind_up(self._index)
        await self.coordinator.async_request_refresh()

    async def async_set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        position = kwargs.get(ATTR_POSITION)
        await self._dingz_session.set_blind_position(self._index, position=position)
        await self.coordinator.async_request_refresh()

    async def async_set_cover_tilt_position(self, **kwargs):
        """Move the cover tilt to a specific position."""
        tilt = kwargs.get(ATTR_TILT_POSITION)
        await self._dingz_session.set_blind_tilt_position(self._index, tilt=tilt)
        await self.coordinator.async_request_refresh()

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        await self._dingz_session.blind_stop(self._index)
        await self.coordinator.async_request_refresh()