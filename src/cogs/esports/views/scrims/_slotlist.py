from __future__ import annotations

from contextlib import suppress

import discord

from core import Context
from models import Scrim
from utils import emote, inputs

from ._base import ScrimsView
from ._formatter import show_slotlist_formatter

__all__ = ("ManageSlotlist",)


class ManageSlotlist(discord.ui.Select):
    view: ScrimsView

    def __init__(self, ctx: Context, scrim: Scrim):
        super().__init__(
            placeholder="Select an option to manage slotlist.",
            options=[
                discord.SelectOption(
                    label="Repost Slotlist",
                    emoji="🔁",
                    description="Respost slotlist to a channel",
                    value="repost",
                ),
                discord.SelectOption(
                    label="Change Design",
                    description="Design slotlist of any scrim.",
                    emoji="⚙️",
                    value="format",
                ),
                discord.SelectOption(
                    label="Edit Slotlist",
                    description="Edit slotlist (Remove/Add New teams).",
                    emoji=emote.edit,
                    value="edit",
                ),
                discord.SelectOption(
                    label="Go Back",
                    description="Move back to Main Menu",
                    emoji=emote.exit,
                    value="back",
                ),
            ],
        )

        self.ctx = ctx
        self.record = scrim

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if (selected := self.values[0]) == "repost":
            m = await self.ctx.simple("Mention the channel to send slotlist.")
            channel = await inputs.channel_input(self.ctx, delete_after=True)
            await self.ctx.safe_delete(m)

            if not await self.record.teams_registered.count():
                return await self.ctx.error("No registrations found in {0}.".format(self.record), 5)

            m = await self.record.send_slotlist(channel)
            await self.ctx.success("Slotlist sent! [Click to Jump]({0})".format(m.jump_url), 5)

            from .main import ScrimsMain

            self.view.stop()
            v = ScrimsMain(self.ctx)
            v.message = await self.view.message.edit(content="", embed=await v.initial_embed(), view=v)

        elif selected == "format":
            self.view.stop()
            await show_slotlist_formatter(self.ctx, self.record, self.view.message)

        elif selected == "edit":
            if self.record.slotlist_message_id is None:
                return await self.ctx.error("Slotlist not found. Please repost.", 5)

            msg = None
            with suppress(discord.HTTPException):
                msg = await self.ctx.bot.get_or_fetch_message(
                    self.record.slotlist_channel, self.record.slotlist_message_id
                )
            if not msg:
                return await self.ctx.error("Slotlist Message not found. Repost first.", 5)

            return await self.ctx.success("Click `Edit` button under [slotlist message]({0}).".format(msg.jump_url), 6)

        elif selected == "back":
            from .main import ScrimsMain

            self.view.stop()
            v = ScrimsMain(self.ctx)
            v.message = await self.view.message.edit(content="", embed=await v.initial_embed(), view=v)
