"""Constants for the Hisense VIDAA integration."""

DOMAIN = "hisense_vidaa"

CONF_DEVICE_ID = "device_id"
CONF_MAC = "mac"

# Waiting for a TV to boot after a wake-up must not block a service call for long.
TURN_ON_WAIT_SECONDS = 45.0
