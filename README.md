# Wing Bot

A Discord bot to play anagrams, "who's that Pokemon?", and more!

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

- python-3.8
- A Discord token
- A Reddit bot application's credentials


### Installing

- Install the required packages using:

```
pip -r requirements.txt
```

- Create a `.env` file in the root directory with:
```
DISCORD_TOKEN=<your discord token>
REDDIT_CLIENT_ID=<your reddit app's client ID>
REDDIT_SECRET=<your reddit app's client secret>
``` 

## Deployment

Run `python wingbot.py` from the root directory. 

## Authors

* **Naveen Unnikrishnan** - *Initial work* - [naveen-u](https://github.com/naveen-u)
* **Adhitya Mamallan** - *Added Reddit and other useful cogs* - [adhityamamallan](https://github.com/adhityamamallan)


## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
