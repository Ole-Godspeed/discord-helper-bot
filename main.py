import discord
from discord.ext import commands
import random
import os
import config as cfg
import aiohttp
import io

prefix = cfg.Prefix
bot = commands.Bot(command_prefix=prefix)
gVol = cfg.DefaultVolume
gPlaylist = []

@bot.event
async def on_ready():
    print("At your service! Bot is online now.")

@bot.command()
async def ping(ctx):
    ''' You can check if the bot is up and running. '''
    latency = bot.latency
    msg = "I'm awake! And reacting in " + str(latency) + " seconds"
    await ctx.send(msg)

@bot.command()
async def roll(ctx, roll : str):
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
            mod = ' + ' + nmod
        elif(nmod < 0):
            mod = ' - ' + nmod
        else:
            mod = ''

        if (numDice == '1') & (mod == '0'):
            await ctx.send(ctx.message.author.mention + "\n**Result:** " + resultString)
        else:
            await ctx.send(ctx.message.author.mention + "\n**Result:** " + resultString + "\n**Total" + mod + ":** " + str(resultTotal))

    except Exception as e:
        print(e)
        return

@bot.command()
async def flip(ctx, *args):
    ''' Flip a coin. Default sides are 'head' and 'tails'. '''
    if len(args) >= 2:
        choices = [str(args[0]), str(args[1])]
    else:
        choices = ['head', 'tails']

    res = random.choice(choices)
    await ctx.send('The coin shows ' + res + '.')

def SameChannel (ctx):
    same = False
    author = ctx.message.author.voice.channel
    bot = ctx.voice_client.channel

    if (author == bot):
        same = True
    return same

@bot.command(aliases=['lonely','summon'])
async def join(ctx):
    ''' Make the Bot join the voice_channel. Alias: lonely, summon '''
    try:
        channel = ctx.message.author.voice.channel
        await channel.connect()
    except Exception as e:
        print(e)

@bot.command(aliases=['ffs','release'])
async def leave(ctx):
    ''' Make the Bot leave the voice_channel. Alias: ffs, release '''
    try:
        await ctx.voice_client.disconnect()
    except Exception as e:
        print(e)

@bot.command()
async def show(ctx, *args):
    ''' Shows content of a Folder (pass with "" in case of spaces) '''
    path = 'G:/Musik'
    if len(args) != 0:
        path = path + '/' + args[0]
    try:
        content = str(os.listdir(path)).strip('[]')
        await ctx.send('Found following stuff in the dir ' + path +':\n' + content)
    except Exception as e:
        await ctx.send('Did not find the folder you wanted to show the content.')

@bot.command()
async def play(ctx, *args):
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

        if len(args) == 2:
            random.shuffle(gPlaylist)

        if os.path.isdir(path):
            for root, directories, filenames in os.walk(path):
                for filename in filenames:
                    if '.flac' in filename:
                        gPlaylist.append(os.path.join(root,filename))
        else:
           gPlaylist.append(path)

        try:
            if not ctx.voice_client.is_playing():
                source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(gPlaylist[0]), gVol)
                ctx.voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else None) # in a galaxy far away Helper-Bot plays the next song - but I'm to stupid for it.
                await ctx.send('Now playing: {}'.format(gPlaylist[0][9:]))
                gPlaylist.pop(0)

        except Exception as e:
            await ctx.send("I need a file from the local filesystem\n" + "Error Code: " + str(e))
    except Exception as e:
        print(e)

@bot.command(aliases=['s'])
async def skip(ctx, *args):
    ''' Skips the current song. Alias: s'''
    global gPlaylist
    try:
        if (SameChannel(ctx)==False):
            raise Exception('Not in the same channel.')

        try:
            ctx.voice_client.stop()
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(gPlaylist[0]), gVol)
            ctx.voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else None)
            await ctx.send('Now playing: {}'.format(gPlaylist[0][9:]))
            gPlaylist.pop(0)

        except Exception as e:
            await ctx.send("I need a file from the local filesystem\n" + "Error Code: " + str(e))
    except Exception as e:
        print(e)

@bot.command()
async def vol(ctx, args):
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

@bot.command(aliases=['stfu'])
async def stop(ctx):
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

@bot.command(aliases=['r'])
async def resume(ctx):
    ''' Resumes the music. Alias: r'''
    if ctx.voice_client is not None:
        try:
            if (SameChannel(ctx)==False):
                raise Exception('Not in the same channel.')
            ctx.voice_client.resume()
        except Exception as e:
            print(e)

@bot.command(aliases=['p'])
async def pause(ctx):
    ''' Pauses the music. Alias: p '''
    if ctx.voice_client is not None:
        try:
            if (SameChannel(ctx)==False):
                raise Exception('Not in the same channel.')
            ctx.voice_client.pause()
        except Exception as e:
            print(e)

@bot.command(aliases=['pl'])
async def playlist(ctx):
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

@bot.command(aliases=['meow', 'purr'])
async def cat(ctx):
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

bot.run(cfg.BotToken)
