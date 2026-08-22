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
        self.session_id = "".join(random.choice('0123456789abcdef') for _ in range(32))

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
        
        payload = {
            "type": 2,
            "application_id": APPLICATION_ID,
            "guild_id": guild_id,
            "channel_id": channel_id,
            "session_id": self.session_id,
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
                if resp.status == 200 or resp.status == 204:
                    print(f"✅ [{self.token[:10]}...] Triggered in guild {guild_id}")
                else:
                    print(f"❌ [{self.token[:10]}...] Failed in guild {guild_id}: {resp.status}")
                    print(await resp.text())
        except Exception as e:
            print(f"⚠️ Netzwerkfehler bei Bot [{self.token[:10]}...]: {e}")

    @tasks.loop(hours=2, minutes=1)
    async def bump_loop(self):
        await asyncio.sleep(random.randint(2, 8))
        
        for server in SERVERS:
            guild_id = server["guild_id"]
            channel_id = server["channel_id"]

            guild = self.get_guild(int(guild_id))
            if guild is None:
                print(f"⚠️ [{self.token[:10]}...] Überspringe: Account ist nicht auf Server {guild_id}")
                continue

            channel = guild.get_channel(int(channel_id))
            if channel is None:
                print(f"⚠️ [{self.token[:10]}...] Kanal {channel_id} auf Server '{guild.name}' nicht sichtbar!")
                continue

            print(f"🚀 [{self.token[:10]}...] Valide! Sende Interaktion für Server '{guild.name}'...")
            await self.trigger_command(guild_id, channel_id)
            
            await asyncio.sleep(random.randint(3, 7))

    @bump_loop.before_loop
    async def before_bump_loop(self):
        await self.wait_until_ready()
        await asyncio.sleep(10)

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
