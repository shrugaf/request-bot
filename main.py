import os
from flask import Flask, request
from threading import Thread
import discord
from discord.ext import commands
from datetime import datetime
import asyncio

# Load token from environment variable
TOKEN = os.getenv("DISCORD_TOKEN")

# Discord bot constants
GUILD_ID = 1393376630684254359
REQUEST_CHANNEL_ID = 1394073906708742236
TARGET_MESSAGE_ID = 1394074089320218624
TRIGGER_EMOJI = "📩"

# Flask web server for keepalive
app = Flask(__name__)

@app.route("/")
def home():
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    # Get IP from X-Forwarded-For if behind proxy (Render), otherwise remote_addr
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    print(f"✅ Ping received at {now} UTC from {ip}", flush=True)
    return "✅ I'm alive!", 200

@app.route("/favicon.ico")
def favicon():
    return "", 204

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    thread = Thread(target=run_flask)
    thread.daemon = True
    thread.start()

# Discord bot setup
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

    if user is None or user.bot:
        return

    try:
        prompt = await channel.send(f"{user.mention}, please type your request now:")

        def check(msg):
            return msg.author == user and msg.channel.id == channel.id

        msg = await bot.wait_for("message", check=check, timeout=60)

        embed = discord.Embed(
            title="New Request",
            description=msg.content,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"From: {user.display_name} ({user})")

        request_channel = bot.get_channel(REQUEST_CHANNEL_ID)
        await request_channel.send(embed=embed)

        await msg.delete()
        await prompt.delete()

        await channel.send(f"✅ {user.mention}, your request has been submitted.")

    except asyncio.TimeoutError:
        try:
            await prompt.delete()
        except:
            pass
        await channel.send(f"⚠️ {user.mention}, request timed out. Please try again.")
    except Exception as e:
        print(f"⚠️ Error: {e}", flush=True)
        await channel.send(f"⚠️ {user.mention}, something went wrong.")

# Start Flask and bot
keep_alive()
bot.run(TOKEN)
