from __future__ import annotations
from contextlib import suppress
import typing as T

from .conts import Team
from core import Context, QuotientView
import discord
from utils import emote


class PointsTable(QuotientView):
    def __init__(self, ctx: Context):
        super().__init__(ctx, timeout=100)

        self.teams: T.List[Team] = []
        self.header: str = None

        self.footer: str = None

    @property
    def initial_msg(self):
        _e = discord.Embed(color=self.bot.color, title="Points Table Maker")
        _e.description = "S.No. " + "Team Name".ljust(22) + "Place Pts".ljust(5) + "Kills".ljust(5) + "Total\n" "```\n"
        for idx, team in enumerate(self.teams, 1):
            _e.description += (
                f"{idx:02}. {team.name.ljust(22)} {str(team.placepts).ljust(5)} {str(team.kills).ljust(5)}"
                f"{str(team.totalpts)}\n"
            )

        _e.description += "```"
        _e.set_footer(text=f"Header: {self.header or 'Not Set'}\nFooter: {self.footer or 'Not Set'}")
        return _e

    async def refresh_view(self):
        self.message = await self.message.edit(embed=self.initial_msg, view=self)

    @discord.ui.button(label="Title & Footer")
    async def set_title(self, inter: discord.Interaction ,btn: discord.Button):
        modal = ...
        await inter.response.send_modal()
        await modal.wait()

        self.header = modal.header.value
        self.footer = modal.footer.value

        await self.refresh_view()

    @discord.ui.button(label="Add Team")
    async def add_team(self, inter: discord.Interaction ,btn: discord.Button):
        modal = TeamInput()
        await inter.response.send_modal(modal)
        await modal.wait()

        kills, placepts = None, None

        with suppress(ValueError):
            kills = int(modal.kills.value)
            placepts = int(modal.placepts.value)

        if not all((kills, placepts)):
            return await self.ctx.error("Invalid input", 5)

        self.teams.append(
            Team(
                name=modal.team_name.value,
                matches=modal.matches.value,
                kills=kills,
                placepts=placepts,
                totalpts=kills + placepts,
            )
        )
        await self.refresh_view()

    @discord.ui.button(label="Remove Team")
    async def remove_team(self, inter: discord.Interaction ,btn: discord.Button):
        await inter.response.defer()
        if not self.teams:
            return await self.ctx.error("No teams to remove.", 5)

        v = QuotientView(self.ctx)
        v.add_item(TeamSelector(self.teams))
        v.message = await inter.followup.send("", view=v, ephemeral=True)
        await v.wait()

        for _ in self.teams:
            if str(_.id) in v.custom_id:
                self.teams.remove(_)

        await self.refresh_view()

    @discord.ui.button(label="Create Image")
    async def create_image(self, inter: discord.Interaction ,btn: discord.Button):
        await inter.response.send_message(self.teams)


class HeaderInput(discord.ui.Modal, title="Set Title & Footer"):
    header = discord.ui.TextInput(
        label="Header (optional)",
        max_length=100,
        placeholder="Enter a title for the table",
    )
    footer = discord.ui.TextInput(
        label="Footer (optional)",
        max_length=100,
        placeholder="Enter a footer for the table",
    )
    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()


class TeamInput(discord.ui.Modal, title="Add New Team"):
    team_name = discord.ui.TextInput(
        label="Team Name",
        placeholder="Enter team name",
        max_length=20,
        min_length=4,
        required=True,
        style=discord.TextStyle.short,
    )

    matches = discord.ui.TextInput(
        label="No. of Matches",
        placeholder="Enter no. of matches",
        max_length=2,
        min_length=1,
        required=True,
        default=1,
    )

    kills = discord.ui.TextInput(
        label="No. of Kills",
        placeholder="Enter no. of kills",
        max_length=2,
        min_length=1,
        required=True,
    )

    placepts = discord.ui.TextInput(
        label="Place Points",
        placeholder="Enter placement points",
        max_length=2,
        min_length=1,
        required=True,
    )
    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

class TeamSelector(discord.ui.Select):
    view: QuotientView

    def __init__(self, teams: T.List[Team]):
        _options = [
            discord.SelectOption(
                label=_.name, value=str(_.id), emoji=emote.TextChannel
            )
            for _ in teams
        ]
        super().__init__(placeholder="Select the teams you want to remove...", max_values=len(teams), options=_options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.custom_id = self.values
        self.view.stop()
