# Wing Bot

A Discord bot to play games, get xkcd updates, browse reddit, and more!

## Development

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

- python-3.8 or newer
- [A Discord token](https://discordpy.readthedocs.io/en/latest/discord.html)
- [A Reddit application's credentials](https://ssl.reddit.com/prefs/apps/)
- [A mongoDB instance](https://docs.atlas.mongodb.com/getting-started/) and its [connection string](https://docs.mongodb.com/manual/reference/connection-string/)

### Installing

- Install the required packages using:

```
pip install -r requirements.txt
```

### Configuration

- Create a file named `.env` in the root directory with:

```
DISCORD_TOKEN=<your discord token>
REDDIT_CLIENT_ID=<your reddit app's client ID>
REDDIT_SECRET=<your reddit app's client secret>
MONGODB_CONNECTION_STRING=<your mongodb connection string>
```

### Deployment

Run `python wingbot.py` from the root directory.

## Authors

- **Naveen Unnikrishnan** - _Xkcd, anagrams, pokemon, bullshit, and more_ - [naveen-u](https://github.com/naveen-u)
- **Adhitya Mamallan** - _Reddit and polls_ - [adhityamamallan](https://github.com/adhityamamallan)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
