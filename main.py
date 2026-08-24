import random
import json
import aiohttp
import asyncio
import logging
from discord.ext import commands

logging.getLogger('discord.state').setLevel(logging.ERROR)

with open("config.json") as f:
    config = json.load(f)

TOKENS = config["tokens"]
application_id = config["application_id"]
command_id = config["command_id"]
command_name = config["command_name"]
version = config["version"]
servers = config["servers"]

class SimpleBot(commands.Bot):
    def __init__(self, token, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = token
        self.session_id = "".join(random.choice('0123456789abcdef') for _ in range(32))
        self.joined_guilds = set()

    async def fetch_joined_guilds(self):
        headers = {'Authorization': self.token}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://discord.com", headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.joined_guilds = {str(g["id"]) for g in data}
        except Exception as e:
            print(f"⚠️ Fehler beim Laden der Serverliste für [{self.token[:10]}...]: {e}")

    async def trigger_command(self, guild_id, channel_id):
        headers = {
            'Authorization': self.token,
            'Content-Type': 'application/json',
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "Referer": f"https://discord.com{guild_id}/{channel_id}",
        }
        payload = {
            "type": 2,
            "application_id": application_id,
            "guild_id": guild_id,
            "channel_id": channel_id,
            "session_id": self.session_id,
            "data": {
                "version": version,
                "id": command_id,
                "name": command_name,
                "type": 1,
                "options": []
            }
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post("https://discord.com", headers=headers, json=payload) as resp:
                    if resp.status == 204:
                        print(f"✅ [{self.token[:10]}...] Triggered in guild {guild_id}")
                    else:
                        print(f"❌ [{self.token[:10]}...] Failed in guild {guild_id}: {resp.status}")
                        print(await resp.text())
        except Exception as e:
            print(f"⚠️ Netzwerkfehler bei Bot [{self.token[:10]}...]: {e}")

    async def on_ready(self):
        print(f"👤 {self.user} ist online.")

async def run_bump_cycle(bots):
    print("🔄 Starte neuen Bump-Durchgang für alle Bots...")
    for bot in bots:
        await bot.fetch_joined_guilds()
        
        for server in servers:
            g_id = str(server["guild_id"])
            c_id = str(server["channel_id"])
            
            if g_id not in bot.joined_guilds:
                print(f"⚠️ [{bot.token[:10]}...] Überspringe: Token ist nicht auf Server {g_id}")
                continue

            await bot.trigger_command(g_id, c_id)
            await asyncio.sleep(30)
    print("⏳ Durchgang beendet. Warte 2 Stunden und 1 Minute bis zum nächsten Mal...")

async def main():
    bots = []
    for token in TOKENS:
        bot = SimpleBot(token=token, command_prefix="$", self_bot=True)
        bots.append(bot)
        asyncio.create_task(bot.start(token))

    await asyncio.sleep(5)

    while True:
        await run_bump_cycle(bots)
        await asyncio.sleep(7260)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Skript manuell beendet.")
