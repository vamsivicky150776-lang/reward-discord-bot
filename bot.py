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
    return text.lower().replace(" ", "")

def get_reward_role(guild):
    for role in guild.roles:
        if normalize(role.name) == normalize(ROLE_NAME):
            return role
    return None

# ---------------- BOT READY ----------------

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user}")

# ---------------- MENU VIEW ----------------

class MenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="🎁 Give Rewards", style=discord.ButtonStyle.primary)
    async def give_rewards(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("How many rewards do you want to give?", ephemeral=True)

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        msg = await bot.wait_for("message", check=check)
        try:
            count = int(msg.content)
        except:
            await interaction.followup.send("Invalid number.", ephemeral=True)
            return

        await interaction.followup.send("Mention eligible members:", ephemeral=True)
        msg2 = await bot.wait_for("message", check=check)

        role = get_reward_role(interaction.guild)
        if not role:
            await interaction.followup.send("`reward members` role not found.", ephemeral=True)
            return

        role_members = {m.id for m in role.members}
        mentioned = [m for m in msg2.mentions if m.id in role_members]

        if not mentioned:
            await interaction.followup.send("No valid members mentioned.", ephemeral=True)
            return

        for m in mentioned:
            reward_data.setdefault(str(m.id), 0)

        mentioned.sort(key=lambda m: reward_data[str(m.id)])
        selected = mentioned[:count]

        if not selected:
            await interaction.followup.send("No users selected.", ephemeral=True)
            return

        winners_text = "\n".join(
            f"- {m.mention} (received {reward_data[str(m.id)]} times)"
            for m in selected
        )

        confirm_view = ConfirmView(selected)
        await interaction.followup.send(
            f"🎯 **Suggested Winners:**\n{winners_text}",
            view=confirm_view,
            ephemeral=False
        )

    @discord.ui.button(label="📊 View Stats", style=discord.ButtonStyle.secondary)
    async def view_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = get_reward_role(interaction.guild)
        if not role:
            await interaction.response.send_message("`reward members` role not found.", ephemeral=True)
            return

        stats_text = ""
        for m in role.members:
            count = reward_data.get(str(m.id), 0)
            stats_text += f"{m.display_name}: {count}\n"

        await interaction.response.send_message(f"📊 **Reward Stats:**\n{stats_text}", ephemeral=True)

# ---------------- CONFIRM VIEW ----------------

class ConfirmView(discord.ui.View):
    def __init__(self, winners):
        super().__init__(timeout=300)
        self.winners = winners

    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        for m in self.winners:
            reward_data[str(m.id)] += 1

        save_data(reward_data)
        await interaction.response.send_message("✅ Rewards confirmed and saved.")
        self.stop()

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("❌ Reward process cancelled.")
        self.stop()

# ---------------- SLASH COMMAND ----------------

@tree.command(name="start", description="Open reward system menu")
async def start(interaction: discord.Interaction):
    view = MenuView()
    await interaction.response.send_message("🎮 **Reward System Menu**", view=view)

bot.run(TOKEN)
