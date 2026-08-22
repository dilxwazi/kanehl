import random
import json
import aiohttp
import asyncio
import logging
import discord
from discord.ext import commands, tasks

logging.getLogger('discord.state').setLevel(logging.ERROR)

with open("config.json") as f:
    config = json.load(f)

TOKENS = config["tokens"]
APPLICATION_ID = config["application_id"]
COMMAND_ID = config["command_id"]
COMMAND_NAME = config["command_name"]
VERSION = config["version"]
SERVERS = config["servers"]

class BumpBot(commands.Bot):
    def __init__(self, token, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = token
        self.session = None 
        self.custom_session_id = "".join(random.choice('0123456789abcdef') for _ in range(32))

    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        self.bump_loop.start()

    async def close(self):
        if self.session:
            await self.session.close()
        await super().close()

    async def trigger_command(self, guild_id, channel_id):
        if not self.session:
            return

        headers = {
            'Authorization': self.token,
            'Content-Type': 'application/json',
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "Referer": f"https://discord.com{guild_id}/{channel_id}",
        }
        
        session_id = getattr(self, "_connection", None)
        session_id = getattr(session_id, "session_id", self.custom_session_id)

        payload = {
            "type": 2,
            "application_id": APPLICATION_ID,
            "guild_id": str(guild_id),
            "channel_id": str(channel_id),
            "session_id": session_id,
            "data": {
                "version": VERSION,
                "id": COMMAND_ID,
                "name": COMMAND_NAME,
                "type": 1,
                "options": []
            }
        }

        try:
            async with self.session.post("https://discord.com", headers=headers, json=payload) as resp:
                if resp.status in:
                    print(f"✅ [{self.token[:10]}...] Befehl erfolgreich gesendet in Guild {guild_id}")
                else:
                    print(f"❌ [{self.token[:10]}...] API-Fehler (Status {resp.status}) in Guild {guild_id}")
        except Exception as e:
            print(f"⚠️ Netzwerkfehler bei Bot [{self.token[:10]}...]: {e}")

    @tasks.loop(hours=2, minutes=1)
    async def bump_loop(self):
        await asyncio.sleep(random.randint(2, 8))
        
        for server in SERVERS:
            guild_id = int(server["guild_id"])
            channel_id = int(server["channel_id"])
            invite_code = server.get("invite")

            guild = self.get_guild(guild_id)
            
            if guild is None:
                print(f"⚠️ [{self.token[:10]}...] Nicht auf Server {guild_id}. Versuche beizutreten...")
                
                if not invite_code:
                    print(f"❌ [{self.token[:10]}...] Beitritt unmöglich: Kein 'invite' in der config.json hinterlegt.")
                    continue

                try:
                    await self.accept_invite(invite_code)
                    print(f"📥 [{self.token[:10]}...] Erfolgreich über Invite beigetreten! Warte kurz auf Cache-Update...")
                    await asyncio.sleep(5)
                    
                    guild = self.get_guild(guild_id)
                    if guild is None:
                        print(f"❌ [{self.token[:10]}...] Beitritt schien erfolgreich, Server wurde aber nicht im Cache gefunden.")
                        continue
                except discord.HTTPException as e:
                    print(f"❌ [{self.token[:10]}...] Beitritt zu Server fehlgeschlagen: {e}")
                    continue

            channel = guild.get_channel(channel_id)
            if channel is None:
                print(f"⚠️ [{self.token[:10]}...] Kanal {channel_id} auf Server '{guild.name}' existiert nicht oder keine Rechte!")
                continue

            print(f"🚀 [{self.token[:10]}...] Valide! Sende Interaktion for Server '{guild.name}'...")
            await self.trigger_command(guild_id, channel_id)
            
            await asyncio.sleep(random.randint(3, 7))

    @bump_loop.before_loop
    async def before_bump_loop(self):
        await self.wait_until_ready()

async def main():
    bots = []
    for token in TOKENS:
        bot = BumpBot(token=token, command_prefix="$", self_bot=True)
        bots.append(bot)

    await asyncio.gather(*[bot.start(token) for bot, token in zip(bots, TOKENS)])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Skript manuell beendet.")