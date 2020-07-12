import discord
from discord.ext import commands
from discord.utils import get
import random
import os
import config as cfg
import aiohttp
import io
import asyncio
import youtube_dl

prefix = cfg.Prefix
bot = discord.Client()
bot = commands.Bot(command_prefix=prefix)
gVol = cfg.DefaultVolume
gPlaylist = []

@bot.event
async def on_ready():
    print("At your service! Bot is online now.")

class randoms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command()
    async def roll(self, ctx, roll : str):
        ''' Rolls a dice using #d# format. e.g !roll 3d6 or !roll 3d6+5 '''
        resultTotal = 0
        resultString = ''
        mod = ''
        nmod = 0
        try:
            try:
                numDice = roll.split('d')[0]
                diceVal = roll.split('d')[1]
                if '+' in diceVal:
                    try:
                        mod = int(diceVal.split('+')[1])
                        nmod = int(mod)
                        diceVal = diceVal.split('+')[0]
                    except Exception as e:
                        print(e)
                        await ctx.send('Format has to be in #d#+# or d#+#.')
                        return
                if '-' in diceVal:
                    try:
                        mod = diceVal.split('-')[1]
                        nmod = -int(mod)
                        diceVal = diceVal.split('-')[0]
                    except Exception as e:
                        print(e)
                        await ctx.send('Format has to be in #d#-# or d#-#.')
                        return
            except Exception as e:
                print(e)
                await ctx.send('Format has to be in #d# or d#.')
                return

            if numDice == '':
                numDice = '1'

            if int(numDice) > 500:
                await ctx.send("I can't roll that many dice.")
                return

            try:
                rolls = int(numDice)
                limit = int(diceVal)
            except Exception as e:
                print(e)
                await ctx.send('Format has to be in #d# or something like that.')
                return

            print('Start rolling')

            resultArray = []
            for r in range(rolls):
                number = random.randint(1, limit)
                resultArray.append(number)

            resultTotal = sum(resultArray)
            resultTotal += nmod
            resultArray.sort()
            resultString = str(resultArray).strip('[]')

            if (nmod > 0):
                mod = ' + ' + str(nmod)
            elif(nmod < 0):
                mod = str(nmod)
            else:
                mod = '0'

            if (numDice == '1') & (mod == '0'):
                await ctx.send("**Result:** " + resultString)
            else:
                await ctx.send("**Result:** " + resultString + "\n**Total" + mod + ":** " + str(resultTotal))

        except Exception as e:
            print(e)
            return

    @commands.command()
    async def d(self, ctx):
        ''' Rolls a d20 '''
        resultString = ''

        try:
            limit = 20

            number = random.randint(1, limit)

            resultString = str(number)

            await ctx.send("**Result:** " + resultString)

        except Exception as e:
            print(e)
            return

    @commands.command()
    async def flip(self, ctx, *args):
        ''' Flip a coin. Default sides are 'head' and 'tails'. '''
        if len(args) < 2:
            args = ['head', 'tails']

        res = random.choice(args)
        await ctx.send('The coin shows ' + res + '.')

bot.add_cog(randoms(bot))

def SameChannel (ctx):
    same = False
    author = ctx.message.author.voice.channel
    bot = ctx.voice_client.channel

    if (author == bot):
        same = True
    return same

class talking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command(aliases=['lonely','summon'])
    async def join(self, ctx):
        ''' Make the Bot join the voice_channel. Alias: lonely, summon '''
        try:
            channel = ctx.message.author.voice.channel
            await channel.connect()
        except Exception as e:
            print(e)

    @commands.command(aliases=['ffs','release'])
    async def leave(self, ctx):
        ''' Make the Bot leave the voice_channel. Alias: ffs, release '''
        try:
            await ctx.voice_client.disconnect()
        except Exception as e:
            print(e)

bot.add_cog(talking(bot))

def playit():
    try:
        if (len(gPlaylist)==0):
            raise Exception('Playlist empty')
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(gPlaylist[0]), gVol)
        bot.voice_clients[0].play(source, after = myafter)
        gPlaylist.pop(0)
    except Exception as e:
        print(e)

def myafter(error):
    try:
        fut = asyncio.run_coroutine_threadsafe(playit(), bot.loop)
        fut.result()
    except Exception as e:
        print(e)

class music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command()
    async def show(self, ctx, *args):
        ''' Shows content of a Folder (pass with "" in case of spaces) '''
        path = cfg.MusicPath
        if len(args) != 0:
            path = path + '/' + args[0]
        try:
            content = os.listdir(path)
            content.sort()
            content = str(content).strip('[]')
            await ctx.send('Found following stuff in the dir ' + path +':\n' + content)
        except Exception as e:
            await ctx.send('Did not find the folder you wanted to show the content.')

    @commands.command()
    async def play(self, ctx, *args):
        ''' Plays the specified local file or content of the folder. Plays shuffle if you give a second argument.'''
        global gPlaylist
        try:
            channel = ctx.message.author.voice.channel

            if ctx.voice_client is None:
                await channel.connect()

            if (SameChannel(ctx)==False):
                raise Exception('Not in the same channel.')

            path = cfg.MusicPath
            if len(args) != 0:
                path = path + '/' + args[0]

            if os.path.isdir(path):
                for root, directories, filenames in os.walk(path):
                    for filename in filenames:
                        if '.flac' in filename:
                            gPlaylist.append(os.path.join(root,filename))
                gPlaylist.sort()
            else:
                gPlaylist.append(path)

            if len(args) == 2:
                random.shuffle(gPlaylist)

            try:
                if not ctx.voice_client.is_playing():
                    source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(gPlaylist[0]), gVol)
                    ctx.voice_client.play(source, after = myafter)
                    await ctx.send('Now playing: {}'.format(gPlaylist[0][9:]))
                    gPlaylist.pop(0)

            except Exception as e:
                print(e)
        except Exception as e:
            print(e)

    @commands.command()
    async def yt(self, ctx, url: str):
        ''' Plays the specified youtube url.'''
        try:
            channel = ctx.message.author.voice.channel

            if ctx.voice_client is None:
                await channel.connect()

            if (SameChannel(ctx)==False):
                raise Exception('Not in the same channel.')
            try:
                if ctx.voice_client.is_playing():
                    ctx.voice_client.stop()

                song_there = os.path.isfile("song.mp3")
                try:
                    if song_there:
                        os.remove("song.mp3")
                except PermissionError:
                    await ctx.send("Wait for the current playing music end or use the 'stop' command")
                    return
                await ctx.send("Working on it.")
                print("Someone wants to play music let me get that ready for them...")

                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                }
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                for file in os.listdir("./"):
                    if file.endswith(".mp3"):
                        os.rename(file, 'song.mp3')
                source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio("song.mp3"), gVol)
                ctx.voice_client.play(source)

            except Exception as e:
                print(e)
        except Exception as e:
            print(e)

    @commands.command()
    async def jb(self, ctx, tracknr: str):
        ''' Plays the specified JBridge Soundfile (e.g. 1-15 for track 15 of CD 1 or 1-02 for track 2 of CD 1).'''
        try:
            channel = ctx.message.author.voice.channel

            if ctx.voice_client is None:
                await channel.connect()

            if (SameChannel(ctx)==False):
                raise Exception('Not in the same channel.')
            try:
                if ctx.voice_client.is_playing():
                    ctx.voice_client.stop()

                track = "../Japan/JBridge/" + tracknr + ".flac"

                source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(track), gVol)
                ctx.voice_client.play(source)

            except Exception as e:
                print(e)
        except Exception as e:
            print(e)

    @commands.command()
    async def mn(self, ctx, tracknr: str):
        ''' Plays the specified Mina no Nihongo Soundfile (e.g. 15 for track 15 or 02 for track 2 ).'''
        try:
            channel = ctx.message.author.voice.channel

            if ctx.voice_client is None:
                await channel.connect()

            if (SameChannel(ctx)==False):
                raise Exception('Not in the same channel.')
            try:
                if ctx.voice_client.is_playing():
                    ctx.voice_client.stop()

                track = "../Japan/MinaNoNihongo/" + tracknr + ".flac"

                source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(track), gVol)
                ctx.voice_client.play(source)

            except Exception as e:
                print(e)
        except Exception as e:
            print(e)

    @commands.command(aliases=['np'])
    async def nippel(self, ctx, track: str):
        ''' Plays a sound from the nippelboard.'''
        try:
            channel = ctx.message.author.voice.channel

            if ctx.voice_client is None:
                await channel.connect()

            if (SameChannel(ctx)==False):
                raise Exception('Not in the same channel.')
            try:
                if ctx.voice_client.is_playing():
                    ctx.voice_client.stop()

                track = "./Nippel/" + track + ".mp3"

                source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(track), gVol)
                ctx.voice_client.play(source)

            except Exception as e:
                print(e)
        except Exception as e:
            print(e)

    @commands.command(aliases=['s'])
    async def skip(self, ctx, *args):
        ''' Skips the current song. Alias: s'''
        global gPlaylist
        try:
            if (SameChannel(ctx)==False):
                raise Exception('Not in the same channel.')

            try:
                ctx.voice_client.stop()
                source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(gPlaylist[0]), gVol)
                ctx.voice_client.play(source, after = myafter)
                await ctx.send('Now playing: {}'.format(gPlaylist[0][9:]))
                gPlaylist.pop(0)

            except Exception as e:
                await ctx.send("I need a file from the local filesystem\n" + "Error Code: " + str(e))
        except Exception as e:
            print(e)

    @commands.command()
    async def vol(self, ctx, args):
        ''' Changes the player's volume. Set to something between 0 and 100.'''
        global gVol
        if ctx.voice_client is not None:
            try:
                if (SameChannel(ctx)==False):
                    raise Exception('Not in the same channel.')
                gVol = float(args) / 200
                if gVol >= 0.5:
                    gVol = 0.5

                ctx.voice_client.source.volume = gVol
                await ctx.send("Changed volume to {}%".format(args))
            except Exception as e:
                print(e)

    @commands.command(aliases=['stfu'])
    async def stop(self, ctx):
        ''' Stops the music. Alias: stfu '''
        global gPlaylist
        gPlaylist = []
        if ctx.voice_client is not None:
            try:
                if (SameChannel(ctx)==False):
                    raise Exception('Not in the same channel.')
                ctx.voice_client.stop()
            except Exception as e:
                print(e)

    @commands.command(aliases=['r'])
    async def resume(self, ctx):
        ''' Resumes the music. Alias: r'''
        if ctx.voice_client is not None:
            try:
                if (SameChannel(ctx)==False):
                    raise Exception('Not in the same channel.')
                ctx.voice_client.resume()
            except Exception as e:
                print(e)

    @commands.command(aliases=['p'])
    async def pause(self, ctx):
        ''' Pauses the music. Alias: p '''
        if ctx.voice_client is not None:
            try:
                if (SameChannel(ctx)==False):
                    raise Exception('Not in the same channel.')
                ctx.voice_client.pause()
            except Exception as e:
                print(e)

    @commands.command(aliases=['pl'])
    async def playlist(self, ctx):
        ''' Shows the next songs. Alias: pl '''
        try:
            next = ''
            n = 1
            for i in gPlaylist:
                next = next + i[9:] + '\n'
                if n > 4:
                    break
                n += 1
            await ctx.send('Next in the line:\n'+next)
        except Exception as e:
            print(e)

bot.add_cog(music(bot))

class stuff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command()
    async def ping(self, ctx):
        ''' You can check if the bot is up and running. '''
        latency = bot.latency
        msg = "I'm awake! And reacting in " + str(latency) + " seconds"
        await ctx.send(msg)

    @commands.command(aliases=['meow', 'purr'])
    async def cat(self, ctx):
        '''Outputs a random cat. (Needs webpreview enabled.) Alias: meow, purr'''
        async with ctx.typing():
            async with aiohttp.ClientSession() as cs:
                async with cs.get("http://aws.random.cat/meow") as r:
                    if r.status != 200:
                        return await channel.send('Could not reach random.cat :(')
                    data = await r.json()
                    embed = discord.Embed(title='meow')
                    embed.set_image(url = data['file'])
                    embed.set_footer(text = "http://random.cat/")
                    await ctx.send(embed = embed)

    @commands.command()
    async def test(self, ctx, url: str):
        ''' Testing command - does something... or not '''
        song_there = os.path.isfile("song.mp3")
        try:
            if song_there:
                os.remove("song.mp3")
        except PermissionError:
            await ctx.send("Wait for the current playing music end or use the 'stop' command")
            return
        await ctx.send("Getting everything ready, playing audio soon")
        print("Someone wants to play music let me get that ready for them...")

        voice = get(bot.voice_clients, guild=ctx.guild)
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        for file in os.listdir("./"):
            if file.endswith(".mp3"):
                os.rename(file, 'song.mp3')
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio("song.mp3"), gVol)
        ctx.voice_client.play(source)

bot.add_cog(stuff(bot))

bot.run(cfg.BotToken)
