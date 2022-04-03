from __future__ import annotations
import typing as T

from ...views.base import EsportsBaseView
from core import Context

from discord import ButtonStyle, ui, Interaction
import discord

from ._wiz import ScrimSetup
from models import Scrim
from utils import emote


class ScrimsMain(EsportsBaseView):
    def __init__(self, ctx: Context):
        super().__init__(ctx, timeout=100)

        self.ctx = ctx

    async def initial_embed(self):
        _e = discord.Embed(color=0x00FFB3, description="Smart Scrims Manager", url=self.ctx.config.SERVER_LINK)

        to_show = []
        for idx, _r in enumerate(await Scrim.filter(guild_id=self.ctx.guild.id).order_by("open_time"), start=1):
            to_show.append(f"`{idx}.` {(emote.xmark,emote.check)[_r.stoggle]}: {str(_r)} ")

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

    @discord.ui.button(label="Start/Stop Reg", style=ButtonStyle.green)
    async def toggle_reg(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()

    @discord.ui.button(label="Reserve Slots", style=ButtonStyle.green)
    async def reserve_slots(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()

    @discord.ui.button(label="Ban/Unban", style=ButtonStyle.red)
    async def ban_unban(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()

    @discord.ui.button(label="Design", style=ButtonStyle.red)
    async def change_design(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()

    @discord.ui.button(label="Design", style=ButtonStyle.red)
    async def change_design(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()