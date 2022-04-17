


# Clash Hogs

Clash Hogs is a bot for **Clash of Clans**. It implements a few handy utilities for analysing clan data, and making clan management easier. 

 **The bot is not publicly hosted** as I do not have the resources to host the bot at scale. However, you can clone this repository and run a copy of your own bot, as long as you agree with the GPL v3 licence T&C. Alternatively, create a post under 'Issues' if you really want to use the bot but do not have the knowledge to run your own bot.

 - **Version**: internal deployment
 - **Status**: privately hosted only
 - **License**: GPL v3

## Running your own copy of this bot
Clash Hogs is written in Python 3.9. Follow the steps below.

 1. Create your own discord bot (a.k.a. discord app or application) and get your own bot token. You can find many online tutorials or video guides on this, such as https://discordjs.guide/preparations/setting-up-a-bot-application.html#creating-your-bot
 2. Continuing from step 1, select your discord app, under `OAuth2 > URL Generator`, in the `scopes` panel, select `bot` and `applications.commands`
 3. Step 2 will open another panel where you select the bot permissions. Choose at least `Send Messages, Embed Links, Attach Files, Read Message History, Use External Emojis`. This will generate an URL that you can copy and paste into any browser, and this will invite the bot to your discord server.
 4. Obtain your own Clash of Clans API account: https://developer.clashofclans.com/#/
 5. Clone this repository onto a machine that can run the bot 24/7 (ideally a server)
 6. Install required Python libraries on that machine (see the list at the end of this section)
 7. Navigate to `env` folder, change `template.config` to `env.config`, and edit the file to fill the required information such as the discord bot token, your CoC API authentication details etc.
 8. Host your bot by running the file `bot.py` under `src`, with one argument pointing to the `env.config` file above. E.g., '`python bot.py /path/to/env.confg`', modify this command depending on your folder structure.
 9. Use the URL generated in step 3 to invite the bot to your own discord server.

**Python libraries needed**
- coc.py 2.0.0
- disnake 2.4.0 
- matplotlib 3.5.1
- pandas 1.3.4
- sqlite 3.36.0 (should be built-in with Python 3.9)

## Using the bot 
Clash Hogs is documented through its `/help` command. I suggest you start with running the `/help command: show-all` to view all the commands available, and then type `/help command: [command-in-question]`for instructions on how to use that specific command.

**TBD** Future version of the bot will support a `/example` command that demonstrates each command.