from vidaa_tv.discovery.neighbour import parse_arp_output, parse_proc_net_arp

PROC = """IP address       HW type     Flags       HW address            Mask     Device
192.0.2.10       0x1         0x2         aa:bb:cc:dd:ee:ff     *        eth0
192.0.2.11       0x1         0x0         00:00:00:00:00:00     *        eth0
"""


def test_parse_proc_net_arp() -> None:
    assert parse_proc_net_arp(PROC, "192.0.2.10") == "AA:BB:CC:DD:EE:FF"
    assert parse_proc_net_arp(PROC, "192.0.2.11") is None
    assert parse_proc_net_arp(PROC, "192.0.2.99") is None


def test_parse_arp_output_windows_style() -> None:
    text = """
Interface: 192.0.2.5 --- 0x11
  Internet Address      Physical Address      Type
  192.0.2.10            aa-bb-cc-dd-ee-ff     dynamic
"""
    assert parse_arp_output(text, "192.0.2.10") == "AA:BB:CC:DD:EE:FF"


def test_parse_arp_output_bsd_style() -> None:
    text = "? (192.0.2.10) at aa:bb:cc:dd:ee:ff on en0 ifscope [ethernet]"
    assert parse_arp_output(text, "192.0.2.10") == "AA:BB:CC:DD:EE:FF"
    assert parse_arp_output("no entry", "192.0.2.10") is None
