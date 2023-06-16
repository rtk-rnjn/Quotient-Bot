from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List

from models import Guild, Tourney

from ...views.base import EsportsBaseView

if TYPE_CHECKING:
    from core import Quotient

import asyncio

import discord
from discord.ext import commands
from humanize import precisedelta

import config
from core import Context
from utils import QuoRole, emote, get_chunks, inputs, truncate_string


class TourneyGroupManager(EsportsBaseView):
    def __init__(self, ctx: Context, *, tourney: Tourney, size: int = 20):
        super().__init__(ctx, timeout=60, title="Tourney Group Manager")

        self.ctx = ctx
        self.tourney = tourney
        self.size = size
        self.bot: Quotient = ctx.bot

    @staticmethod
    def initial_embed(tourney: Tourney, size: int) -> discord.Embed:
        e = discord.Embed(color=0x00FFB3, title="Tourney Group Manager")
        e.description = (
            f"**[Tourney Slot Manager]({config.SERVER_LINK})** ─ {tourney}\n"
            f"**Group Size: `{size}`**\n\n"
            "• Click `Publish` to send group embeds in a channel.\n"
            "• Click `Give Roles` to provide group roles to team leaders.\n"
        )

        return e

    @discord.ui.button(custom_id="publish_groups", label="Publish Group List")
    async def publish_tourney_groups(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer(ephemeral=True)

        m = await self.ask_embed(
            "Kindly mention the channel where you want me to send group list.\n\n"
            "`Make sure I have embed_links and manage_webhooks permission there.`"
        )

        _channel = await inputs.channel_input(self.ctx, self.check, delete_after=True)
        await self.ctx.maybe_delete(m)

        if not _channel.permissions_for(self.ctx.guild.me).manage_webhooks:
            return await self.error_embed(f"Make sure I have `manage_webhooks` permission in {_channel.mention}.")

        _list = []

        for idx, _chunk in enumerate(await self.tourney.get_groups(self.size), start=1):
            e = discord.Embed(color=self.bot.color, title=f"{self.tourney.name} Group {idx}")
            e.set_footer(text=self.ctx.guild.name, icon_url=getattr(self.ctx.guild.icon, "url", None))
            e.description = ""
            for count, _slot in enumerate(_chunk, start=1):
                e.description += f"`{count:02}` • **{truncate_string(_slot.team_name,30)}** (<@{_slot.leader_id}>)\n"

            _list.append(e)

        _view = GroupListView(self.ctx, tourney=self.tourney, size=self.size, channel=_channel, embeds=_list)
        _view.message = await interaction.followup.send(embed=GroupListView.initial_embed(self.tourney), view=_view)

    @discord.ui.button(custom_id="give_group_roles", label="Give Roles")
    async def give_group_roles(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer(ephemeral=True)
        if len(self.ctx.guild.roles) >= 235:
            return await self.error_embed(
                "Your server is about to hit the max roles limit (250 roles), please delete some first."
            )

        if not self.ctx.guild.me.guild_permissions.manage_roles:
            return await self.error_embed(
                "Kindly give me `manage_roles` permission and move my role above your group roles."
            )

        # TODO: check manager roles , total roles less than 195
        m = await self.ask_embed(
            f"Write the group number and the name of group role.\n"
            "**Format:** `Group Number, Name of Group Role`\n\n"
            "Note that you can also mention the role instead of name to give it to users, "
            "or just write its name, if there is no role of that name, Quotient "
            "will create the role and give it to group leaders.\n\n"
            "**Example:**```1, @group_role\n2, Group role\n3, @3rd_group```\n"
            "*Enter upto 15 roles at a time.*",
            image="https://cdn.discordapp.com/attachments/851846932593770496/901862381473374299/unknown.png",
        )

        _roleinfo = await inputs.string_input(self.ctx, self.check, delete_after=True)
        await self.ctx.safe_delete(m)

        if (_roleinfo := _roleinfo.strip()) == "cancel":
            return

        _split = _roleinfo.split("\n")

        if len(_split) > 15:
            return await self.error_embed(
                "Group Roles can be given to upto 15 groups at a time."
            )

        for _group in _split:
            try:
                group, role = _group.strip().strip(",").split(",")
                group = int(group)

            except ValueError:
                return await self.error_embed(
                    f"Invalid format given in `line {_split.index(_group) + 1}`.```{_roleinfo}```",
                    footer="Auto-deleting this message in 10s.",
                    delete_after=10,
                )

        _e = discord.Embed(
            color=self.bot.color,
            title="Giving Group Roles:",
            description=f"{emote.check} Starting the role distribution!\n",
        )

        m: discord.Message = await self.ctx.send(embed=_e)

        _t = datetime.now()

        for _group in _split:
            group, role = _group.strip().strip(",").split(",")
            group = int(group)

            try:
                role = await QuoRole().convert(self.ctx, role := role.strip())
                _e.description += f"{emote.check} {role.mention} Found...\n"
                await m.edit(embed=_e)

                if not role < self.ctx.guild.me.top_role:
                    _e.description += f"{emote.error} Skipping {role.mention}, because it is above my highest role ({self.ctx.guild.me.top_role.mention}).\n"
                    await m.edit(embed=_e)
                    continue

            except commands.RoleNotFound:
                _e.description += f"{emote.xmark} {role} Not Found, Creating new role..\n"
                role = await self.ctx.guild.create_role(name=role, reason=f"Created by {self.ctx.author} for grouping")

            _e.description += f"{emote.check} {role.mention} Assigning to team leaders of Group {group}\n"
            await m.edit(embed=_e)

            actual_group = await self.tourney.get_group(group, self.size)

            try:
                counter = 0
                for _slot in actual_group:
                    if member := self.ctx.guild.get_member(_slot.leader_id):
                        counter += 1
                        if role not in member.roles:
                            self.bot.loop.create_task(
                                member.add_roles(role, reason=f"Given by {self.ctx.author} for tourney grouping")
                            )

                _e.description += f"{emote.check} {counter} people are given {role.mention}\n"
                await m.edit(embed=_e)
                counter = 0

            except TypeError:
                _e.description += f"{emote.xmark} Group {group} is empty.\n"
                await m.edit(embed=_e)
                continue

            await asyncio.sleep(0.6)

        _e.description += f"{emote.check} Done! (Time taken: `{precisedelta(datetime.now()-_t)}`)\n"
        await m.edit(embed=_e)
        await self.ctx.safe_delete(m, 10)


class GroupListView(EsportsBaseView):
    def __init__(
        self,
        ctx: Context,
        *,
        tourney: Tourney,
        size: int,
        channel: discord.TextChannel,
        embeds: List[discord.Embed],
    ):
        super().__init__(ctx, timeout=30, title="Group List Publisher")

        self.ctx = ctx
        self.bot: Quotient = ctx.bot
        self.tourney = tourney
        self.size = size
        self.channel = channel
        self.embeds = embeds

    @staticmethod
    def initial_embed(tourney: Tourney) -> discord.Embed:
        return discord.Embed(
            color=0x00FFB3,
            description=(
                f"**How would you like to publish the group list of {tourney}?**\n\n"
                "• `Webhook` will create a webhook in the channel and will send group embeds with your server's logo and name.\n"
                "• `Bot Option` will just make Quotient send the embeds.\n\n"
                "*Webhook Option is more cool.*"
            ),
        )

    @discord.ui.button(custom_id="publish_g_hook", emoji="<a:diamond:899295009289949235>", label="Webhook (Recommended)")
    async def publish_groups_webhook(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer(ephemeral=True)

        if not await self.ctx.is_premium_guild():
            from cogs.premium.views import PremiumView

            _view = PremiumView()
            return await interaction.followup.send(embed=_view.premium_embed, view=_view)

        try:
            _webhook = await self.channel.create_webhook(
                name="Quotient Group List", reason=f"Created by {self.ctx.author} to send group list"
            )
        except Exception as e:
            return await self.error_embed(e)

        m = await self.ctx.simple(f"Publishing, please wait {emote.loading}")
        for _chunk in get_chunks(self.embeds, 2):
            await _webhook.send(
                embeds=_chunk,
                username=self.ctx.guild.name,
                avatar_url=getattr(self.ctx.guild.icon, "url", None),
            )

        await _webhook.delete()
        await self.ctx.safe_delete(m)
        await self.ctx.success("Group list published.", 4)

    @discord.ui.button(custom_id="publish_g_bot", emoji="<:pain:837567768106238002>", label="With Bot")
    async def publish_groups_bot(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer(ephemeral=True)

        m = await self.ctx.simple(f"Publishing, please wait {emote.loading}")
        for _chunk in get_chunks(self.embeds, 2):
            await self.channel.send(embeds=_chunk)

        await self.ctx.safe_delete(m)
        await self.ctx.success("Group list published.", 4)

    @discord.ui.button(custom_id="publish_g_delete", emoji=emote.trash)
    async def publish_groups_delete(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.delete_original_message()
