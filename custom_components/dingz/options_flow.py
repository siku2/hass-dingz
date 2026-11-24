import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.components.network import async_get_source_ip
from homeassistant.config_entries import (
    ConfigEntryState,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from homeassistant.helpers.typing import UNDEFINED
from yarl import URL

from . import api
from .shared import Shared

_LOGGER = logging.getLogger(__name__)

CONF_ENABLE = "enable"
CONF_CERTIFICATE = "certificate"

DEFAULT_PORT = 1883
DEFAULT_TLS_PORT = 8883

_LOCAL_BROKER_HOSTS = {"core-mosquitto", "localhost", "127.0.0.1", "::1"}


class DingzOptionsFlow(OptionsFlow):
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if self.config_entry.state is not ConfigEntryState.LOADED:
            return self.async_abort(reason="not_loaded")
        return self.async_show_menu(step_id="init", menu_options=["mqtt"])

    async def async_step_mqtt(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if self.config_entry.state is not ConfigEntryState.LOADED:
            return self.async_abort(reason="not_loaded")
        shared: Shared = self.config_entry.runtime_data
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                config = _to_mqtt_config(user_input)
            except ValueError:
                errors[CONF_HOST] = "invalid_host"
            if bool(user_input.get(CONF_USERNAME)) != bool(
                user_input.get(CONF_PASSWORD)
            ):
                errors["base"] = "credentials_incomplete"
            if not errors:
                try:
                    await shared.client.update_mqtt_service_config(config)
                    await shared.client.save_default_config()
                except aiohttp.ClientError, TimeoutError, api.NotEnoughRamError:
                    _LOGGER.exception("failed to update the MQTT configuration")
                    errors["base"] = "cannot_connect"
                else:
                    self.hass.config_entries.async_schedule_reload(
                        self.config_entry.entry_id
                    )
                    return self.async_create_entry(data=dict(self.config_entry.options))

        defaults = user_input or await self._async_defaults()
        return self.async_show_form(
            step_id="mqtt",
            data_schema=self.add_suggested_values_to_schema(_MQTT_SCHEMA, defaults),
            errors=errors,
        )

    async def _async_defaults(self) -> dict[str, Any]:
        shared: Shared = self.config_entry.runtime_data
        current = shared.config.data.services.get("mqtt", {})
        defaults: dict[str, Any] = {
            CONF_ENABLE: current.get("enable", False) or not current.get("uri"),
            CONF_SSL: False,
            CONF_CERTIFICATE: current.get("server.crt") or "",
        }

        if uri := current.get("uri"):
            url = URL(uri)
            defaults[CONF_SSL] = url.scheme == "mqtts"
            defaults[CONF_HOST] = url.host
            defaults[CONF_PORT] = url.explicit_port or _default_port(url.scheme)
            defaults[CONF_USERNAME] = url.user or ""
            defaults[CONF_PASSWORD] = url.password or ""
            return defaults

        for entry in self.hass.config_entries.async_entries("mqtt"):
            host = entry.data.get("broker")
            if not host:
                continue
            if host in _LOCAL_BROKER_HOSTS:
                try:
                    host = await async_get_source_ip(
                        self.hass, shared.client.base_url.host or UNDEFINED
                    )
                except HomeAssistantError:
                    continue
            defaults[CONF_HOST] = host
            defaults[CONF_PORT] = entry.data.get("port", DEFAULT_PORT)
            break
        return defaults


_MQTT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ENABLE): bool,
        vol.Required(CONF_HOST): TextSelector(),
        vol.Required(CONF_PORT): NumberSelector(
            NumberSelectorConfig(min=1, max=65535, mode=NumberSelectorMode.BOX)
        ),
        vol.Required(CONF_SSL): bool,
        vol.Optional(CONF_USERNAME): TextSelector(),
        vol.Optional(CONF_PASSWORD): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD)
        ),
        vol.Optional(CONF_CERTIFICATE): TextSelector(
            TextSelectorConfig(multiline=True)
        ),
    }
)


def _default_port(scheme: str) -> int:
    return DEFAULT_TLS_PORT if scheme == "mqtts" else DEFAULT_PORT


def _to_mqtt_config(user_input: dict[str, Any]) -> api.ServicesConfigMqtt:
    certificate = (user_input.get(CONF_CERTIFICATE) or "").strip() or None
    uri = URL.build(
        scheme="mqtts" if user_input[CONF_SSL] else "mqtt",
        user=user_input.get(CONF_USERNAME) or None,
        password=user_input.get(CONF_PASSWORD) or None,
        host=user_input[CONF_HOST].strip(),
        port=int(user_input[CONF_PORT]),
    )
    return api.ServicesConfigMqtt(
        {"enable": user_input[CONF_ENABLE], "uri": str(uri), "server.crt": certificate}
    )
