"""Configuration flow: pair with the PIN shown on the TV, reconfigure, reauthenticate."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import SOURCE_REAUTH, ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST
from homeassistant.core import callback

from .const import CONF_DEVICE_ID, CONF_MAC, DOMAIN
from .vidaa_tv import mqtt_transport_factory
from .vidaa_tv.errors import AuthenticationError, VidaaError
from .vidaa_tv.pairing import PairingFlow, PairingOutcome

_LOGGER = logging.getLogger(__name__)

CONF_PIN = "pin"


class VidaaConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._host = ""
        self._mac: str | None = None
        self._pairing: PairingFlow | None = None

    # -- first setup ---------------------------------------------------------
    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._host = user_input[CONF_HOST]
            self._mac = user_input.get(CONF_MAC) or None
            result = await self._start_pairing(errors)
            if result is not None:
                return result
        schema = vol.Schema({vol.Required(CONF_HOST): str, vol.Optional(CONF_MAC): str})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_pin(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None and self._pairing is not None:
            try:
                await self._pairing.submit_pin(user_input[CONF_PIN])
            except AuthenticationError as err:
                _LOGGER.warning("The TV rejected the PIN: %s", err)
                errors["base"] = "invalid_pin"
            except VidaaError as err:
                _LOGGER.warning("Lost the TV while checking the PIN: %s", err)
                errors["base"] = "cannot_connect"
            else:
                _LOGGER.info("The TV accepted the PIN")
                return await self._finish()
        return self.async_show_form(
            step_id="pin", data_schema=vol.Schema({vol.Required(CONF_PIN): str}), errors=errors
        )

    # -- the TV forgot this client: pair again -------------------------------
    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        self._host = entry_data[CONF_HOST]
        self._mac = entry_data.get(CONF_MAC)
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            result = await self._start_pairing(errors)
            if result is not None:
                return result
        return self.async_show_form(step_id="reauth_confirm", errors=errors)

    # -- the TV moved ----------------------------------------------------------
    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            flow = PairingFlow(
                user_input[CONF_HOST],
                mqtt_transport_factory(),
                device_id=entry.data[CONF_DEVICE_ID],
            )
            try:
                outcome = await flow.start()
                if outcome is PairingOutcome.PIN_REQUIRED:
                    _LOGGER.warning(
                        "Reconfigure: the TV at the new address does not know this installation"
                    )
                    errors["base"] = "not_paired"
                else:
                    info = await flow.fetch_info()
                    if info is not None and entry.unique_id and info.device_id != entry.unique_id:
                        _LOGGER.warning("Reconfigure: the new address belongs to a different TV")
                        errors["base"] = "wrong_device"
                    else:
                        return self.async_update_reload_and_abort(
                            entry,
                            data_updates={
                                CONF_HOST: user_input[CONF_HOST],
                                CONF_MAC: user_input.get(CONF_MAC) or entry.data.get(CONF_MAC),
                            },
                        )
            except VidaaError as err:
                _LOGGER.warning("Reconfigure: cannot reach the TV at the new address: %s", err)
                errors["base"] = "cannot_connect"
            finally:
                await flow.close()
        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=entry.data[CONF_HOST]): str,
                vol.Optional(CONF_MAC, default=entry.data.get(CONF_MAC) or ""): str,
            }
        )
        return self.async_show_form(step_id="reconfigure", data_schema=schema, errors=errors)

    # -- shared --------------------------------------------------------------
    async def _start_pairing(self, errors: dict[str, str]) -> ConfigFlowResult | None:
        """Connect with a fresh identity; returns the next step, or None on failure."""
        self._pairing = PairingFlow(self._host, mqtt_transport_factory())
        _LOGGER.info("Starting to pair with the TV at %s", self._host)
        try:
            outcome = await self._pairing.start()
        except VidaaError as err:
            _LOGGER.warning("Cannot reach the TV at %s: %s", self._host, err)
            errors["base"] = "cannot_connect"
            await self._close_pairing()
            return None
        if outcome is PairingOutcome.PIN_REQUIRED:
            _LOGGER.info("The TV is showing a PIN on its screen")
            return await self.async_step_pin()
        return await self._finish()

    async def _finish(self) -> ConfigFlowResult:
        assert self._pairing is not None
        device_id = self._pairing.device_id
        info = await self._pairing.fetch_info()
        await self._close_pairing()
        tv_id = info.device_id if info and info.device_id else None
        _LOGGER.info(
            "Pairing finished; the TV identity was %s", "read" if tv_id else "not available"
        )
        if self.source == SOURCE_REAUTH:
            entry = self._get_reauth_entry()
            if tv_id and entry.unique_id and tv_id != entry.unique_id:
                return self.async_abort(reason="wrong_device")
            return self.async_update_reload_and_abort(
                entry, data_updates={CONF_DEVICE_ID: device_id}
            )
        await self.async_set_unique_id(tv_id or self._mac or self._host)
        self._abort_if_unique_id_configured(updates={CONF_HOST: self._host})
        return self.async_create_entry(
            title="Hisense TV",
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
