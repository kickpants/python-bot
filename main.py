import discord
from discord.ext import commands
import music
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

cogs=[music]
intents = discord.Intents().all()
client = commands.Bot(command_prefix='!', intents=intents)

for i in range(len(cogs)):
  cogs[i].setup(client)

client.run(os.getenv('TOKEN'))
