from dotenv import load_dotenv, find_dotenv
import os
import discord
from discord.ext import commands
import youtube_dl
from youtubesearchpython import VideosSearch
import asyncio
import spotify_fetch
from random import shuffle as shuffle_queue

load_dotenv(find_dotenv())
song_queue = asyncio.Queue()
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
YDL_OPTIONS = {'format':"bestaudio"}

class music(commands.Cog):
  def __init__(self, client):
      self.client = client

  async def get_song(self, ctx, title):
    print(title)

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
        message = '<a:catJAM:830304947781632010> Added `' + title + '` to the queue at position ' + str(song_queue.qsize()) + ' <a:catJAM:830304947781632010>'
      else:
        message = '<a:catJAM:830304947781632010> Now Playing `' + title + '`<a:catJAM:830304947781632010>'
      await ctx.send(message)

    return source
  
  async def manage_queue(self, vc):
    while vc.is_playing(): #Checks if song is playing
      await asyncio.sleep(5) #While it's playing it sleeps for 5 seconds
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
  
  async def fill_queue(self, ctx, playlist_content):
    if len(playlist_content) == 1:
      title = playlist_content[0]
      print(f"{title}\n")
      song_info = await self.get_song(ctx, title)
      with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(song_info[0], download=False)
        url2 = info['formats'][0]['url']
        source = asyncio.create_task(discord.FFmpegOpusAudio.from_probe(url2,
        **FFMPEG_OPTIONS))
      song_queue.put_nowait(source)
    else:
      mid = len(playlist_content) // 2
      first_half = playlist_content[:mid]
      second_half = playlist_content[mid:]

      await asyncio.gather(
        self.fill_queue(ctx, first_half),
        self.fill_queue(ctx, second_half)
      )
      
      
  @commands.command()
  async def spotify(self, ctx, args): #change args to *args if creating playlist finder
    print('spotify playlist reader invoked')
    voice_channel = ctx.author.voice.channel

    ## Checks to see if person who issued command is in a voice channel
    if ctx.author.voice is None:
      await ctx.send("You need to be in a channel to use this command")
      return ## returns because caller does not have permission to call the bot
    ## Checks to see if bot is already in a voice client
    if ctx.voice_client is None:
      await voice_channel.connect()

    vc = ctx.voice_client

    auth_token = spotify_fetch.get_auth_token(os.getenv('CLIENT_ID'), os.getenv('CLIENT_SECRET'), spotify_fetch.api_url, os.getenv('refresh_token'))
    playlist_content = spotify_fetch.get_playlist_items(auth_token, args)

    await ctx.send("<a:catJAM:830304947781632010> Playlist found adding songs to queue now <a:catJAM:830304947781632010>")

    if len(playlist_content) > 20 and len(playlist_content) <= 50:
      message = "Downloading songs... May take a little while"
    elif len(playlist_content) > 50:
      message = "why this playlist so long its gonna take 20 years to download all of this"
    elif len(playlist_content) <= 20:
      message = "Downloading songs... Will take a minute."
    await ctx.send(message)

    if not vc.is_playing():
        print('Nothing currently playing, playing song and making queue')
        first_song = playlist_content.pop(0)
        song_info = await self.get_song(ctx, first_song)
        audio_source = await self.create_source(ctx, song_info[0], song_info[1])
        vc.play(audio_source)

    await asyncio.gather(
      self.fill_queue(ctx, playlist_content)
    )
    await ctx.send(f"The queue has been filled with { song_queue.qsize() } songs")
    
    await self.manage_queue(vc)
    

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
    ## Search youtube using provided arguements, and then return a url and title for video\
    search_message = "<:Hmm:825811585116143616> Searching for " + title
    await ctx.send(search_message)
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
      
  @commands.command()
  async def shuffle(self, ctx):
    shuffle_queue(song_queue._queue)
    print("queue shuffled")
    await ctx.send("Shuffled the queue")


  #Needs work, issue with removing using the supplied arguement. May need to split
  @commands.command()
  async def remove(self, ctx, arg):
    response = song_queue.get_nowait(arg)
    print(arg)
    if response != None:
      await ctx.send(f"Removed song at position {arg} from the queue")
    else:
      await ctx.send(f"Nothing to remove at position {arg}")

  @commands.command()
  async def leave(self, ctx):
    while song_queue.qsize() > 0:
      song_queue.get_nowait()
    ctx.voice_client.stop()
    await ctx.voice_client.disconnect()

  @commands.command()
  async def stop(self, ctx):
    while song_queue.qsize() > 0:
      song_queue.get_nowait()
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