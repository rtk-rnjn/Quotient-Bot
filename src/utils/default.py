from __future__ import annotations

import re
from datetime import datetime
from itertools import islice
from typing import Union
from unicodedata import normalize as nm

import discord

from constants import IST


def get_chunks(iterable, size: int):
    it = iter(iterable)
    return iter(lambda: tuple(islice(it, size)), ())


def split_list(data: list, per_list: int):
    data = list(data)

    new = []

    for i in range(0, len(data), per_list):
        new.append(data[i : i + per_list])

    return new


def find_team(message: discord.Message):
    """
    Finds team name from a message
    """
    author = message.author
    teamname = re.search(r"team.*", message.content)
    if teamname is None:
        return f"{author}'s team"

    # teamname = (re.sub(r"\b[0-9]+\b\s*|team|name|[^\w\s]", "", teamname.group())).strip()
    teamname: str = re.sub(r"<@*#*!*&*\d+>|team|name|[^\w\s]", "", teamname.group()).strip()

    teamname = f"Team {teamname.title()}" if teamname else f"{author}'s team"
    return teamname


def find_drop_location(message: discord.Message):
    """
    Find team's drop location from message, if provided.
    """
    drop_location = re.search(r"drop.*", message.content)
    if drop_location is None:
        return None

    drop_location = re.sub(r"<@*#*!*&*\d+>|drop|location|[^\w\s]", "", drop_location.group()).strip()

    return drop_location.title() if drop_location else None


def regional_indicator(c: str) -> str:
    """Returns a regional indicator emoji given a character."""
    return chr(0x1F1E6 - ord("A") + ord(c.upper()))


def keycap_digit(c: Union[int, str]) -> str:
    """Returns a keycap digit emoji given a character."""
    c = int(c)
    if 0 < c < 10:
        return str(c) + "\U0000FE0F\U000020E3"
    if c == 10:
        return "\U000FE83B"
    raise ValueError("Invalid keycap digit")


async def aenumerate(asequence, start=0):
    """Asynchronously enumerate an async iterator from a given start value"""
    n = start
    async for elem in asequence:
        yield n, elem
        n += 1


def get_ipm(bot):
    """Returns Quotient's cmds invoke rate per minute"""
    time = (datetime.now(tz=IST) - bot.start_time).total_seconds()
    per_second = bot.cmd_invokes / time
    per_minute = per_second * 60
    return per_minute
