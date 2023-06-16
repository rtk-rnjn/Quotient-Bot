from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

import re
from contextlib import suppress

import discord
import utils
from core import Cog
from models import EasyTag, TagCheck

from ..helpers import EasyMemberConverter, delete_denied_message


class TagEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @Cog.listener(name="on_message")
    async def on_tagcheck_msg(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        channel_id = message.channel.id

        if channel_id not in self.bot.cache.tagcheck:
            return

        tagcheck = await TagCheck.get_or_none(channel_id=channel_id)

        if not tagcheck:
            return self.bot.cache.tagcheck.discard(channel_id)

        ignore_role = tagcheck.ignorerole

        if ignore_role is not None and ignore_role in message.author.roles:  # type: ignore # line guarded #25
            return

        with suppress(discord.HTTPException, AttributeError):
            ctx = await self.bot.get_context(message)

            _react = True
            if tagcheck.required_mentions and not all(map(lambda m: not m.bot, message.mentions)):
                _react = False
                await message.reply("Kindly mention your real teammate.", delete_after=5)

            if len(message.mentions) < tagcheck.required_mentions:
                _react = False
                await message.reply(
                    f"You need to mention `{utils.plural(tagcheck.required_mentions):teammate|teammates}`.",
                    delete_after=5,
                )

            team_name = utils.find_team(message)
            await message.add_reaction(("❌", "✅")[_react])

            if _react:
                embed = self.bot.embed(ctx)
                embed.description = f"Team Name: {team_name}\nPlayer(s): {(', '.join(m.mention for m in message.mentions)) if message.mentions else message.author.mention}"
                await message.reply(embed=embed)

            if tagcheck.delete_after and not _react:
                self.bot.loop.create_task(delete_denied_message(message, 15))

    # ==========================================================================================================
    # ==========================================================================================================

    @Cog.listener(name="on_message")
    async def on_eztag_msg(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        if message.channel.id not in self.bot.cache.eztagchannels:
            return

        channel_id = message.channel.id
        eztag = await EasyTag.get_or_none(channel_id=channel_id)

        if not eztag:
            return self.bot.cache.eztagchannels.discard(channel_id)

        ignore_role = eztag.ignorerole

        if ignore_role is not None and ignore_role in message.author.roles:  # type: ignore # line guarded #74
            return

        with suppress(discord.HTTPException, AttributeError):
            ctx = await self.bot.get_context(message)

            tags = set(re.findall(r"\b\d{18}\b|\b@\w+", message.content, re.IGNORECASE))

            if not tags:
                await message.add_reaction("❌")
                return await ctx.reply(
                    "I couldn't find any discord tag in this form.\nYou can write your teammate's id , @their_name or @their_full_discord_tag",
                    delete_after=10,
                )

            members = []
            for m in tags:
                members.append(await EasyMemberConverter().convert(ctx, m))

            mentions = ", ".join(members)

            msg = await ctx.reply(f"```{message.clean_content}\nDiscord Tags: {mentions}```")

            if eztag.delete_after:
                self.bot.loop.create_task(delete_denied_message(message, 60))
                self.bot.loop.create_task(delete_denied_message(msg, 60))

    @Cog.listener(name="on_guild_channel_delete")
    async def on_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        if not isinstance(channel, discord.TextChannel):
            return

        channel_id = channel.id

        # Delete EasyTag record
        if channel_id in self.bot.cache.eztagchannels:
            await EasyTag.filter(channel_id=channel_id).delete()
            self.bot.cache.eztagchannels.remove(channel_id)

        # Delete TagCheck record
        if channel_id in self.bot.cache.tagcheck:
            await TagCheck.filter(channel_id=channel_id).delete()
            self.bot.cache.tagcheck.remove(channel_id)
