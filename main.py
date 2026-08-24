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
                    if resp.status in [200, 204]:
                        print(f"✅ [{self.token[:10]}...] Triggered in guild {guild_id}")
                    else:
                        print(f"❌ [{self.token[:10]}...] Failed in guild {guild_id}: {resp.status}")
        except Exception:
            pass

    async def start_working_loop(self):
        # Gibt dem Bot etwas Zeit, um nach dem Login die Serverliste zu laden
        await asyncio.sleep(15)
        
        while True:
            print(f"🔄 Starte neuen Bump-Durchgang für [{self.token[:10]}...]")
            
            # Holt die IDs der Server, auf denen der Bot aktuell wirklich online ist
            joined_guild_ids = {str(guild.id) for guild in self.guilds}
            
            for server in servers:
                g_id = str(server["guild_id"])
                c_id = str(server["channel_id"])
                
                # Wenn der Bot nicht auf dem Server ist, überspringt er ihn ohne Wartezeit
                if g_id not in joined_guild_ids:
                    print(f"⚠️ [{self.token[:10]}...] Überspringe: Token ist nicht auf Server {g_id}")
                    continue

                await self.trigger_command(g_id, c_id)
                await asyncio.sleep(30)
            
            print("⏳ Durchgang beendet. Warte 2 Stunden und 1 Minute bis zum nächsten Mal...")
            await asyncio.sleep(7260)

    async def on_ready(self):
        print(f"👤 {self.user} ist online.")
        self.loop.create_task(self.start_working_loop())

def make_bot(token):
    return SimpleBot(token=token, command_prefix="$", self_bot=True)

async def main():
    bots = [make_bot(token) for token in TOKENS]
    await asyncio.gather(*[bot.start(token) for bot, token in zip(bots, TOKENS)])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Skript manuell beendet.")
