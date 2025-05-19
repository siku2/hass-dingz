import json
import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service_info.mqtt import MqttServiceInfo
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
from yarl import URL

from . import api
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host"): str,
    }
)

# we use a different error than 'already_configured' because mqtt stops discovering new devices if we return it once
_ERROR_DEVICE_ALREADY_CONFIGURED = "device_already_configured"


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    base_url = URL(data["host"])
    if not base_url.is_absolute():
        base_url = URL(f"http://{base_url}")

    client = api.Client(async_get_clientsession(hass), base_url)
    try:
        system_config = await client.get_system_config()
    except Exception:
        _LOGGER.exception("failed to get system config")
        raise CannotConnect

    dingz_id = system_config.get("id")
    title = system_config.get("dingz_name")
    if title is None:
        title = dingz_id

    return {"title": title, "dingz_id": dingz_id, "data": {"base_url": str(base_url)}}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        super().__init__()

        self._info: dict[str, Any] | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                self._info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                if dingz_id := self._info["dingz_id"]:
                    await self.async_set_unique_id(dingz_id)
                    self._abort_if_unique_id_configured(
                        error=_ERROR_DEVICE_ALREADY_CONFIGURED
                    )
                return await self.async_step_confirm({})

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        assert self._info
        if user_input is not None:
            return self.async_create_entry(
                title=self._info["title"], data=self._info["data"]
            )

        self.context["title_placeholders"] = {
            "name": self._info["title"],
        }
        return self.async_show_form(step_id="confirm")

    async def async_step_mqtt(
        self, discovery_info: MqttServiceInfo
    ) -> config_entries.ConfigFlowResult:
        _LOGGER.debug("discovered potential device using mqtt: %s", discovery_info)
        try:
            payload = json.loads(discovery_info.payload)
        except json.JSONDecodeError:
            return self.async_abort(reason="false_positive")
        try:
            ip = str(payload["ip"])
        except KeyError:
            return self.async_abort(reason="false_positive")

        topic_levels = discovery_info.topic.split("/")
        try:
            dingz_id = topic_levels[1]
        except IndexError:
            return self.async_abort(reason="false_positive")

        _LOGGER.debug("mqtt discovery: id=%s, ip=%s", dingz_id, ip)
        await self.async_set_unique_id(dingz_id)
        self._abort_if_unique_id_configured(error=_ERROR_DEVICE_ALREADY_CONFIGURED)

        self._info = await validate_input(self.hass, {"host": ip})
        return await self.async_step_confirm()

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> config_entries.ConfigFlowResult:
        _LOGGER.debug("discovered potential device using zeroconf: %s", discovery_info)
        try:
            dingz_id = str(discovery_info.properties["id"])
        except KeyError:
            return self.async_abort(reason="false_positive")

        _LOGGER.debug("zeroconf discovery: id=%s, ip=%s", dingz_id, discovery_info.host)
        await self.async_set_unique_id(dingz_id)
        self._abort_if_unique_id_configured(error=_ERROR_DEVICE_ALREADY_CONFIGURED)

        self._info = await validate_input(self.hass, {"host": discovery_info.host})
        return await self.async_step_confirm()


class CannotConnect(HomeAssistantError): ...
