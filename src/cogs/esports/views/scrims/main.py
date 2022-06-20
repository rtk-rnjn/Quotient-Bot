from __future__ import annotations

import typing as T

import discord
from discord import ButtonStyle, Interaction, ui

from core import Context
from models import Scrim
from utils import discord_timestamp, emote

from ._design import ScrimDesign
from ._edit import ScrimsEditor
from ._reserve import ScrimsSlotReserve
from ._wiz import ScrimSetup

from ._slotlist import ManageSlotlist
from ._base import ScrimsView
from ._toggle import ScrimsToggle
from ._ban import ScrimBanManager


class ScrimsMain(ScrimsView):
    def __init__(self, ctx: Context):
        super().__init__(ctx, timeout=100)

        self.ctx = ctx

    async def initial_embed(self):
        _e = discord.Embed(color=0x00FFB3, title="Quotient's Smart Scrims Manager", url=self.ctx.config.SERVER_LINK)

        to_show = []
        for idx, _r in enumerate(await Scrim.filter(guild_id=self.ctx.guild.id).order_by("open_time"), start=1):
            to_show.append(
                f"`{idx}.` {(emote.xmark,emote.check)[_r.stoggle]}: {str(_r)} - {discord_timestamp(_r.open_time,'t')}"
            )

        _e.description = "\n".join(to_show) if to_show else "```Click Create button for new Scrim.```"

        _e.set_footer(
            text="Quotient Prime allows unlimited scrims.",
            icon_url=getattr(self.ctx.author.display_avatar, "url", discord.Embed.Empty),
        )

        if not to_show:
            for _ in self.children[1:]:
                _.disabled = True

        return _e

    @discord.ui.button(label="Create Scrim", style=ButtonStyle.green)
    async def create_new_scrim(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()

        if not await self.ctx.is_premium_guild():
            ...

        self.stop()
        v = ScrimSetup(self.ctx)
        v.message = await self.message.edit(embed=v.initial_message(), view=v)

    @discord.ui.button(label="Edit Settings", style=ButtonStyle.blurple)
    async def edit_scrim(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()
        scrim = await Scrim.show_selector(self.ctx, multi=False)
        self.stop()

        v = ScrimsEditor(self.ctx, scrim)
        await v._add_buttons()
        v.message = await self.message.edit(embed=await v.initial_message, view=v)

    @discord.ui.button(label="Instant Start/Stop Reg", style=ButtonStyle.green)
    async def toggle_reg(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()

        scrim = await Scrim.show_selector(
            self.ctx, multi=False, placeholder="Please select the scrim to stop or start registration."
        )
        self.stop()
        v = ScrimsToggle(self.ctx, scrim)
        await v._add_buttons()
        v.message = await self.message.edit(embed=await v.initial_message, view=v)

    @discord.ui.button(label="Reserve Slots", style=ButtonStyle.green)
    async def reserve_slots(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()
        scrim = await Scrim.show_selector(self.ctx, multi=False)
        self.stop()

        view = ScrimsSlotReserve(self.ctx, scrim)
        await view.add_buttons()
        view.message = await self.message.edit(embed=await view.initial_embed, view=view)

    @discord.ui.button(label="Ban/Unban", style=ButtonStyle.red)
    async def ban_unban(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()

        scrim = await Scrim.show_selector(self.ctx, multi=False)
        self.stop()

        v = ScrimBanManager(self.ctx, scrim)
        await v._add_buttons()
        v.message = await self.message.edit(embed=await v.initial_message, view=v)

    @discord.ui.button(label="Design", style=ButtonStyle.red)
    async def change_design(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()

        scrim = await Scrim.show_selector(self.ctx, multi=False)
        self.stop()

        view = ScrimDesign(self.ctx, scrim)
        await view._add_buttons()
        view.message = await self.message.edit(embed=await view.initial_embed, view=view)

    @discord.ui.button(label="Manage Slotlist", style=ButtonStyle.blurple)
    async def manage_slotlist(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()

        scrim = await Scrim.show_selector(
            self.ctx, multi=False, placeholder="Please select the scrim to manage slotlist."
        )

        self.stop()
        v = ScrimsView(self.ctx)
        v.add_item(ManageSlotlist(self.ctx, scrim))
        v.message = await self.message.edit("Please choose an action:", embed=None, view=v)

    @discord.ui.button(label="Scrim not working, Need Help!", style=ButtonStyle.red)
    async def troubleshoot_scrim(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()

        scrim = await Scrim.show_selector(
            self.ctx, multi=False, placeholder="Please select the scrim you need help with."
        )
        _e = discord.Embed(color=self.bot.color, title="Analyzing {0}...".format(scrim))
        _e.description = ""

        await self.message.edit(embed=_e)