from os import link
import discord
from discord.ext import commands
import youtube_dl
from youtubesearchpython import VideosSearch
import asyncio

song_queue = asyncio.Queue()
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
YDL_OPTIONS = {'format':"bestaudio"}

class music(commands.Cog):
  def __init__(self, client):
      self.client = client

  async def get_song(self, ctx, title):
    print(title)
    search_message = "<:Hmm:825811585116143616> Searching for " + title
    await ctx.send(search_message)

    video_search = VideosSearch(title, limit=1)
    url = video_search.result()['result'][0]['link']
    vid_title = video_search.result()['result'][0]['title']

    return url, vid_title

  async def create_source(self, ctx, url, title):
    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
      info = ydl.extract_info(url, download=False)
      url2 = info['formats'][0]['url']
      source = await discord.FFmpegOpusAudio.from_probe(url2,
      **FFMPEG_OPTIONS)
      if ctx.voice_client.is_playing() or song_queue.qsize() > 0:
        message = '<a:catJAM:830304947781632010> Added `' + title + '` to the queue at position ' + str(song_queue.qsize()) + '<a:catJAM:830304947781632010>'
      else:
        message = '<a:catJAM:830304947781632010> Now Playing `' + title + '`<a:catJAM:830304947781632010>'
      await ctx.send(message)

    return source
  
  async def manage_queue(self, vc):
    while vc.is_playing(): #Checks if song is playing
      await asyncio.sleep(15) #While it's playing it sleeps for 30 seconds
      print('waiting...')
    else:
      if song_queue.qsize() > 0:
        print('I see something in the queue, playing it now')
        source = song_queue.get_nowait()
        vc.play(source)
      await asyncio.sleep(10)
      while vc.is_playing(): #and checks once again if the bot is not playing
        break #if it's playing it breaks
      else:
        await vc.disconnect() #if not it disconnects

  @commands.command()
  async def play(self, ctx, *args):
    print('play invoked')
    voice_channel = ctx.author.voice.channel

    ## Checks to see if person who issued command is in a voice channel
    if ctx.author.voice is None:
      await ctx.send("You need to be in a channel to use this command")
      return ## returns because caller does not have permission to call the bot
    ## Checks to see if bot is already in a voice client
    if ctx.voice_client is None:
      await voice_channel.connect()

    vc = ctx.voice_client
    title = (' ').join(args)
    ## Search youtube using provided arguements, and then return a url and title for video
    vid_info = await self.get_song(ctx, title)
    ## Extract audio from video as playable format
    audio_source = await self.create_source(ctx, vid_info[0], vid_info[1])

    ## If the queue of songs is empty, there's no reason to start it because it'll instantly pop the only song
    ## So the song is just directly played
    if song_queue.empty():
      if not vc.is_playing():
        print('Nothing currently playing, playing song with no queue')
        vc.play(audio_source)
      else: 
        ## If the queue is empty but there's a song playing, the queue is started
        print('Song playing detected. Starting queue')
        song_queue.put_nowait(audio_source)
    else:
      ## queue not empty means a song is already queued up and it should be added
      print('Added song to queue')
      song_queue.put_nowait(audio_source)

    if song_queue.qsize() > 0:
      print('there\'s something in the queue... time to manage')
      await self.manage_queue(vc)
    else:
      print('queue is empty, not going to manage')
      return

    ##while vc.is_playing(): #Checks if song is playing
    ##  await asyncio.sleep(15) #While it's playing it sleeps for 30 seconds
    ##else:
    ##  await asyncio.sleep(15)
    ##  while vc.is_playing(): #and checks once again if the bot is not playing
    ##    break #if it's playing it breaks
    ##  else:
    ##    await vc.disconnect() #if not it disconnects
      
  @commands.command()
  async def leave(self, ctx):
    ctx.voice_client.stop()
    await ctx.voice_client.disconnect()

  @commands.command()
  async def stop(self, ctx):
    ctx.voice_client.stop()

  @commands.command()
  async def skip(self, ctx):
    ## If there's something in the queue, then it'll be played
    if not song_queue.empty():
      ctx.voice_client.stop()
      source = song_queue.get_nowait()
      ctx.voice_client.play(source)
      await ctx.send("Skipping...")
      ## Back to managing queue
      await self.manage_queue(ctx.voice_client)
    else:
      await ctx.send("There's nothing in the queue, I'll stop playing the song <:Sadge:760052673713537034>")
      ctx.voice_client.stop()

def setup(client):
  client.add_cog(music(client))