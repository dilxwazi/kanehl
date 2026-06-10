import random
import json
import aiohttp
import asyncio
from discord.ext import commands, tasks

# Load config
with open("config.json") as f:
    config = json.load(f)

TOKEN = config["token"]
application_id = config["application_id"]
command_id = config["command_id"]
command_name = config["command_name"]
version = config["version"]
guild_id = config["guild_id"]
channel_id = config["channel_id"]

# Self-bot setup
bot = commands.Bot(command_prefix="$", self_bot=True)
session_id = "".join(random.choice('0123456789abcdef') for _ in range(32))

async def trigger_command():
    headers = {
        'Authorization': TOKEN, 
        'Content-Type': 'application/json',
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "Referer": f"https://discord.com/channels/{guild_id}/{channel_id}",
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
        async with session.post("https://discord.com/api/v9/interactions", headers=headers, json=payload) as resp:
            if resp.status == 204:
                print("✅ Successfully triggered slash command.")
            else:
                print(f"❌ Failed with status {resp.status}")
                print(await resp.text())

@bot.event
async def on_ready():
    print(f"{bot.user} is now online.")
    repeat.start()

@bot.command()
async def start(ctx):
    repeat.start()
    await ctx.send("✅ Bump task started.")

@bot.command()
async def stop(ctx):
    repeat.stop()
    await ctx.send("🛑 Bump task stopped.")

@tasks.loop(hours=2)
async def repeat():
    await trigger_command()

bot.run(TOKEN)
