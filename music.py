from os import link
import discord
from discord.ext import commands
import youtube_dl
from youtubesearchpython import VideosSearch
import asyncio

song_queue = asyncio.Queue()

class music(commands.Cog):
  def __init__(self, client):
      self.client = client

  @commands.command()
  async def play(self, ctx, *args):
    print('play invoked')
    if ctx.author.voice is None:
      await ctx.send("You need to be in a channel to use this command")
    voice_channel = ctx.author.voice.channel
    if ctx.voice_client is None:
      await voice_channel.connect()
      FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
      YDL_OPTIONS = {'format':"bestaudio"}
      vc = ctx.voice_client

      ytsearch = (' ').join(args)
      print(ytsearch)
      search_message = "<:Hmm:825811585116143616> Searching for " + ytsearch
      await ctx.send(search_message)

      video_search = VideosSearch(ytsearch, limit=1)
      url = video_search.result()['result'][0]['link']


      with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=False)
        url2 = info['formats'][0]['url']
        source = await discord.FFmpegOpusAudio.from_probe(url2,
        **FFMPEG_OPTIONS)

        vc.play(source)
        message = '<a:catJAM:830304947781632010> Now Playing **' + video_search.result()['result'][0]['title'] + '** <a:catJAM:830304947781632010>'
        await ctx.send(message)

      while vc.is_playing(): #Checks if song is playing
        await asyncio.sleep(15) #While it's playing it sleeps for 30 seconds
      else:
        await asyncio.sleep(15)
        while vc.is_playing(): #and checks once again if the bot is not playing
          break #if it's playing it breaks
        else:
          await vc.disconnect() #if not it disconnects
      
    
  @commands.command()
  async def leave(self, ctx):
    ctx.voice_client.stop()
    await ctx.voice_client.disconnect()

def setup(client):
  client.add_cog(music(client))