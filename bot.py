import os
import json
import discord
from discord.ext import commands
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN missing")

DATA_FILE = "rewards.json"
ROLE_NAME = "reward members"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ---------------- STORAGE ----------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

reward_data = load_data()

def normalize(text):
    return text.lower().strip()

def get_reward_role(guild):
    for role in guild.roles:
        if normalize(role.name) == normalize(ROLE_NAME):
            return role
    return None

# ---------------- READY ----------------

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user}")

# ---------------- MENU ----------------

class MenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="🎁 Give Rewards", style=discord.ButtonStyle.primary)
    async def give_rewards(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Feature already working. Use existing flow.")

    @discord.ui.button(label="📊 View Stats", style=discord.ButtonStyle.secondary)
    async def view_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = get_reward_role(interaction.guild)
        if not role:
            await interaction.response.send_message("❌ `reward members` role not found.")
            return

        stats_text = ""
        for m in role.members:
            count = reward_data.get(str(m.id), 0)
            stats_text += f"{m.display_name}: {count}\n"

        await interaction.response.send_message(f"📊 **Reward Stats:**\n{stats_text}")

    @discord.ui.button(label="📥 Import Old Stats", style=discord.ButtonStyle.success)
    async def import_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("📥 Paste the old Reward Stats message now:")

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        msg = await bot.wait_for("message", check=check)
        lines = msg.content.split("\n")

        role = get_reward_role(interaction.guild)
        if not role:
            await interaction.followup.send("❌ `reward members` role not found.")
            return

        updated = 0

        for line in lines:
            if ":" in line:
                parts = line.split(":")
                name = parts[0].strip()
                try:
                    count = int(parts[1].strip())
                except:
                    continue

                for member in role.members:
                    if member.display_name.strip() == name:
                        reward_data[str(member.id)] = count
                        updated += 1
                        break

        save_data(reward_data)
        await interaction.followup.send(f"✅ Imported stats for {updated} members.")

    @discord.ui.button(label="🔄 Reset All Data", style=discord.ButtonStyle.danger)
    async def reset_data(self, interaction: discord.Interaction, button: discord.ui.Button):
        reward_data.clear()
        save_data(reward_data)
        await interaction.response.send_message("🔄 All reward data has been reset.")

# ---------------- SLASH COMMAND ----------------

@tree.command(name="start", description="Open reward system menu")
async def start(interaction: discord.Interaction):
    view = MenuView()
    await interaction.response.send_message("🎮 **Reward System Menu**", view=view)

bot.run(TOKEN)
