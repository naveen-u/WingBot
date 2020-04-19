import yaml

class Config(object):
    def __init__(self, section):
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
            self._config = config[section]

    def get_property(self, propertyName):
        if propertyName not in self._config.keys():
            return None
        return self._config[propertyName]


class BotConfig(Config):
    def __init__(self):
        Config.__init__(self,'Bot')

    @property
    def commandPrefix(self):
        return self.get_property('CommandPrefix')

    @property
    def activity(self):
        return self.get_property('Activity')

    @property
    def cogDirectory(self):
        return self.get_property('CogDirectory')

    @property
    def cogs(self):
        return self.get_property('Cogs')


class AnagramConfig(Config):
    def __init__(self):
        Config.__init__(self,'Anagram')
    
    @property
    def corpus(self):
        return self.get_property('Corpus')
    
    @property
    def noOfQuestions(self):
        return int(self.get_property('NoOfQuestions'))
    
    @property
    def questionLimit(self):
        return int(self.get_property('QuestionLimit'))

    @property
    def timeToFirstQuestion(self):
        return int(self.get_property('TimeToFirstQuestion'))

    @property
    def timeToNextQuestion(self):
        return int(self.get_property('TimeToNextQuestion'))

    @property
    def timePerQuestion(self):
        return int(self.get_property('TimePerQuestion'))

    @property
    def timeToFirstHint(self):
        return int(self.get_property('TimeToFirstHint'))

    @property
    def timeToSecondHint(self):
        return int(self.get_property('TimeToSecondHint'))

    @property
    def timeToSecondHintShortWords(self):
        return int(self.get_property('TimeToSecondHintShortWords'))

    @property
    def shortWordLengthCutoff(self):
        return int(self.get_property('ShortWordLengthCutoff'))
    
    @property
    def wordsAPI(self):
        return self.get_property('WordsAPI')


class GarlicConfig(Config):
    def __init__(self):
        Config.__init__(self,'Garlic')
    
    @property
    def template(self):
        return self.get_property('Template')
    
    @property
    def darkTemplate(self):
        return self.get_property('DarkTemplate')
    
    @property
    def font(self):
        return self.get_property('Font')

class PokemonConfig(Config):
    def __init__(self):
        Config.__init__(self,'Pokemon')

    @property
    def noOfQuestions(self):
        return int(self.get_property('NoOfQuestions'))

    @property
    def questionLimit(self):
        return int(self.get_property('QuestionLimit'))

    @property
    def timeToFirstQuestion(self):
        return int(self.get_property('TimeToFirstQuestion'))

    @property
    def timeToNextQuestion(self):
        return int(self.get_property('TimeToNextQuestion'))

    @property
    def timePerQuestion(self):
        return int(self.get_property('TimePerQuestion'))

    @property
    def timeToFirstHint(self):
        return int(self.get_property('TimeToFirstHint'))

    @property
    def timeToSecondHint(self):
        return int(self.get_property('TimeToSecondHint'))

    @property
    def pokemonDataAPI(self):
        return self.get_property('PokemonDataAPI')
    
    @property
    def pokemonSpeciesDataAPI(self):
        return self.get_property('PokemonSpeciesDataAPI')

    @property
    def pokemonSpriteAPI(self):
        return self.get_property('PokemonSpriteAPI')

    @property
    def pokemonSpriteDirectory(self):
        return self.get_property('PokemonSpriteDirectory')

    @property
    def backgroundImage(self):
        return self.get_property('BackgroundImage')

    @property
    def typeToEmojiMap(self):
        return self.get_property('TypeToEmojiMap')

    def getEmoji(self, t: str):
        return self.typeToEmojiMap[t]

    @property
    def regionWiseDex(self):
        return self.get_property('RegionWiseDex')

    def getRange(self, region: str):
        return self.regionWiseDex[region]['start'], self.regionWiseDex[region]['end']
