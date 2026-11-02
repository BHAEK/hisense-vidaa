import asyncio
import json

from tests.fakes import FakeTransport
from vidaa_tv.capabilities.channels import Channels
from vidaa_tv.models import Channel, ChannelList
from vidaa_tv.session import Session

CLIENT = "AA$vidaa_common"
BASE = f"/remoteapp/mobile/{CLIENT}/platform_service/data"


async def test_lists_and_channels_and_tune() -> None:
    transport = FakeTransport()
    channels = Channels(Session(transport, CLIENT, timeout=1))

    async def tv() -> None:
        await asyncio.sleep(0.01)
        info = [{"list_name": "DTT", "list_para": "L1", "list_version": "34"}]
        await transport.deliver(f"{BASE}/getchannellistinfo", json.dumps(info).encode())
        await asyncio.sleep(0.05)
        listing = {
            "list_para": "L1",
            "list_name": "DTT",
            "list": [{"channel_num": "5", "channel_name": "Canale5 HD", "channel_param": "P5"}],
        }
        await transport.deliver(f"{BASE}/channellist", json.dumps(listing).encode())

    reply = asyncio.create_task(tv())
    [channel_list] = await channels.lists()
    assert channel_list == ChannelList("L1", "DTT", "34")
    found = await channels.find(channel_list, "canale5 hd")
    await reply
    assert found == Channel("5", "Canale5 HD", "P5")
    await channels.tune(found)
    assert transport.published[-1].payload == b'{"channel_param":"P5"}'
    assert transport.published[-2].payload == b'{"list_para":"L1","list_name":"DTT"}'
