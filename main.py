from flask import Flask
from threading import Thread
import discord
from discord.ext import commands
import os

TOKEN = os.getenv("DISCORD_TOKEN")

# 🔧 YOUR REAL DISCORD IDs
GUILD_ID = 1393376630684254359
REQUEST_CHANNEL_ID = 1394073906708742236
TARGET_MESSAGE_ID = 1394074089320218624
TRIGGER_EMOJI = "📩"

# Flask app to keep the bot alive
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ I'm alive!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run_flask).start()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}!")

@bot.event
async def on_raw_reaction_add(payload):
    if payload.message_id != TARGET_MESSAGE_ID or str(payload.emoji) != TRIGGER_EMOJI:
        return

    guild = bot.get_guild(GUILD_ID)
    channel = bot.get_channel(payload.channel_id)
    user = guild.get_member(payload.user_id)

    if user.bot:
        return

    prompt = await channel.send(f"{user.mention}, please type your request now:")

    def check(msg):
        return msg.author == user and msg.channel.id == channel.id

    try:
        msg = await bot.wait_for('message', check=check, timeout=60)

        request_channel = bot.get_channel(REQUEST_CHANNEL_ID)
        embed = discord.Embed(
            title="New Request",
            description=msg.content,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"From: {user.display_name} ({user})")
        await request_channel.send(embed=embed)

        await msg.delete()
        await prompt.delete()
        await channel.send(f"✅ {user.mention}, your request has been submitted.")

    except Exception as e:
        await prompt.delete()
        await channel.send(f"⚠️ {user.mention}, request timed out or something went wrong.")
        print(f"Error: {e}")

keep_alive()
bot.run(TOKEN)
