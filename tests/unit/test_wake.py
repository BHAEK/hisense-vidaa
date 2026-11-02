import pytest

from vidaa_tv.discovery.wake import (
    broadcast_addresses,
    magic_packet,
    parse_mac,
    vidaa_packet,
)

MAC = "AA:BB:CC:DD:EE:FF"


def test_parse_mac_accepts_separators() -> None:
    assert parse_mac("aa-bb-cc-dd-ee-ff") == bytes.fromhex("AABBCCDDEEFF")
    with pytest.raises(ValueError):
        parse_mac("AA:BB")


def test_magic_packet_layout() -> None:
    packet = magic_packet(MAC)
    assert packet[:6] == b"\xff" * 6
    assert packet[6:] == bytes.fromhex("AABBCCDDEEFF") * 16
    assert len(packet) == 102


def test_vidaa_packet_has_six_zero_bytes_trailer() -> None:
    packet = vidaa_packet(MAC)
    assert packet[:102] == magic_packet(MAC)
    assert packet[102:] == b"\x00" * 6


def test_broadcast_addresses() -> None:
    assert broadcast_addresses() == ("255.255.255.255",)
    assert broadcast_addresses("192.0.2.10") == ("255.255.255.255", "192.0.2.255")
    assert broadcast_addresses("tv.local") == ("255.255.255.255",)
