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

def make_bot(token):
    bot = commands.Bot(command_prefix="$", self_bot=True)
    session_id = "".join(random.choice('0123456789abcdef') for _ in range(32))

    async def trigger_command(guild_id, channel_id):
        headers = {
            'Authorization': token,
            'Content-Type': 'application/json',
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "Referer": f"https://discord.com{guild_id}/{channel_id}",
        }
        payload = {
            "type": 2,
            "application_id": application_id,
            "guild_id": guild_id,
            "channel_id": channel_id,
            "session_id": session_id,
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
                        print(f"✅ [{token[:10]}...] Triggered in guild {guild_id}")
                    else:
                        print(f"❌ [{token[:10]}...] Failed in guild {guild_id}: {resp.status}")
        except Exception:
            pass

    async def start_working_loop():
        # Warte kurz, damit Discord Zeit hat, die Session komplett aufzubauen
        await asyncio.sleep(5)
        
        while True:
            print(f"🔄 Starte neuen Bump-Durchgang für [{token[:10]}...]")
            for server in servers:
                await trigger_command(server["guild_id"], server["channel_id"])
                await asyncio.sleep(30)  # Die gewünschte 30-Sekunden-Pause nach jedem Command
            
            print("⏳ Durchgang beendet. Warte 2 Stunden und 1 Minute bis zum nächsten Mal...")
            await asyncio.sleep(7260)  # Exakt 2 Stunden und 1 Minute Pause vor der nächsten Runde

    @bot.event
    async def on_ready():
        print(f"👤 {bot.user} ist online.")
        # Startet die unendliche Schleife im Hintergrund, sobald der Bot bereit ist
        bot.loop.create_task(start_working_loop())

    return bot

async def main():
    bots = [make_bot(token) for token in TOKENS]
    await asyncio.gather(*[bot.start(token) for bot, token in zip(bots, TOKENS)])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Skript manuell beendet.")
