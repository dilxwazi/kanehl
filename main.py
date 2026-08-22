import random
import json
import aiohttp
import asyncio
import logging
from discord.ext import commands, tasks

logging.getLogger('discord.state').setLevel(logging.ERROR)

with open("config.json") as f:
    config = json.load(f)

TOKENS = config["tokens"]
application_id = config["application_id"]
command_id = config["command_id"]
command_name = config["command_name"]
version = config["version"]
servers = config["servers"]

# Das Lock sorgt dafür, dass die Bots nacheinander drankommen
loop_lock = asyncio.Lock()

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
        async with aiohttp.ClientSession() as session:
            async with session.post("https://discord.com", headers=headers, json=payload) as resp:
                if resp.status == 204:
                    print(f"✅ [{token[:10]}...] Triggered in guild {guild_id}")
                else:
                    print(f"❌ [{token[:10]}...] Failed in guild {guild_id}: {resp.status}")
                    print(await resp.text())

    @bot.event
    async def on_ready():
        print(f"{bot.user} is now online.")
        if not repeat.is_running():
            repeat.start()

    @bot.command()
    async def start(ctx):
        if not repeat.is_running():
            repeat.start()
        await ctx.send("✅ Bump task started.")

    @bot.command()
    async def stop(ctx):
        repeat.stop()
        await ctx.send("🛑 Bump task stopped.")

    @tasks.loop(hours=2, minutes=1)
    async def repeat():
        # Blockiert andere Bots, bis dieser Bot komplett fertig ist
        async with loop_lock:
            for server in servers:
                await trigger_command(server["guild_id"], server["channel_id"])
                await asyncio.sleep(1) 
            
            # Warte exakt 10 Sekunden, bevor das Lock für den nächsten Bot freigegeben wird
            print(f"⏳ [{token[:10]}...] Fertig. Warte 10 Sekunden vor dem nächsten Token...")
            await asyncio.sleep(10)

    return bot

async def main():
    bots = [make_bot(token) for token in TOKENS]
    await asyncio.gather(*[bot.start(token) for bot, token in zip(bots, TOKENS)])

if __name__ == "__main__":
    asyncio.run(main())
