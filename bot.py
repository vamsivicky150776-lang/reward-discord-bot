import os
import json
import discord
from discord.ext import commands

DATA_FILE = "rewards.json"
ROLE_NAME = "reward members"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ------------------ STORAGE ------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

reward_data = load_data()
last_suggestion = []

# ------------------ EVENTS ------------------

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# ------------------ HELPERS ------------------

def normalize(text):
    return text.lower().replace(" ", "")

def get_reward_role(guild):
    for role in guild.roles:
        if normalize(role.name) == normalize(ROLE_NAME):
            return role
    return None

# ------------------ COMMANDS ------------------

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong! Bot is online.")

@bot.command()
async def suggest(ctx, count: int, *members: discord.Member):
    global last_suggestion

    role = get_reward_role(ctx.guild)
    if not role:
        await ctx.send("❌ `reward members` role not found.")
        return

    role_members = {m.id for m in role.members}
    eligible = [m for m in members if m.id in role_members]

    if not eligible:
        await ctx.send("❌ No mentioned users are in `reward members` role.")
        return

    for m in eligible:
        reward_data.setdefault(str(m.id), 0)

    eligible.sort(key=lambda m: reward_data[str(m.id)])

    selected = eligible[:count]
    last_suggestion = selected

    if not selected:
        await ctx.send("❌ No users to suggest.")
        return

    msg = "🎯 **Suggested Reward Winners:**\n"
    for m in selected:
        msg += f"- {m.mention} (received {reward_data[str(m.id)]} times)\n"

    msg += "\nType `!confirm` to finalize."
    await ctx.send(msg)

@bot.command()
async def confirm(ctx):
    global last_suggestion

    if not last_suggestion:
        await ctx.send("❌ No suggestion to confirm.")
        return

    for m in last_suggestion:
        reward_data[str(m.id)] += 1

    save_data(reward_data)
    last_suggestion = []

    await ctx.send("✅ Rewards confirmed and saved.")

@bot.command()
async def stats(ctx):
    role = get_reward_role(ctx.guild)
    if not role:
        await ctx.send("❌ `reward members` role not found.")
        return

    msg = "📊 **Reward Stats:**\n"
    for m in role.members:
        count = reward_data.get(str(m.id), 0)
        msg += f"- {m.display_name}: {count}\n"

    await ctx.send(msg)

# ------------------ START ------------------

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN missing")

bot.run(TOKEN)
