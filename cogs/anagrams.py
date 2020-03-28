import discord
from discord.ext import commands
import random
import asyncio
from concurrent.futures import CancelledError
import traceback
import json
from utils.configManager import AnagramConfig, BotConfig
from utils.log import log

class Anagrams(commands.Cog):
    """
    Play the anagram game.
    """
    def __init__(self, bot):
        self.bot = bot
        self.corpus = None
        self.channelStates = {}
        self.config = AnagramConfig()
        self.botConfig = BotConfig()

    @commands.command(name='anagram', aliases=['an'])
    async def anagram(self, ctx, numberOfQuestions = None):
        """
        Starts a game of anagrams.
        """
        if str(ctx.channel.id) not in self.channelStates:
            self.channelStates[str(ctx.channel.id)] = {}
            embed = discord.Embed(
                title = ctx.message.author.name + ' started a game of anagrams',
                description = 'Unscramble the letters to make meaningful words.',
                colour = discord.Colour.blue()
            )
            await ctx.send(embed = embed)
            try:
                await self.playAnagrams(ctx, numberOfQuestions)
            except Exception as e:
                log(ctx.channel.id, 'Oopsie, exception: ', e)
                traceback.print_exc()
        else:
            embed = discord.Embed(
                title = 'There\'s already a game running in this channel',
                description = 'Try running the command in another channel or stop the ongoing game with `'+ self.botConfig.commandPrefix + 'stop`.',
                colour = discord.Colour.red()
            )
            await ctx.send(embed = embed)

    @commands.command(name='stop', aliases=['quit', 'q', 's', 'end'])
    async def stop(self, ctx):
        """
        Stops an ongoing game of anagrams.
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
                    description = 'Type `'+ self.botConfig.commandPrefix + 'anagram` to start a new game.',
                    colour = discord.Colour.red()
                )
                await ctx.send(embed = embed)
                await self.publishScores(ctx.channel)
    
    @commands.command(name='skip', aliases=['giveup', 'sk', 'lite'])
    async def skip(self, ctx):
        """
        Skips the current question in an anagram game.
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
                answerTask.set_name('anagram-' + str(ctx.channel.id))
    

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
        
        if 'answer' not in self.channelStates[str(message.channel.id)]:
            return
        if message.content.lower() == self.channelStates[str(message.channel.id)]['answer']:
            self.channelStates[str(message.channel.id)]['answer'] = None
            await message.add_reaction('\N{THUMBS UP SIGN}')
            if message.author in self.channelStates[str(message.channel.id)]['scores']:
                self.channelStates[str(message.channel.id)]['scores'][message.author] = self.channelStates[str(message.channel.id)]['scores'][message.author] + 1
            else:
                self.channelStates[str(message.channel.id)]['scores'][message.author] = 1
            embed = discord.Embed(
                title = 'The answer was: `' + message.content.lower() + '`',
                colour = discord.Colour.green()
            )
            embed.set_author(name = message.author.name + ' got it right!', icon_url = 'https://cdn.discordapp.com/avatars/' + str(message.author.id) + '/' + str(message.author.avatar) + '.png')
            embed.set_thumbnail(url = 'https://cdn.discordapp.com/avatars/' + str(message.author.id) + '/' + str(message.author.avatar) + '.png')
            for i in self.channelStates[str(message.channel.id)]['details']:
                if 'partOfSpeech' in i and i['partOfSpeech'] is not None and 'definition' in i and i['definition'] is not None:
                    embed.add_field(name = '_' + i['partOfSpeech'] + '_', value = i['definition'], inline = False)
            await message.channel.send(embed = embed)
            try:
                self.cleanTasks(str(message.channel.id))
            except Exception as e:
                log(message.channel.id, 'Oopsie, exception: ', e)
                traceback.print_exc()
            try:
                nextQuestionTask = asyncio.create_task(self.askQuestion(message.channel, waitTime = self.config.timeToNextQuestion))
                nextQuestionTask.set_name('anagrams-' + str(message.channel.id))
            except Exception as e:
                log(message.channel.id, 'Oopsie, exception: ', e)
                traceback.print_exc()
            return
    
    async def checkGameInProgress(self, channel):
        """
        Checks if there is a game running in the channel. Sends an embed message if there are
        no games running.

        Parameters:
        channel (discord.TextChannel): The channel to be checked for running games

        Returns:
        boolean: True if there is a game running in the channel. False otherwise.
        """
        if str(channel.id) not in self.channelStates:
            embed = discord.Embed(
                title = 'There are no games in progress',
                description = 'Type `' + self.botConfig.commandPrefix + 'anagram` to start a game.',
                colour = discord.Colour.red()
            )
            await channel.send(embed = embed)
            return False
        else:
            return True

    async def playAnagrams(self, ctx, numberOfQuestions):
        """
        Function to set up and start the anagram game.

        Parameters:
        ctx (discord.ext.commands.Context): The context of the recieved command
        numberOfQuestions (int): The number of questions in the game
        """
        if self.corpus is None:
            with open(self.config.corpus) as fp:
                self.corpus = json.load(fp)
        await self.getWordsFromCorpus(ctx, numberOfQuestions)
        self.channelStates[str(ctx.channel.id)]['scores'] = {}
        askQuestionTask = asyncio.create_task(self.askQuestion(ctx.channel, self.config.timeToFirstQuestion))
        askQuestionTask.set_name('anagrams-' + str(ctx.channel.id))
        log(ctx.channel.id, 'Anagram game started.')

    async def getWordsFromCorpus(self, ctx,numberOfQuestions):
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
                title = 'The maximum allowed number is 50. Hence, setting to 50.',
                colour = discord.Colour.blue()
            )
            await ctx.send(embed = embed)
            numberOfQuestions = self.config.questionLimit
        self.channelStates[str(ctx.channel.id)]['words'] = random.sample( self.corpus.items(), int(numberOfQuestions) )
    
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
            if not self.channelStates[str(channel.id)]['words']:
                await self.publishScores(channel)
                return

            await asyncio.sleep(waitTime)
            word, details = self.channelStates[str(channel.id)]['words'][0]
            self.channelStates[str(channel.id)]['words'] = self.channelStates[str(channel.id)]['words'][1:]
            self.channelStates[str(channel.id)]['answer'] = word
            self.channelStates[str(channel.id)]['details'] = details['definitions']
            question = self.shuffle_word(word)
            self.channelStates[str(channel.id)]['question'] = discord.Embed(
                title = '`' + question + '`',
                colour = discord.Colour.blue()
            )
            if 'questionNumber' not in self.channelStates[str(channel.id)]:
                self.channelStates[str(channel.id)]['questionNumber'] = 1
            else:
                self.channelStates[str(channel.id)]['questionNumber'] += 1
            self.channelStates[str(channel.id)]['question'].set_author(name = 'Question ' + str(self.channelStates[str(channel.id)]['questionNumber']))
            await channel.send(embed = self.channelStates[str(channel.id)]['question'])
            try:
                answerTask = asyncio.create_task(self.revealAnswer(channel))
                answerTask.set_name('anagram-' + str(channel.id))
                hintTask = asyncio.create_task(self.giveHint(channel))
                hintTask.set_name('anagram-' + str(channel.id))
            except Exception as e:
                log(channel.id,'Oopsie, exception: ', e)
                traceback.print_exc()
        except asyncio.CancelledError:
            log(channel.id,'askQuestion task was cancelled')
        except KeyError:
            log(channel.id,'askQuestion task was interrupted by stop')
    
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
                title = 'The answer was `' + answer + '`',
                colour = discord.Colour.red()
            )
            for i in self.channelStates[str(channel.id)]['details']:
                if 'partOfSpeech' in i and i['partOfSpeech'] is not None and 'definition' in i and i['definition'] is not None:
                    embed.add_field(name = '_' + i['partOfSpeech'] + '_', value = i['definition'], inline = False)
            embed.set_author(name = reason)
            await channel.send(embed = embed)
            try:
                nextQuestionTask = asyncio.create_task(self.askQuestion(channel, waitTime = self.config.timeToNextQuestion))
                nextQuestionTask.set_name('anagram-' + str(channel.id))
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
        if waitTime is None:
            waitTime = self.config.timeToFirstHint
        try:
            await asyncio.sleep(waitTime)
            if not await self.checkGameInProgress(channel):
                return
            
            elif 'answer' not in self.channelStates[str(channel.id)] or self.channelStates[str(channel.id)]['answer'] is None:
                return
            
            elif self.channelStates[str(channel.id)]['question'].fields == []:
                self.channelStates[str(channel.id)]['question'].add_field(name = 'First letter', value = self.channelStates[str(channel.id)]['answer'][0], inline = True)
                await channel.send(embed = self.channelStates[str(channel.id)]['question'])
            else:
                n = len(self.channelStates[str(channel.id)]['question'].fields)
                if (n > len(self.channelStates[str(channel.id)]['details'])):
                    return
                i = self.channelStates[str(channel.id)]['details'][n-1]
                if 'definition' in i and i['definition'] is not None:
                    self.channelStates[str(channel.id)]['question'].add_field(name = 'Definition', value = i['definition'], inline = False)
                    await channel.send(embed = self.channelStates[str(channel.id)]['question'])
            if len(self.channelStates[str(channel.id)]['answer']) > self.config.shortWordLengthCutoff:
                hintTask = asyncio.create_task(self.giveHint(channel, self.config.timeToSecondHint))
                hintTask.set_name('anagram-' + str(channel.id))
            else:
                hintTask = asyncio.create_task(self.giveHint(channel, self.config.timeToSecondHintShortWords))
                hintTask.set_name('anagram-' + str(channel.id))
        except asyncio.CancelledError:
            log(channel.id, 'giveHint task was cancelled')

    async def publishScores(self, channel):
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
            winnerString = 'Ruh-roh! No one got any points.'
            showScores = False
            noOfQuestions = self.channelStates[str(channel.id)]['questionNumber']
            if len(scores) > 0:
                showScores = True
                maxScore = scores[0][1]
            if showScores:
                if len(scores) == 1 or scores[0][1] != scores[1][1]:
                    winner = scores[0][0]
                    winnerString = winner.name + ' won the game!'
                    avatar = 'https://cdn.discordapp.com/avatars/' + str(winner.id) + '/' + str(winner.avatar) + '.png'
                else:
                    winnerString = 'It\'s a tie!'
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
            embed.set_author(name = 'Game over', icon_url = avatar)
            if showScores:
                embed.add_field(name = 'Player', value = nameString)
                embed.add_field(name = 'Score', value = scoreString)
                embed.set_thumbnail(url = avatar)
            await channel.send(embed = embed)
        self.cleanTasks(str(channel.id))
        del self.channelStates[str(channel.id)]
        log(channel.id, 'Anagram game ended.')

    def cleanTasks(self, channel):
        """
        Clean up any existing game task.

        Parameters:
        channel (discord.TextChannel): Channel to clean up tasks in.
        """
        for task in asyncio.all_tasks():
            if task != asyncio.current_task() and task.get_name() == 'anagram-' + channel:
                task.cancel()
        return

    def shuffle_word(self, word):
        """
        Jumble word to make an anagram.

        Parameters:
        word (string): The word to jumble.
        """
        word = list(word)
        random.shuffle(word)
        return ''.join(word)


def setup(bot):
    """
    Called automatically by discord while loading extension. Adds the Anagram cog on to the bot.
    """
    bot.add_cog(Anagrams(bot))