import discord
from discord.ext import commands
import music

cogs=[music]
intents = discord.Intents().all()
client = commands.Bot(command_prefix='!', intents=intents)

for i in range(len(cogs)):
  cogs[i].setup(client)



client.run('NTIyMjcyMTIxOTE3OTMxNTIy.XBCR0Q.cYCelMtWkAYXZcjGg2xWaj_U6A4')
