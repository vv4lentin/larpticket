import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import asyncio
from keep_alive import keep_alive

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

# Bot setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=",", intents=intents)

# List of cogs to load
COGS = ["ticket"]

# Load cogs on startup
async def load_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(f"cogs.{cog}")
            print(f"✅ Loaded {cog}.py")
        except Exception as e:
            print(f"❌ Failed to load {cog}.py: {e}")

@bot.event
async def on_ready():
    print(f"\n🤖 Bot is online as {bot.user}")
    print(f"✅ Connected to {len(bot.guilds)} servers!")
    print(f"📌 Prefix: {bot.command_prefix}\n")
    await bot.tree.sync()  # Sync slash commands globally
    print("🌐 Slash commands synced.")

# Run the bot
keep_alive()
async def main():
    async with bot:
        await load_cogs()
        await bot.start(token=token)

asyncio.run(main())
