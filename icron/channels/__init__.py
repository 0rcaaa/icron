"""Chat channels module with plugin architecture."""

from icron.channels.base import BaseChannel
from icron.channels.manager import ChannelManager

__all__ = ["BaseChannel", "ChannelManager"]
