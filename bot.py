import os
import json
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_TOKEN not found in environment variables")

DATA_FILE = "reward_data.json"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ------------------ UTILITIES ------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def normalize(text):
    return text.replace(" ", "").lower()

# ------------------ EVENTS ------------------

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# ------------------ COMMANDS ------------------

@bot.command()
@commands.has_permissions(administrator=True)
async def reward(ctx, count: int, *members: discord.Member):
    guild = ctx.guild
    data = load_data()

    # Find role "reward members" (case & space insensitive)
    reward_role = None
    for role in guild.roles:
        if normalize(role.name) == "rewardmembers":
            reward_role = role
            break

    if not reward_role:
        await ctx.send("❌ Role `reward members` not found.")
        return

    role_members = set(reward_role.members)
    eligible = [m for m in members if m in role_members]

    if not eligible:
        await ctx.send("❌ No eligible members from `reward members` role.")
        return

    # Initialize data
    for m in role_members:
        data.setdefault(str(m.id), 0)

    # Sort by least rewards first
    eligible.sort(key=lambda m: data.get(str(m.id), 0))

    selected = eligible[:count]

    if not selected:
        await ctx.send("❌ No members selected.")
        return

    # Update counts
    for m in selected:
        data[str(m.id)] += 1

    save_data(data)

    msg = "**🏆 Reward Winners:**\n"
    for m in selected:
        msg += f"- {m.mention} (total: {data[str(m.id)]})\n"

    await ctx.send(msg)

@bot.command()
async def rewardstats(ctx):
    data = load_data()
    if not data:
        await ctx.send("No reward data found.")
        return

    lines = ["**📊 Reward Stats:**"]
    for uid, count in sorted(data.items(), key=lambda x: x[1], reverse=True):
        member = ctx.guild.get_member(int(uid))
        if member:
            lines.append(f"{member.display_name}: {count}")

    await ctx.send("\n".join(lines))

@bot.command()
@commands.has_permissions(administrator=True)
async def rewardreset(ctx):
    save_data({})
    await ctx.send("🔄 Reward data reset successfully.")

# ------------------ RUN ------------------

bot.run(TOKEN)
