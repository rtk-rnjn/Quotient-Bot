import typing as T

import discord
from models import Guild
from pydantic import BaseModel

__all__ = ("QGuild",)


class QGuild(BaseModel):
    id: str
    name: str
    icon: str
    channels: T.List[dict]
    roles: T.List[dict]
    boosted_by: dict
    dashboard_access: int

    @staticmethod
    async def from_guild(guild: discord.Guild, perms: int):
        _d = {
            "id": str(guild.id),
            "name": guild.name,
            "dashboard_access": perms,
            "icon": getattr(
                guild.icon, "url", "https://cdn.discordapp.com/embed/avatars/0.png"
            ),
            "channels": [
                {"id": str(c.id), "name": c.name} for c in guild.text_channels
            ],
            "roles": [
                {
                    "id": str(r.id),
                    "name": r.name,
                    "color": int(r.color),
                    "managed": r.managed,
                }
                for r in guild.roles
            ],
            "boosted_by": {},
        }

        record = await Guild.get(pk=guild.id)

        if record.is_premium:
            booster = await record.bot.get_or_fetch_member(guild, record.made_premium_by)
            _d["boosted_by"] = {
                "id": str(getattr(booster, "id", 12345)),
                "username": getattr(booster, "name", "Unknown User"),
                "discriminator": getattr(booster, "discriminator", "#0000"),
                "avatar": booster.display_avatar.url if booster else "https://cdn.discordapp.com/embed/avatars/0.png",
            }

        return QGuild(**_d)
