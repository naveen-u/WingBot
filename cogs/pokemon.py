import discord
from discord.ext import commands
import random
import asyncio
from concurrent.futures import CancelledError
import traceback
import json
from utils.configManager import PokemonConfig, BotConfig
from utils.log import log
import re
from PIL import Image
from io import BytesIO
import numpy as np
import typing
import aiohttp
import os.path
import os

class Pokemon(commands.Cog):
    """
    Play "Who's that Pokémon?".
    """
    def __init__(self, bot):
        self.bot = bot
        self.channelStates = {}
        self.config = PokemonConfig()
        self.botConfig = BotConfig()


    @commands.group(name='pokemon', aliases = ['pm'], invoke_without_command = True, case_insensitive = True)
    async def pokemon(self, ctx, numberOfQuestions : typing.Optional[int], region : typing.Optional[str] = 'all'):
        """
        Play "Who's that Pokémon?". If no subcommands are provided, it defaults to start.
        """
        await self.start(ctx, numberOfQuestions, region)

    @pokemon.command(name='start')
    async def start(self, ctx, numberOfQuestions : typing.Optional[int], region : typing.Optional[str] = 'all'):
        """
        Start a game of "Who's that Pokémon?".
        """
        if str(ctx.channel.id) not in self.channelStates:
            self.channelStates[str(ctx.channel.id)] = {}
            embed = discord.Embed(
                title = ctx.message.author.name + ' started a game of "Who\'s that Pokémon?"',
                description = 'Figure out who the given Pokémon is.',
                colour = discord.Colour.blue()
            )
            await ctx.send(embed = embed)
            try:
                await self.playPokemon(ctx, numberOfQuestions, region)
            except Exception as e:
                log(ctx.channel.id, 'Oopsie, exception: ', e)
                traceback.print_exc()
        else:
            embed = discord.Embed(
                title = 'There\'s already a game running in this channel',
                description = 'Try running the command in another channel or stop the ongoing game with `'+ self.botConfig.commandPrefix + 'pokemon stop`.',
                colour = discord.Colour.red()
            )
            await ctx.send(embed = embed)

    @pokemon.command(name='stop', aliases=['s', 'quit', 'q', 'end'])
    async def stop(self, ctx):
        """
        Stops an ongoing game of "Who's that Pokémon?".
        """
        if await self.checkGameInProgress(ctx.channel):
            try:
                self.cleanTasks(str(ctx.channel.id))
            except Exception as e:
                log(ctx.channel.id, 'Oopsie, exception: ', e)
                traceback.print_exc()
            else:
                embed = discord.Embed(
                    title = ctx.message.author.name + ' cancelled the game!',
                    description = 'Type `'+ self.botConfig.commandPrefix + 'pokemon start` to start a new game.',
                    colour = discord.Colour.red()
                )
                await ctx.send(embed = embed)
                await self.publishScores(ctx.channel)
                self.stopGame(ctx.channel)
    
    @pokemon.command(name='skip', aliases=['giveup', 'sk', 'lite'])
    async def skip(self, ctx):
        """
        Skips the current question.
        """
        if not await self.checkGameInProgress(ctx.channel):
            return
        elif  'answer' not in self.channelStates[str(ctx.channel.id)] or self.channelStates[str(ctx.channel.id)]['answer'] is None:
            return
        else:
            try:
                self.cleanTasks(str(ctx.channel.id))
            except Exception as e:
                log(ctx.channel.id, 'Oopsie, exception: ', e)
                traceback.print_exc()
            else:
                answerTask = asyncio.create_task(self.revealAnswer(ctx.channel, waitTime = 0, reason = 'Question skipped'))
                answerTask.set_name('pokemon-' + str(ctx.channel.id))
    
    @pokemon.command(name='scores', alias=['points', 'sc', 'p'])
    async def scores(self, ctx):
        """
        Displays the scoreboard.
        """
        await self.publishScores(ctx.channel, False)

    @commands.Cog.listener()
    async def on_message(self,message):
        """
        Event listener to listen to user messages. If a message is recieved and a 
        game is in progress, it checks if the answer is correct.
        """
        if message.author == self.bot.user:
            return

        if str(message.channel.id) not in self.channelStates:
            return
        
        if  not self.channelStates[str(message.channel.id)]:
            return
        
        if 'answer' not in self.channelStates[str(message.channel.id)] or self.channelStates[str(message.channel.id)]['answer'] is None:
            return

        if message.content.lower() == self.channelStates[str(message.channel.id)]['answer'].lower():
            self.channelStates[str(message.channel.id)]['answer'] = None
            await message.add_reaction('\N{THUMBS UP SIGN}')
            if message.author in self.channelStates[str(message.channel.id)]['scores']:
                self.channelStates[str(message.channel.id)]['scores'][message.author] = self.channelStates[str(message.channel.id)]['scores'][message.author] + 1
            else:
                self.channelStates[str(message.channel.id)]['scores'][message.author] = 1
            embed = discord.Embed(
                title = 'It\'s ' + message.content.capitalize() + '!',
                colour = discord.Colour.green()
            )
            embed.set_author(name = message.author.name + ' got it right!', icon_url = 'https://cdn.discordapp.com/avatars/' + str(message.author.id) + '/' + str(message.author.avatar) + '.png')
            
            embed.set_image(url = self.config.pokemonSpriteAPI.replace('{id}', str(self.channelStates[str(message.channel.id)]['pokemonId'])))
            types = self.channelStates[str(message.channel.id)]['types']
            embed.add_field(name = 'Type', value = self.config.getEmoji(types[0]) + ' ' + types[0].capitalize(), inline = True)
            if len(types) == 2:
                embed.add_field(name = '\u200b', value = self.config.getEmoji(types[1]) + ' ' + types[1].capitalize(), inline = True)
            embed.add_field(name = 'Pokédex', value = self.channelStates[str(message.channel.id)]['descriptions'][0], inline = False)
            await message.channel.send(embed = embed)
            try:
                self.cleanTasks(str(message.channel.id))
            except Exception as e:
                log(message.channel.id, 'Oopsie, exception: ', e)
                traceback.print_exc()
            try:
                nextQuestionTask = asyncio.create_task(self.askQuestion(message.channel, waitTime = self.config.timeToNextQuestion))
                nextQuestionTask.set_name('pokemon-' + str(message.channel.id))
            except Exception as e:
                log(message.channel.id, 'Oopsie, exception: ', e)
                traceback.print_exc()
            return
    
    async def checkGameInProgress(self, channel, sendEmbed = True):
        """
        Checks if there is a game running in the channel. Sends an embed message if there are
        no games running and sendEmbed is True.

        Parameters:
        channel (discord.TextChannel): The channel to be checked for running games
        sendEmbed (boolean): Whether or not to send an embed if there are no games in progress

        Returns:
        boolean: True if there is a game running in the channel. False otherwise.
        """
        if str(channel.id) not in self.channelStates:
            if sendEmbed:
                file = discord.File("resources/common/oak.png", filename="oak.png")
                embed = discord.Embed(
                    title = 'Oak\'s words echoed... There\'s a time and place for everything, but not now.',
                    description = 'There are no games in progress at the moment! Type `' + self.botConfig.commandPrefix + 'pokemon start` to start a game.',
                    colour = discord.Colour.red()
                )
                embed.set_thumbnail(url="attachment://oak.png")
                await channel.send(file=file, embed=embed)
            return False
        else:
            return True

    async def playPokemon(self, ctx, numberOfQuestions, region):
        """
        Function to set up and start the game.

        Parameters:
        ctx (discord.ext.commands.Context): The context of the recieved command
        numberOfQuestions (int): The number of questions in the game
        """
        await self.getPokemonList(ctx, numberOfQuestions, region)
        self.channelStates[str(ctx.channel.id)]['scores'] = {}
        askQuestionTask = asyncio.create_task(self.askQuestion(ctx.channel, self.config.timeToFirstQuestion))
        askQuestionTask.set_name('pokemon-' + str(ctx.channel.id))
        log(ctx.channel.id, 'Pokemon game started.')
    
    async def fetchSprite(self, id:int, session:object, ctx):
        """
        Sends a GET request for a pokemon's sprite and starts a task to create a
        question image.

        Parameters:
        id (int): The Pokemon's ID
        session (aiohttp.ClientSession): Session to make the GET request from
        ctx (discord.ext.commands.Context): The context of the recieved command
        """
        url = self.config.pokemonSpriteAPI.replace('{id}', str(id))
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.read()
                task = asyncio.create_task(self.makeQuestion(BytesIO(data), str(id)))
                task.set_name(f'pokemon-sprite-{id}-{ctx.channel.id}')
                return task
        return False
    
    async def fetchData(self, id:int, session: object, ctx):
        """
        Sends a GET request for a pokemon's data.

        Parameters:
        id (int): The Pokemon's ID
        session (aiohttp.ClientSession): Session to make the GET request from
        ctx (discord.ext.commands.Context): The context of the recieved command
        """
        url = self.config.pokemonDataAPI.replace('{id}', str(id))
        async with session.get(url) as r:
            if r.status == 200:
                data = await r.json()
                name = data['species']['name'].replace('-', ' ').capitalize()
                typeList = {}
                for i in data['types']:
                    typeList[str(i['slot'])] = i['type']['name']
                typeList = [typeList[key] for key in sorted(typeList.keys())]
                d = {}
                d['id'] = id
                d['name'] = name
                d['typeList'] = typeList
                return d
        return False
    
    async def fetchSpeciesData(self, id: int, session: object, ctx):
        """
        Sends a GET request for a pokemon species' data.

        Parameters:
        id (int): The Pokemon species' ID
        session (aiohttp.ClientSession): Session to make the GET request from
        ctx (discord.ext.commands.Context): The context of the recieved command
        """
        url = self.config.pokemonSpeciesDataAPI.replace('{id}', str(id))
        async with session.get(url) as speciesData:
            if speciesData.status == 200:
                speciesData = await speciesData.json()
                descriptionList = []
                for i in speciesData['flavor_text_entries']:
                    if i['language']['name'] == 'en':
                        descriptionList.append(i['flavor_text'].replace('\n', ' '))
                d = {}
                d['id'] = id
                d['descriptionList'] = descriptionList
                return d
        return False

    
    async def fetch(self, id: int, session: object, ctx, start, end):
        """
        Fetch all the data for a Pokemon. If the required data is not available,
        pick a new Pokemon and get data for that.

        Parameters:
        id (int): The Pokemon species' ID
        session (aiohttp.ClientSession): Session to make the GET request from
        ctx (discord.ext.commands.Context): The context of the recieved command
        start (int): The starting ID in the available list of Pokemon
        end (int): The starting ID in the available list of Pokemon
        """
        tasks = []
        task = asyncio.ensure_future(self.fetchSprite(id, session, ctx))
        tasks.append(task)
        task = asyncio.ensure_future(self.fetchData(id, session, ctx))
        tasks.append(task)
        task = asyncio.ensure_future(self.fetchSpeciesData(id, session, ctx))
        tasks.append(task)
        results = await asyncio.gather(*tasks)
        if False in results:
            # Some data is not available. Get a new pokemon and try again.
            if results[0] is not False:
                results[0].cancel()
            oldId = id
            while id in self.channelStates[str(ctx.channel.id)]['pokeList']:
                id = random.randrange(start,end + 1)
            self.channelStates[str(ctx.channel.id)]['pokeList'].append(id)
            log(ctx.channel.id,f'Replacing {oldId} with {id}')
            task = asyncio.create_task(self.fetch(id, session, ctx, start, end))
            await task
            return
        else:
            result = {}
            result.update(results[1])
            result.update(results[2])
            self.channelStates[str(ctx.channel.id)]['pokemonIdList'].append(result)
            return


    async def getPokemonList(self, ctx,numberOfQuestions, region):
        """
        Get the words required for the game from the corpus.

        Parameters:
        ctx (discord.ext.commands.Context): The context of the recieved command
        numberOfQuestions (int): The number of questions in the game
        """
        if numberOfQuestions is None:
            numberOfQuestions = self.config.noOfQuestions
        elif int(numberOfQuestions) > self.config.questionLimit:
            embed = discord.Embed(
                title = 'The maximum allowed number is ' + str(self.config.questionLimit) + '. Defaulting to that.',
                colour = discord.Colour.blue()
            )
            await ctx.send(embed = embed)
            numberOfQuestions = self.config.questionLimit
        if region.lower() not in self.config.regionWiseDex:
            embed = discord.Embed(
                title = 'Couldn\'t find the region you specified. Defaulting to all.',
                colour = discord.Colour.blue()
            )
            await ctx.send(embed = embed)
            region = 'all'
        start, end = self.config.getRange(region.lower())
        self.channelStates[str(ctx.channel.id)]['pokeList'] = random.sample(range(start,end + 1), int(numberOfQuestions))
        tasks = []
        self.channelStates[str(ctx.channel.id)]['pokemonIdList'] = []
        async with aiohttp.ClientSession(loop = self.bot.loop) as session:
            for id in list(self.channelStates[str(ctx.channel.id)]['pokeList']):
                task = asyncio.ensure_future(self.fetch(id, session, ctx, start, end))
                tasks.append(task)
            _ = await asyncio.gather(*tasks)
        log(ctx.channel.id, 'Pokemon List: ' + str(self.channelStates[str(ctx.channel.id)]['pokeList']))
        del self.channelStates[str(ctx.channel.id)]['pokeList']
    
    async def makeQuestion(self, data, id):
        # Async wrapper around createQuestionImage
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.createQuestionImage, data, id)
    
    def createQuestionImage(self, image, id):
        if not os.path.exists(self.config.pokemonSpriteDirectory):
            os.makedirs(self.config.pokemonSpriteDirectory)
        fileName = f'{self.config.pokemonSpriteDirectory}/{id}.png'
        if os.path.isfile(fileName):
            return fileName
        sprite = Image.open(image)
        alpha = sprite.split()[-1]
        spriteImage = Image.new('RGBA',sprite.size,(54,57,63,0))
        bgImage = Image.open(self.config.backgroundImage, 'r')
        spriteImage.putalpha(alpha)
        
        spriteImage.load()
        imageData = np.asarray(spriteImage)
        imageDataBW = imageData.max(axis=2)
        nonEmptyColumns = np.where(imageDataBW.max(axis=0)>0)[0]
        nonEmptyRows = np.where(imageDataBW.max(axis=1)>0)[0]
        cropBox = (min(nonEmptyRows), max(nonEmptyRows), min(nonEmptyColumns), max(nonEmptyColumns))

        imageDataNew = imageData[cropBox[0]:cropBox[1]+1, cropBox[2]:cropBox[3]+1 , :]
        newImage = Image.fromarray(imageDataNew)

        mywidth = 750
        wpercent = (mywidth/float(newImage.size[0]))
        hsize = int((float(newImage.size[1])*float(wpercent)))
        newImage = newImage.resize((mywidth,hsize), Image.ANTIALIAS)
        bgImage.paste(newImage, (225,220), newImage)
        bgImage.save(fileName)
        return fileName

    async def askQuestion(self, channel, waitTime = None):
        """
        Ask the next question.

        Parameters:
        channel (discord.TextChannel): Channel to send the message to.
        waitTime (int): Seconds to wait before asking the question.
        """
        if waitTime is None:
            waitTime = self.config.timeToNextQuestion
        try:
            if not self.channelStates[str(channel.id)]['pokemonIdList']:
                await self.publishScores(channel)
                self.stopGame(channel)
                return

            await asyncio.sleep(waitTime)
            pokemonData = self.channelStates[str(channel.id)]['pokemonIdList'][0]
            self.channelStates[str(channel.id)]['pokemonIdList'] = self.channelStates[str(channel.id)]['pokemonIdList'][1:]
            self.channelStates[str(channel.id)]['pokemonId'] = pokemonData['id']
            self.channelStates[str(channel.id)]['answer'] = pokemonData['name']
            self.channelStates[str(channel.id)]['types'] = pokemonData['typeList']
            self.channelStates[str(channel.id)]['descriptions'] = pokemonData['descriptionList']

            print('Pokemon: ' + pokemonData['name'])
            id = pokemonData['id']
            for task in asyncio.all_tasks():
                if task.get_name() == f'pokemon-sprite-{id}-{channel.id}':
                    await task
                    break

            fileName = f'{self.config.pokemonSpriteDirectory}/{id}.png'
            self.channelStates[str(channel.id)]['questionFile'] = fileName
            spriteFile = discord.File(fileName, filename = 'sprite.png')

            self.channelStates[str(channel.id)]['question'] = discord.Embed(
                title = 'Who\'s that Pokémon?',
                colour = discord.Colour.blue()
            )
            if 'questionNumber' not in self.channelStates[str(channel.id)]:
                self.channelStates[str(channel.id)]['questionNumber'] = 1
            else:
                self.channelStates[str(channel.id)]['questionNumber'] += 1
            self.channelStates[str(channel.id)]['question'].set_author(name = 'Question ' + str(self.channelStates[str(channel.id)]['questionNumber']))
            self.channelStates[str(channel.id)]['question'].set_image(url = f'attachment://sprite.png')
            await channel.send(file = spriteFile, embed = self.channelStates[str(channel.id)]['question'])
            try:
                answerTask = asyncio.create_task(self.revealAnswer(channel))
                answerTask.set_name('pokemon-' + str(channel.id))
                hintTask = asyncio.create_task(self.giveHint(channel))
                hintTask.set_name('pokemon-' + str(channel.id))
            except Exception as e:
                log(channel.id,'Oopsie, exception: ', e)
                traceback.print_exc()
        except asyncio.CancelledError:
            log(channel.id,'askQuestion task was cancelled')
        except KeyError:
            log(channel.id,'askQuestion task was interrupted by stop')
            traceback.print_exc()
    
    async def revealAnswer(self, channel, waitTime = None, reason = 'Time\'s up!'):
        """
        Reveal the answer to the current question.

        Parameters:
        channel (discord.TextChannel): Channel to send the message to.
        waitTime (int): Seconds to wait before asking the question.
        reason (string): Reason why the answer is being revealed.
        """
        if waitTime is None:
            waitTime = self.config.timePerQuestion
        try:
            await asyncio.sleep(waitTime)
            answer = self.channelStates[str(channel.id)]['answer']
            self.channelStates[str(channel.id)]['answer'] = None
            self.cleanTasks(str(channel.id))
            embed = discord.Embed(
                title = 'It\'s ' + answer + '!',
                colour = discord.Colour.red()
            )
            types = self.channelStates[str(channel.id)]['types']
            embed.add_field(name = 'Type', value = self.config.getEmoji(types[0]) + ' ' + types[0].capitalize(), inline = True)
            if len(types) == 2:
                embed.add_field(name = '\u200b', value = self.config.getEmoji(types[1]) + ' ' + types[1].capitalize(), inline = True)

            embed.add_field(name = 'Pokédex', value = self.channelStates[str(channel.id)]['descriptions'][0], inline = False)
            embed.set_author(name = reason)
            embed.set_image(url = self.config.pokemonSpriteAPI.replace('{id}', str(self.channelStates[str(channel.id)]['pokemonId'])))
            await channel.send(embed = embed)
            try:
                nextQuestionTask = asyncio.create_task(self.askQuestion(channel, waitTime = self.config.timeToNextQuestion))
                nextQuestionTask.set_name('pokemon-' + str(channel.id))
            except Exception as e:
                log(channel.id,'Oopsie, exception', e)
                traceback.print_exc()
        except asyncio.CancelledError:
            log(channel.id, 'revealAnswer task was cancelled')
    
    async def giveHint(self, channel, waitTime = None):
        """
        Give the next hint for the question.

        Parameters:
        channel (discord.TextChannel): Channel to send the message to.
        waitTime (int): Seconds to wait before asking the question.
        """
        # pass
        if waitTime is None:
            waitTime = self.config.timeToFirstHint
        try:
            await asyncio.sleep(waitTime)
            if not await self.checkGameInProgress(channel):
                return
            
            elif 'answer' not in self.channelStates[str(channel.id)] or self.channelStates[str(channel.id)]['answer'] is None:
                return
            
            elif self.channelStates[str(channel.id)]['question'].fields == []:
                types = self.channelStates[str(channel.id)]['types']
                self.channelStates[str(channel.id)]['question'].add_field(name = 'Type', value = self.config.getEmoji(types[0]) + ' ' + types[0].capitalize(), inline = True)
                if len(types) == 2:
                    self.channelStates[str(channel.id)]['question'].add_field(name = '\u200b', value = self.config.getEmoji(types[1]) + ' ' + types[1].capitalize(), inline = True)
                spriteFile = discord.File(self.channelStates[str(channel.id)]['questionFile'], filename = 'sprite.png')
                await channel.send(file = spriteFile, embed = self.channelStates[str(channel.id)]['question'])
                hintTask = asyncio.create_task(self.giveHint(channel, self.config.timeToSecondHint))
                hintTask.set_name('pokemon-' + str(channel.id))
            else:
                n = len(self.channelStates[str(channel.id)]['question'].fields)
                if (n > 1):
                    return
                insensitiveName = re.compile(re.escape(self.channelStates[str(channel.id)]['answer']), re.IGNORECASE)
                self.channelStates[str(channel.id)]['question'].add_field(name = 'Pokédex', value = insensitiveName.sub(':black_large_square::black_large_square::black_large_square:', self.channelStates[str(channel.id)]['descriptions'][0]), inline = False)
                spriteFile = discord.File(self.channelStates[str(channel.id)]['questionFile'], filename = 'sprite.png')
                await channel.send(file = spriteFile, embed = self.channelStates[str(channel.id)]['question'])

            
        except asyncio.CancelledError:
            log(channel.id, 'giveHint task was cancelled')

    async def publishScores(self, channel, gameEnded = True):
        """
        Publish the scores.

        Parameters:
        channel (discord.TextChannel): Channel to send the message to.
        """
        if 'questionNumber' in self.channelStates[str(channel.id)]:
            scores = sorted(self.channelStates[str(channel.id)]['scores'].items(), key=lambda x: x[1], reverse = True)
            nameString = ''
            scoreString = ''
            avatar = ''
            maxScore = -1
            if gameEnded:
                winnerString = 'Ruh-roh! No one got any points.'
            else:
                winnerString = 'No points so far.'
            showScores = False
            noOfQuestions = self.channelStates[str(channel.id)]['questionNumber']
            if len(scores) > 0:
                showScores = True
                maxScore = scores[0][1]
            if showScores:
                if len(scores) == 1 or scores[0][1] != scores[1][1]:
                    winner = scores[0][0]
                    if gameEnded:
                        winnerString = winner.name + ' won the game!'
                    else:
                        winnerString = winner.name + ' is in the lead!'
                    avatar = 'https://cdn.discordapp.com/avatars/' + str(winner.id) + '/' + str(winner.avatar) + '.png'
                else:
                    if gameEnded:
                        winnerString = 'It\'s a tie!'
                    else:
                        winnerString = 'It\'s tied at the top!'
                for user, score in scores:
                    if score == maxScore:
                        nameString = nameString + '**' + user.name + '**\n'
                        scoreString = scoreString + '**' + str(round(score*100/noOfQuestions, 2)) +'**\n'
                    else:
                        nameString = nameString + user.name + '\n'
                        scoreString = scoreString + str(round(score*100/noOfQuestions, 2)) + '\n'
            embed = discord.Embed(
                title = winnerString,
                colour = discord.Colour.blue()
            )
            if gameEnded:
                embed.set_author(name = 'Game over', icon_url = avatar)
            else:
                embed.set_author(name = 'Scores so far', icon_url = avatar)
            if showScores:
                embed.add_field(name = 'Player', value = nameString)
                embed.add_field(name = 'Score', value = scoreString)
                embed.set_thumbnail(url = avatar)
            await channel.send(embed = embed)
        
    
    def stopGame(self, channel):
        self.cleanTasks(str(channel.id))
        del self.channelStates[str(channel.id)]
        log(channel.id, 'Pokemon game ended.')

    def cleanTasks(self, channel = ''):
        """
        Clean up any existing game task.

        Parameters:
        channel (discord.TextChannel): Channel to clean up tasks in.
        """
        for task in asyncio.all_tasks():
            if task != asyncio.current_task() and task.get_name().startswith('pokemon-' + channel):
                task.cancel()
        return
    
    def cleanSprites(self):
        """
        Deletes the question images from the sprite folder.
        """
        mydir = self.config.pokemonSpriteDirectory
        if not os.path.exists(mydir):
            return
        filelist = [ f for f in os.listdir(mydir) ]
        for f in filelist:
            os.remove(os.path.join(mydir, f))

    def signalHandler(self):
        """
        Called by bot when it recieves a SIGTERM or SIGINT. For cleanup activities before exiting.
        """
        print('Cancelling tasks...')
        self.cleanTasks()
        print('Deleting sprite data...')
        self.cleanSprites()


def setup(bot):
    """
    Called automatically by discord while loading extension. Adds the Pokemon cog on to the bot.
    """
    bot.add_cog(Pokemon(bot))