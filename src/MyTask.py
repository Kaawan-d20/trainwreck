from interactions import Task, TimeTrigger, OrTrigger, Embed, Extension

from Calendar import Calendar, changed_events
from UserBase import get_user_base
from Tool import get_tool
from enum import Enum

from datetime import datetime, date, timedelta
from dotenv import load_dotenv
import os
import re


class MyTask(Extension):
    """Classe contenant les Tasks."""
    def __init__(self, bot):
        self.bot = bot
        self.ping_chan = bot.get_channel(os.getenv("PING_CHAN"))
        self.tool = get_tool(bot)

    @Task.create(OrTrigger(
        TimeTrigger(hour=5, minute=55, utc=False),  # juste avant l'envoi automatique.
        TimeTrigger(hour=7, minute=0, utc=False),
        TimeTrigger(hour=8, minute=0, utc=False),
        TimeTrigger(hour=10, minute=0, utc=False),
        TimeTrigger(hour=12, minute=0, utc=False),
        TimeTrigger(hour=14, minute=0, utc=False),
        TimeTrigger(hour=16, minute=0, utc=False),
        TimeTrigger(hour=18, minute=0, utc=False),
        TimeTrigger(hour=20, minute=0, utc=False)
    ))
    async def update_calendar(self):
        """Permet de mettre à jour le calendrier et de vérifier qu'il n'y a pas eu de changement."""
        # sup :set[Event]         = set()
        # add :set[Event]         = set()
        # mod :set[(Event,Event)] = set()
        old_calendar = Calendar(False)
        new_calendar = Calendar(True)

        sup, add, mod = changed_events(old_calendar, new_calendar)
        embeds: list[Embed] = []

        if len(sup) > 0:
            descstr = ""
            for event in sup:
                descstr += f"- {self.tool.ping_liste(event)} {str(event)}\n"
            embeds.append(Embed(title="Événements supprimés :", description=descstr, color=0xEd4245))

        if len(add) > 0:
            descstr = ""
            for event in add:
                descstr += f"- {self.tool.ping_liste(event)} {str(event)}\n"
            embeds.append(Embed(title="Événements ajoutés :", description=descstr, color=0x57f287))

        if len(mod) > 0:
            descstr = ""
            for (old, new) in mod:
                ping = self.tool.ping_liste(old)
                if old.group != new.group:
                    ping += f" {self.tool.ping_liste(new)}"
                descstr += f"- {ping} {str(old)} → {str(new)}\n"
            embeds.append(Embed(title="Événements modifiés :", description=descstr, color=0x5865f2))

        if len(embeds):
            await self.ping_chan.send(embeds=embeds)

    @Task.create(TimeTrigger(hour=6, minute=0, utc=False))
    async def daily_morning_update(self):
        """Permet d'envoyer les EDT automatiquement."""
        user_base = get_user_base()
        # Pour l'envoi hebdomadaire.
        if datetime.today().weekday() == 0:
            for id in user_base.weekly_subscribed_users:
                await self.tool.send_weekly_update(self.bot.get_user(id))
        # Pour l'envoi quotidien.
        if datetime.today().weekday() <= 4:  # Si on est le week end
            for id in user_base.daily_subscribed_users:
                await self.tool.send_daily_update(self.bot.get_user(id))