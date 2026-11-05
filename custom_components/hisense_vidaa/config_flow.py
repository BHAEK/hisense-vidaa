"""Configuration flow: host, then the PIN shown on the TV."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST
from homeassistant.core import callback

from .const import CONF_DEVICE_ID, CONF_MAC, DOMAIN
from .vidaa_tv import mqtt_transport_factory
from .vidaa_tv.errors import AuthenticationError, VidaaError
from .vidaa_tv.pairing import PairingFlow, PairingOutcome

CONF_PIN = "pin"


class VidaaConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._host = ""
        self._mac: str | None = None
        self._pairing: PairingFlow | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._host = user_input[CONF_HOST]
            self._mac = user_input.get(CONF_MAC) or None
            await self.async_set_unique_id(self._mac or self._host)
            self._abort_if_unique_id_configured()
            self._pairing = PairingFlow(self._host, mqtt_transport_factory())
            try:
                outcome = await self._pairing.start()
            except VidaaError:
                errors["base"] = "cannot_connect"
                await self._close_pairing()
            else:
                if outcome is PairingOutcome.PIN_REQUIRED:
                    return await self.async_step_pin()
                return await self._finish()
        schema = vol.Schema({vol.Required(CONF_HOST): str, vol.Optional(CONF_MAC): str})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_pin(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None and self._pairing is not None:
            try:
                await self._pairing.submit_pin(user_input[CONF_PIN])
            except AuthenticationError:
                errors["base"] = "invalid_pin"
            except VidaaError:
                errors["base"] = "cannot_connect"
            else:
                return await self._finish()
        return self.async_show_form(
            step_id="pin", data_schema=vol.Schema({vol.Required(CONF_PIN): str}), errors=errors
        )

    async def _finish(self) -> ConfigFlowResult:
        assert self._pairing is not None
        device_id = self._pairing.device_id
        await self._close_pairing()
        return self.async_create_entry(
            title=f"Hisense TV ({self._host})",
            data={CONF_HOST: self._host, CONF_MAC: self._mac, CONF_DEVICE_ID: device_id},
        )

    async def _close_pairing(self) -> None:
        if self._pairing is not None:
            await self._pairing.close()
            self._pairing = None

    @callback
    def async_remove(self) -> None:
        if self._pairing is not None:
            self.hass.async_create_task(self._pairing.close())
