import os
import discord
from discord.ext import commands

# ----- INTENTS -----
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# ----- BOT SETUP -----
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong! Bot is online.")

# ----- START BOT -----
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN environment variable is missing")

bot.run(TOKEN)
