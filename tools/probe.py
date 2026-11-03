"""Diagnostic probe: pair (if needed) and record how the TV answers each query.

Everything the TV sends is appended, untouched, to ``captures/`` (git-ignored).
A PIN, if the TV asks for one, is read from ``captures/pin.txt`` so the probe can
run non-interactively.

Usage:
    python tools/probe.py HOST [--cert FILE --key FILE] [--wait 180] [--pin-wait 90]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import socket
import sys
import time
from pathlib import Path

from vidaa_tv.errors import VidaaError
from vidaa_tv.pairing import Pairing, PairingOutcome, new_device_id
from vidaa_tv.protocol.auth import static_credentials
from vidaa_tv.protocol.topics import Action, Service, mobile_filter
from vidaa_tv.session import Session
from vidaa_tv.transport.base import Message
from vidaa_tv.transport.mqtt import DEFAULT_PORT, MqttTransport, TlsConfig

CAPTURES = Path("captures")
IDENTITY_FILE = CAPTURES / "identity.json"
PIN_FILE = CAPTURES / "pin.txt"
SETTLE_SECONDS = 2.5


def log(text: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {text}", flush=True)


def port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except OSError:
        return False


async def wait_for_port(host: str, port: int, seconds: float) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if await asyncio.to_thread(port_open, host, port):
            return True
        await asyncio.sleep(2)
    return False


def load_identity() -> str:
    CAPTURES.mkdir(exist_ok=True)
    if IDENTITY_FILE.exists():
        return str(json.loads(IDENTITY_FILE.read_text())["device_id"])
    device_id = new_device_id()
    IDENTITY_FILE.write_text(json.dumps({"device_id": device_id}))
    return device_id


class Recorder:
    """Appends every raw message to a JSON-lines file and prints a short summary."""

    def __init__(self, path: Path) -> None:
        self._file = path.open("a", encoding="utf-8")

    async def __call__(self, message: Message) -> None:
        try:
            body: object = json.loads(message.payload) if message.payload else None
        except (UnicodeDecodeError, json.JSONDecodeError):
            body = {"hex": message.payload[:64].hex(), "size": len(message.payload)}
        self._file.write(
            json.dumps({"t": time.time(), "topic": message.topic, "body": body}) + "\n"
        )
        self._file.flush()
        short = json.dumps(body)[:160]
        log(f"<- {message.topic.replace('/remoteapp/mobile/', '')}  {short}")

    def close(self) -> None:
        self._file.close()


async def await_pin(seconds: float) -> str | None:
    PIN_FILE.unlink(missing_ok=True)
    log("*" * 60)
    log(f"PIN REQUIRED - read it on the TV and write it to {PIN_FILE}  ({seconds:.0f}s)")
    log("*" * 60)
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if PIN_FILE.exists() and PIN_FILE.read_text().strip():
            return PIN_FILE.read_text().strip()
        await asyncio.sleep(0.2)
    return None


async def run_queries(session: Session) -> None:
    queries: list[tuple[str, Action, object, Service | None]] = [
        ("gettvstate", Action.GET_TV_STATE, None, None),
        ("capability", Action.CAPABILITY, None, None),
        ("getdeviceinfo", Action.GET_DEVICE_INFO, None, None),
        ("gettvinfo", Action.GET_TV_INFO, None, None),
        ("getvolume", Action.GET_VOLUME, None, None),
        ("sourcelist", Action.SOURCE_LIST, None, None),
        ("applist", Action.APP_LIST, None, None),
        ("picturesetting@platform", Action.PICTURE_SETTING, {"action": "get_menu_info"}, None),
        ("picturesetting@ui", Action.PICTURE_SETTING, {"action": "get_menu_info"}, Service.UI),
    ]
    for label, action, payload, service in queries:
        log(f"-> {label}")
        await session.send(action, payload, service=service)  # type: ignore[arg-type]
        await asyncio.sleep(SETTLE_SECONDS)


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host")
    parser.add_argument("--cert", type=Path)
    parser.add_argument("--key", type=Path)
    parser.add_argument("--wait", type=float, default=180, help="seconds to wait for the TV")
    parser.add_argument("--pin-wait", type=float, default=90)
    args = parser.parse_args()

    log(f"waiting up to {args.wait:.0f}s for {args.host}:{DEFAULT_PORT} ...")
    if not await wait_for_port(args.host, DEFAULT_PORT, args.wait):
        log("port never opened: is the TV on and on the same network?")
        return 2

    device_id = load_identity()
    credentials = static_credentials(device_id)
    log(f"client identity: {credentials.client_id}")
    tls = TlsConfig(cert_file=args.cert, key_file=args.key)
    transport = MqttTransport(args.host, credentials, tls=tls)
    recorder = Recorder(CAPTURES / f"probe-{time.strftime('%Y%m%d-%H%M%S')}.jsonl")
    try:
        await transport.connect()
        log("MQTT connected")
        for topic_filter in mobile_filter(credentials.client_id):
            await transport.subscribe(topic_filter, recorder)
        session = Session(transport, credentials.client_id, timeout=8)
        pairing = Pairing(session)
        outcome = await pairing.start()
        log(f"pairing outcome: {outcome}")
        if outcome is PairingOutcome.PIN_REQUIRED:
            pin = await await_pin(args.pin_wait)
            if pin is None:
                log("no PIN received in time")
                return 3
            await pairing.submit_pin(pin)
            log("PIN accepted")
        await run_queries(session)
        log("done")
        return 0
    except VidaaError as exc:
        log(f"FAILED: {exc}")
        return 1
    finally:
        recorder.close()
        await transport.disconnect()


if __name__ == "__main__":
    # aiomqtt needs a selector loop; the default on Windows (proactor) lacks add_reader
    sys.exit(asyncio.run(main(), loop_factory=asyncio.SelectorEventLoop))
