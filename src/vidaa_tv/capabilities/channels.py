"""Live TV channels."""

from __future__ import annotations

from ..errors import UnsupportedFeatureError
from ..models import Channel, ChannelList
from ..protocol import parsers
from ..protocol.topics import Action
from ..session import Session


class Channels:
    def __init__(self, session: Session) -> None:
        self._session = session

    async def lists(self) -> list[ChannelList]:
        reply = await self._session.request(
            Action.GET_CHANNEL_LIST_INFO, parsers.is_channel_list_info
        )
        return parsers.parse_channel_lists(reply.payload)

    async def channels(self, channel_list: ChannelList) -> list[Channel]:
        reply = await self._session.request(
            Action.CHANNEL_LIST,
            parsers.is_channel_list,
            {"list_para": channel_list.id, "list_name": channel_list.name},
        )
        return parsers.parse_channels(reply.payload)

    async def tune(self, channel: Channel) -> None:
        """Switch to ``channel`` (obtained from ``channels``)."""
        await self._session.send(Action.CHANGE_CHANNEL, {"channel_param": channel.param})

    async def find(self, channel_list: ChannelList, query: str) -> Channel:
        """Find a channel by number or case-insensitive name."""
        for channel in await self.channels(channel_list):
            if query == channel.number or query.casefold() == channel.name.casefold():
                return channel
        raise UnsupportedFeatureError(f"unknown channel: {query}")
