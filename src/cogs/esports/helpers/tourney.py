from __future__ import annotations

import re
from contextlib import suppress
from typing import Iterable, List, Optional

import discord
from constants import EsportsRole, RegDeny
from models import TMSlot, Tourney


def get_tourney_slots(slots: List[TMSlot]) -> Iterable[int]:
    for slot in slots:
        yield slot.leader_id


def tourney_work_role(tourney: Tourney, _type: EsportsRole):

    if _type == EsportsRole.ping:
        role = tourney.ping_role

    elif _type == EsportsRole.open:
        role = tourney.open_role

    if not role:
        return None

    if role == tourney.guild.default_role:
        return "@everyone"

    return getattr(role, "mention", "role-deleted")


def before_registrations(message: discord.Message, role: discord.Role) -> bool:
    assert message.guild is not None

    if not role:
        return False

    me = message.guild.me
    channel = message.channel

    return all(
        (
            me.guild_permissions.manage_roles,
            role < message.guild.me.top_role,
            channel.permissions_for(me).add_reactions,
            channel.permissions_for(me).use_external_emojis,
        )
    )


async def check_tourney_requirements(bot, message: discord.Message, tourney: Tourney) -> bool:
    _bool = True

    if tourney.teamname_compulsion:
        teamname = re.search(r"team.*", message.content)
        if not teamname or not teamname.group().strip():
            _bool = False
            bot.dispatch("tourney_registration_deny", message, RegDeny.noteamname, tourney)

    if tourney.required_mentions and not all(map(lambda m: not m.bot, message.mentions)):
        _bool = False
        bot.dispatch("tourney_registration_deny", message, RegDeny.botmention, tourney)

    elif len(message.mentions) < tourney.required_mentions:
        _bool = False
        bot.dispatch("tourney_registration_deny", message, RegDeny.nomention, tourney)

    elif message.author.id in tourney.banned_users:
        _bool = False
        bot.dispatch("tourney_registration_deny", message, RegDeny.banned, tourney)

    elif len(message.content.splitlines()) < tourney.required_lines:
        _bool = False
        bot.dispatch("tourney_registration_deny", message, RegDeny.nolines, tourney)

    return _bool


async def t_ask_embed(ctx, value, description: str):
    embed = discord.Embed(
        color=ctx.bot.color,
        title=f"🛠️ Tournament Manager ({value}/5)",
        description=description,
    )
    embed.set_footer(text='Reply with "cancel" to stop the process.')
    await ctx.send(embed=embed, embed_perms=True)


async def update_confirmed_message(tourney: Tourney, link: str):
    _ids = [int(i) for i in link.split("/")[5:]]

    message = None

    with suppress(discord.HTTPException, IndexError):
        message = await tourney.guild.get_channel(_ids[0]).fetch_message(_ids[1])

        if message:
            e = message.embeds[0]

            e.description = f"~~{e.description.strip()}~~"
            e.title = "Cancelled Slot"
            e.color = discord.Color.red()

            await message.edit(embed=e)


async def get_tourney_from_channel(guild_id: int, channel_id: int) -> Optional[Tourney]:
    tourneys = await Tourney.filter(guild_id=guild_id)

    for tourney in tourneys:
        if await tourney.media_partners.filter(pk=channel_id).exists():
            return tourney

    return None
