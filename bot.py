import os
import discord
from discord.ext import commands
import json
import time

TOKEN = os.getenv("BOT_TOKEN")
ROLE_NAME = "reward members"  # case-insensitive
DATA_FILE = "data.json"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

def normalize(name):
    return " ".join(name.lower().split())

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_role(guild):
    for role in guild.roles:
        if normalize(role.name) == normalize(ROLE_NAME):
            return role
    return None

@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")

@bot.command()
async def suggest(ctx, count: int):
    role = get_role(ctx.guild)
    if not role:
        await ctx.send("❌ Role 'Reward Members' not found.")
        return

    members = role.members
    if not members:
        await ctx.send("❌ No members in Reward Members role.")
        return

    data = load_data()

    for m in members:
        if str(m.id) not in data:
            data[str(m.id)] = {"name": m.name, "total": 0, "last": 0}

    ordered = sorted(
        members,
        key=lambda m: (data[str(m.id)]["total"], data[str(m.id)]["last"])
    )

    chosen = ordered[:count]
    msg = f"🎁 **Suggested {count} Reward Recipients**\n\n"
    for i, m in enumerate(chosen, 1):
        info = data[str(m.id)]
        msg += f"{i}. {m.mention} — {info['total']} rewards\n"

    save_data(data)
    await ctx.send(msg)

@bot.command()
async def confirm(ctx, *users: discord.Member):
    data = load_data()
    now = int(time.time())

    for u in users:
        uid = str(u.id)
        if uid not in data:
            data[uid] = {"name": u.name, "total": 0, "last": 0}
        data[uid]["total"] += 1
        data[uid]["last"] = now

    save_data(data)
    await ctx.send("✅ Rewards recorded successfully.")

bot.run(TOKEN)
