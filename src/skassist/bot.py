import datetime
import logging
import pandas
import sys
import time
import traceback
from pathlib import Path
import discord
from discord.ext import commands
from skassist import database, sidekickparser, models, util
import coc
from coc import utils

##########
# Init   #
##########


# There must be a .env file within the same folder of this source file, and this needs to have the following two
# properties
if len(sys.argv) < 1:
    print("Please provide the file path to your .env file")
    exit(0)
properties = util.load_properties(sys.argv[1])
if 'DISCORD_TOKEN' not in properties.keys() or 'BOT_NAME' not in properties.keys() \
        or 'BOT_PREFIX' not in properties.keys() or 'CoC_API_EMAIL' not in properties.keys() \
        or 'CoC_API_PASS' not in properties.keys():
    print(
        "Some of the required properties are missing, please check you have the following properties in your .env file: "
        "\n\t{}\n\t{}\n\t{}\n\t{}\n\t{}".format("BOT_NAME", "BOT_PREFIX", "DISCORD_TOKEN",
                                                "CoC_API_EMAIL", "CoC_API_PASS"))
    exit(0)

coc_client = coc.login(
    properties["CoC_API_EMAIL"],
    properties["CoC_API_PASS"],
    key_names="Sidekick Assist v1",
    client=coc.EventsClient,
)

TOKEN = properties['DISCORD_TOKEN']
BOT_NAME = properties['BOT_NAME']
PREFIX = properties['BOT_PREFIX']

SIDEKICK_NAME = 'sidekick'
PERMISSION_WARDIGEST = 'developers'
PERMISSION_CLANDIGEST = 'developers'
BOT_WAIT_TIME = 5
bot = commands.Bot(command_prefix=PREFIX, help_command=None)

logging.basicConfig(stream=sys.stdout,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    level=logging.INFO,
                    datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger(BOT_NAME)


@bot.event
async def on_ready():
    log.info(f'{bot.user.name} has connected to Discord! (prefix: {PREFIX})')
    # register each connected guild to the bot database
    log.info('The following guilds are connected with the bot:')
    for guild in bot.guilds:
        database.guilds[guild.id] = guild.name
        log.info('\t{}, {}, checking databases...'.format(guild.name, guild.id))
        database.check_database(guild.id)


@bot.event
async def on_guild_join(guild):
    log.info('{} has been added to a new server: {}'.format(BOT_NAME, guild.id))
    log.info('\t{}, {}, checking databases...'.format(guild.name, guild.id))
    database.check_database(guild.id)


#########################################################
# Register the help command
#########################################################
@bot.command()
async def help(context, command=None):
    if command is None:
        await context.send(
            f'{BOT_NAME} supports the following commands. Run **{PREFIX}help [command]** for how to use them. Also see '
            'details at https://github.com/clashzz/sidekickassist:\n'
            '\t\t - **warmiss**: set up a channel for forwarding missed attacks\n'
            '\t\t - **wardigest**: analyse and produce a report for a clan\'s past war peformance\n'
            '\t\t - **clandigest**: analyse and produce a report for a clan\'s activities (excl. war)\n'
            '\t\t - **warpersonal**: analyse and produce a report for a player\'s past war performance\n'
            '\t\t - **warn**: manage warnings for a clan/player\n'
            '\t\t - **credit**: manage a clan members\' credits\n')
    elif command == 'warmiss':
        await context.send(
            'This command is used to map your sidekick war feed channel to another channel,'
            ' where missed attacks will be automatically tallied.\n'
            f'**Usage:** {PREFIX}warmiss [option] #sidekick-war #missed-attacks [clanname]\n'
            '\t\t - [option]: \n'
            '\t\t\t\t -l: to list current channel mappings (ignore other parameters when using this option)\n'
            '\t\t\t\t -a: to add a channel mapping\n'
            '\t\t\t\t -r: to remove a channel mapping:\n'
            '\t\t - [clanname] must be a single word\n'
            'All parameters must be a single word without space characters. The channels must have the # prefix')
    elif command == 'clandigest':
        await context.send(
            'This command is used to generate clan digest for the current season using data from the Sidekick clan '
            'feed channel. \n'
            f'**Usage**: {PREFIX}clandigest #sidekick-clan-feed-channel #output-target-channel [clanname]\n'
            '\t\t - [clanname] must be a single word\n\n'
            f'{BOT_NAME} must have read and write permissions to both channels.')
    elif command == 'wardigest':
        await context.send(
            'This command is used to generate clan war digest using data from the Sidekick clan war feed channel.\n'
            f'**Usage**: {PREFIX}wardigest #sidekick-war-feed-channel #output-target-channel [clanname] [dd/mm/yyyy] '
            '[OPTIONAL:dd/mm/yyyy]\n'
            '\t\t - [clanname]: must be one word\n'
            '\t\t - [dd/mm/yyyy]: the first is the start date (required), the second is the end date (optional). '
            'When the end date is not provided, the present date will be used\n\n'
            f'{BOT_NAME} must have read and write permissions to both channels.')
    elif command == 'warpersonal':
        await context.send(
            'This command is used to generate personal war analysis using data from the Sidekick clan war feed '
            'channel. You must have taken part in the wars to have any data for analysis.\n\n'
            f'**Usage**: {PREFIX}warpersonal [player_tag] [dd/mm/yyyy] [OPTIONAL:dd/mm/yyyy]\n'
            '\t\t - [player_tag] your player tag (must include #)\n'
            '\t\t - [dd/mm/yyyy] the first is the start date (required), the second is the end date (optional) for '
            'your data. When the end date is not provided, the present date will be used\n'
            'When the end date is not provided, the present date will be used\n\n'
            f'{BOT_NAME} must have read and write permissions to both channels.')
    elif command == 'warn':
        await context.send(
            'This command is used to manage warnings of players in a clan.\n'
            f'**Usage:** {PREFIX}warn [option] [clanname] [playername] [value] [note]\n'
            '- [option]: \n'
            '\t\t -l: to list all warnings of a clan, or a player in a clan (clanname is mandatory, other parameters can be ignored)\n'
            '\t\t -a: to add a warning for a player of a clan, and assign a value to that warning (all parameters mandatory except note, which can be multi-word but must be the last parameter)\n'
            '\t\t -c: to remove all warnings of a player in a clan (clanname and playername mandatory)\n'
            '\t\t -d: to delete a specific warning record. Supply the warning record ID as a value for [clanname]\n'
            '\nAll parameters (except [note]) must be a single word without space characters. [value] must be a number when provided')
    elif command == 'credit':
        default=""
        for k, v in database.credit_watch_activities.items():
            default+=k+"="+str(v)+" "
        await context.send(
            'This command is used to manage credits of a clan\'s members.\n'
            f'**Usage:** {PREFIX}credit [option] [clantag or playertag] [*value] [note]\n'
            '- [option]: \n'
            '\t\t -l: If [clantag] is supplied, only that clan will be shown. If you want to see all registered clans, use *, i.e.: credit -l *\n'
            '\t\t -a: to register a clan for credit watch. [clantag] is mandatory. Other multiple [value] parameters can specify the credit points and activities to be registered. '
            'If none provided, then: '
            f'*{default.strip()}*. '
            f'If you want to customise the values, provide them in the same format as above, each separated by a whitespace. Default values will be set when not provided in [*values]'
            '\n\t\t -d: to remove a clan from credit watch. [clantag is mandatory]\n')

    else:
        await context.send(f'Command {command} does not exist.')


#########################################################
# This method is used to configure the discord channels
# to automatically tally missed attacks
#########################################################
@bot.command(name='warmiss')
@commands.has_permissions(manage_guild=True)
async def warmiss(ctx, option: str, from_channel=None, to_channel=None, clan=None):
    log.info("GUILD={}, {}, ACTION=warmiss, arg={}".format(ctx.guild.id, ctx.guild.name, option))
    # list current mappings
    if option == "-l":
        mappings = database.get_warmiss_mappings_for_guild_db(ctx.guild.id)
        msg = "The follow channels are mapped for war missed attacks:\n"
        for m in mappings:
            fc = discord.utils.get(ctx.guild.channels, id=m[0])
            tc = discord.utils.get(ctx.guild.channels, id=m[1])
            clanname = m[2]
            msg += "\t\tFrom: **{}**,\tTo: **{}**,\t Clan: **{}**\n".format(fc.mention, tc.mention, clanname)
        await ctx.channel.send(msg)
        return

    # if other options, then the other three params are required
    if from_channel is None or to_channel is None or clan is None:
        await ctx.channel.send(f"'warmiss' requires arguments. Run {PREFIX}help warmiss for details")
        return

    # check if the channels already exist
    check_ok = True
    from_channel_id = sidekickparser.parse_channel_id(from_channel)
    to_channel_id = sidekickparser.parse_channel_id(to_channel)
    channel = discord.utils.get(ctx.guild.channels, id=from_channel_id)
    if channel is None:
        await ctx.channel.send(
            f"The channel {from_channel} does not exist. Please create it first, and give {BOT_NAME} "
            "'Send messages' and 'Read message history' permissions to that channel.")
        check_ok = False
    channel = discord.utils.get(ctx.guild.channels, id=to_channel_id)
    if channel is None:
        await ctx.channel.send(
            f"The channel {to_channel} does not exist. Please create it first, and give {BOT_NAME} "
            "'Send messages' and 'Read message history' permissions to that channel.")
        check_ok = False

    if not check_ok:
        return

    # checks complete, all good

    if option == "-a":  # adding a mapping
        pair = (from_channel_id, to_channel_id)
        database.add_channel_mappings_warmiss_db(pair, ctx.guild.id, clan)  # TODO
        await ctx.channel.send(
            "Okay. Missed attacks for **{}** from {} will be extracted and forwarded to {}. Please ensure {} has "
            "access to these channels (read and write)".format(clan, from_channel, to_channel, BOT_NAME))

    if option == "-r":  # remove a channel
        database.remove_warmiss_mappings_for_guild_db(ctx.guild.id, from_channel_id)
        await ctx.channel.send(
            "Mapping removed")


@warmiss.error
async def warmiss_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(f"'warmiss' requires arguments. Run {PREFIX}help warmiss for details")
    elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole):
        await ctx.channel.send(
            "Users of 'warmiss' must have 'Manage server' permission. You do not seem to have permission to use this "
            "command")
    else:
        # traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        error = ''.join(traceback.format_stack())
        log.error("GUILD={}, {}, ACTION=warmiss\n{}".format(ctx.guild.id, ctx.guild.name, error))


#########################################################
# This method is used to process clan log summary
#########################################################
@bot.command(name='clandigest')
# @commands.has_role('developers')
async def clandigest(ctx, from_channel: str, to_channel: str, clanname: str):
    log.info("GUILD={}, {}, ACTION=clandigest".format(ctx.guild.id, ctx.guild.name))
    # check if the channels already exist
    check_ok = True
    from_channel_id = sidekickparser.parse_channel_id(from_channel)
    if from_channel_id == -1:
        await ctx.channel.send(
            "You must pass a channel for the first argument")
        check_ok = False
    else:
        channel_from = discord.utils.get(ctx.guild.channels, id=from_channel_id)
        if channel_from is None:
            await ctx.channel.send(
                "The channel {} does not exist. This should be your sidekick clan feed channel, and allows 'Read "
                "message history' and 'Send messages' permissions for {}.".format(from_channel, BOT_NAME))
            check_ok = False

    to_channel_id = sidekickparser.parse_channel_id(to_channel)
    if to_channel_id == -1:
        await ctx.channel.send(
            "You must pass a channel for the second argument")
        check_ok = False
    else:
        channel_to = discord.utils.get(ctx.guild.channels, id=to_channel_id)
        if channel_to is None:
            await ctx.channel.send(
                "The channel {} does not exist. Please create it first, and give {} 'Send messages'"
                " permissions to that channel.".format(to_channel, BOT_NAME))
            check_ok = False

    if not check_ok:
        return

    # start_time=datetime.datetime.now() -datetime.timedelta(seconds=BOT_WAIT_TIME)
    messages = await channel_from.history(limit=20, oldest_first=False).flatten()
    messages.reverse()
    data_clanbest, season_id, sidekick_messages = sidekickparser.parse_clan_best(messages)
    if len(data_clanbest) == 0:
        msg = "Could not find required data in your clan feed channel. Did you run Sidekick's '/best' command immediately before this?"
        await channel_to.send(msg)
    else:
        date_season_start = sidekickparser.parse_season_start(season_id)
        messages = await channel_from.history(after=date_season_start, limit=None).flatten()
        data_clanactivity = sidekickparser.parse_clan_activity(messages)

        msg = "{} clan feed digest - {}:\n\n **Loots and Attacks:**".format(clanname, season_id.replace("\n", " "))
        for k, v in data_clanbest.items():
            msg += "\t" + k + ": " + str(v) + "\n"
        await channel_to.send(msg + "\n")

        msg = "**Member Activity Counts** (upgrade completes, league promotion, super troop boosts etc):\n"
        if len(data_clanactivity) > 0:
            for k, v in data_clanactivity.items():
                msg += "\t" + k + ": " + str(v) + "\n"
            await channel_to.send(msg + "\n")
        else:
            msg += "\t Empty. Your sidekick /best command must be run in the configured clan feed channel. The " \
                   "source channel you provided does not contain this data."
            await channel_to.send(msg + "\n")


@clandigest.error
async def clandigest(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(f"'clandigest' requires three arguments. Run {PREFIX}help clandigest for details")
    elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole):
        await ctx.channel.send(
            "'clandigest' can only be used by the {} role(s). You do not seem to have permission to use this command".format(
                PERMISSION_CLANDIGEST))
    else:
        # traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        error = ''.join(traceback.format_stack())
        log.error("GUILD={}, {}, ACTION=clandigest\n{}".format(ctx.guild.id, ctx.guild.name, error))
        traceback.print_stack()


#########################################################
# This method is used to process clan war summary
#########################################################
@bot.command(name='wardigest')
async def wardigest(ctx, from_channel: str, to_channel: str, clanname: str, fromdate: str, todate=None):
    log.info("GUILD={}, {}, ACTION=wardigest".format(ctx.guild.id, ctx.guild.name))

    # check if the channels already exist
    check_ok = True
    from_channel_id = sidekickparser.parse_channel_id(from_channel)
    to_channel_id = sidekickparser.parse_channel_id(to_channel)
    channel_from = discord.utils.get(ctx.guild.channels, id=from_channel_id)
    if channel_from is None:
        await ctx.channel.send(
            "The channel {} does not exist. This should be your sidekick war feed channel, and allows 'Read message history'"
            " and 'Send messages' permissions for {}.".format(from_channel, BOT_NAME))
        check_ok = False
    channel_to = discord.utils.get(ctx.guild.channels, id=to_channel_id)
    if channel_to is None:
        await ctx.channel.send(
            "The channel {} does not exist. Please create it first, and give {} 'Send messages'"
            " permissions to that channel.".format(to_channel, BOT_NAME))
        check_ok = False

    if not check_ok:
        return

    try:
        fromdate = datetime.datetime.strptime(fromdate, "%d/%m/%Y")
    except:
        fromdate = datetime.datetime.now() - datetime.timedelta(30)
        await ctx.channel.send(
            "The start date you specified does not confirm to the required format dd/mm/yyyy. The date 30 days ago from today"
            " will be used instead.".format(to_channel, BOT_NAME))
    try:
        if todate is not None:
            todate = datetime.datetime.strptime(todate, "%d/%m/%Y")
        else:
            todate = datetime.datetime.now()
            await ctx.channel.send(
                "End date not provided, using today's date as the end date")

    except:
        todate = datetime.datetime.now()
        await ctx.channel.send(
            "The end date you specified does not confirm to the required format dd/mm/yyyy. The current date"
            " will be used instead.".format(to_channel, BOT_NAME))

    delta = todate - fromdate
    if delta.days > 60:
        await ctx.channel.send(
            "Fetching data covering more than 60 days is not recommended as this leads to slow response"
            " time. If you wish to analyse historical data, set your start and end dates accordingly.")
        return

    await ctx.channel.send(
        "This may take a few seconds while I retrieve data from Sidekick. Historical data may take longer, please be patient...")

    # gather missed attacks data
    messages = await channel_from.history(after=fromdate, before=todate, limit=None).flatten()
    data_missed = sidekickparser.parse_warfeed_missed_attacks(messages, SIDEKICK_NAME)

    messages_with_export_data = await channel_from.history(before=datetime.datetime.now(), limit=1).flatten()
    msg = "**{} clan war digest between {} and {}**:\n\n **Missed Attacks:** \n".format(clanname, fromdate, todate)
    for k, v in data_missed.items():
        msg += "\t" + k + ": " + str(v) + "\n"
    await channel_to.send(msg + "\n")

    # gather war data
    last_message = messages_with_export_data[0]
    if str(last_message.attachments) == "[]":  # Checks if there is an attachment on the message
        await ctx.channel.send("Cannot find the Sidekick war data export in the {} channel. Run **/export ...** "
                               "in that channel first and ensure no other messages are posted before you run this command.".format(
            from_channel))
    else:  # If there is it gets the filename from message.attachments
        clanid = str(ctx.guild.id)
        targetfolder = "db/" + clanid
        Path(targetfolder).mkdir(parents=True, exist_ok=True)
        split_v1 = str(last_message.attachments).split("filename='")[1]
        filename = targetfolder + "/" + str(split_v1).split("' ")[0]
        if filename.endswith(".csv"):  # Checks if it is a .csv file
            await last_message.attachments[0].save(fp=filename)  # saves the file
        # now process the file and extract data
        clan_war_data = sidekickparser.parse_sidekick_war_data_export(filename, clanname, fromdate, data_missed)
        data_for_plot, clan_summary = clan_war_data.output_clan_war_data(targetfolder)
        msg = "\n**Clan Overview**:\n"
        for k, v in clan_summary.items():
            msg += "\t" + k + ": " + str(v) + "\n"
        await channel_to.send(msg + "\n")

        figure = data_for_plot.plot(kind='bar', stacked=True).get_figure()
        figure.savefig(targetfolder + '/clan_war_data.jpg', format='jpg')
        # now fetch that file and send it to the channel
        fileA = discord.File(targetfolder + "/clan_war_data.csv")
        await channel_to.send(file=fileA, content="**Clan war data analysis ready for download**:")
        fileB = discord.File(targetfolder + "/clan_war_data.jpg")
        await channel_to.send(file=fileB,
                              content="**Clan war data plot ready for download**:")

        # save individual war data
        log.info("GUILD={}, {}, ACTION=wardigst\n\t\tsaving war data for individuals...".format(ctx.guild.id,
                                                                                                ctx.guild.name))
        database.save_individual_war_data(ctx.guild.id, clan_war_data)
        log.info("GUILD={}, {}, ACTION=wardigst\n\t\tsaving war data for individuals COMPLETE...".format(ctx.guild.id,
                                                                                                         ctx.guild.name))

    await ctx.channel.send("Done. Please see your target channel for the output. ")


@wardigest.error
async def wardigest(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(f"'wardigest' requires four arguments. Run {PREFIX}help wardigest for details")
    elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole):
        await ctx.channel.send(
            "'wardigest' can only be used by the {} role(s). You do not seem to have permission to use this command".format(
                PERMISSION_CLANDIGEST))
    else:
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        error = ''.join(traceback.format_stack())
        log.error("GUILD={}, {}, ACTION=wardigest\n{}".format(ctx.guild.id, ctx.guild.name, error))


#########################################################
# This method is used to produce personal war summary
#########################################################
@bot.command(name='warpersonal')
async def warpersonal(ctx, playertag: str, fromdate: str, todate=None):
    # check if the channels already exist
    try:
        fromdate = datetime.datetime.strptime(fromdate, "%d/%m/%Y")
    except:
        fromdate = datetime.datetime.now() - datetime.timedelta(30)
        await ctx.channel.send(
            "The start date you specified does not conform to the required format dd/mm/yyyy. The date 30 days ago from today"
            " will be used instead.".format(ctx.channel, BOT_NAME))
    try:
        if todate is not None:
            todate = datetime.datetime.strptime(todate, "%d/%m/%Y")
        else:
            todate = datetime.datetime.now()
    except:
        todate = datetime.datetime.now()
        await ctx.channel.send(
            "The end date you specified does not confirm to the required format dd/mm/yyyy. The current date"
            " will be used instead.".format(ctx.channel, BOT_NAME))

    await ctx.channel.send("This may take a few seconds while I retrieve data from Sidekick...")

    # gather personal war data
    war_data = database.load_individual_war_data(ctx.guild.id, playertag, fromdate, todate)
    if len(war_data) < 5:
        await ctx.channel.send(
            "There are not enough war data for {} with a total of {} attacks in our database. Run the command with a wider timespan or try this later "
            "when you have warred more with us.".format(ctx.channel, BOT_NAME))
        return

    player = models.Player(playertag, playertag)
    player._attacks = war_data
    player.summarize_attacks()

    # attack stars by town hall
    data_as_list, row_index, header = models.summarise_by_townhalls(player._thlvl_attacks, player._thlvl_stars)
    data_for_plot = pandas.DataFrame(data_as_list, columns=header, index=row_index)
    targetfolder = "db/"
    Path(targetfolder).mkdir(parents=True, exist_ok=True)
    figure = data_for_plot.plot(kind='bar', stacked=True).get_figure()
    file = targetfolder + '/{}_byth.jpg'.format(playertag.replace('#', '_'))
    figure.savefig(file, format='jpg')
    fileA = discord.File(file)
    await ctx.channel.send("Data for **{}**, between **{}** and **{}**".format(playertag, fromdate, todate))
    await ctx.channel.send(file=fileA, content="**Attack stars by target town hall levels**:")

    # attack stars by time
    dataframe = models.summarise_by_months(player._attacks)
    figure = dataframe.plot(kind='bar', rot=0).get_figure()
    file = targetfolder + '/{}_bytime.jpg'.format(playertag.replace('#', '_'))
    figure.savefig(file, format='jpg')
    fileB = discord.File(file)
    await ctx.channel.send(file=fileB, content="**Attack stars by time**:")


@warpersonal.error
async def warpersonal(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(f"'warpersonal' requires four arguments. Run {PREFIX}help warpersonal for details")
    elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole):
        await ctx.channel.send(
            f"'wardigest' can only be used by the {PERMISSION_CLANDIGEST} role(s). You do not seem to have permission "
            "to use this command")
    else:
        # traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        error = ''.join(traceback.format_stack())
        log.error(f"GUILD={ctx.guild.id}, {ctx.guild.name}, ACTION=warpersonal\n{error}")


#########################################################
# This method is used to log warnings
#########################################################
@bot.command(name='warn')
@commands.has_permissions(manage_guild=True)
async def warn(ctx, option: str, clan: str, name=None, value=None, *note):
    log.info("GUILD={}, {}, ACTION=warn, arg={}".format(ctx.guild.id, ctx.guild.name, option))

    # list current warnings
    if option == "-l":
        if name is None:  # list all warnings of a clan
            res = database.list_warnings(ctx.guild.id, clan)
            await ctx.send(embed=util.format_warnings(clan, res))
            # await ctx.channel.send("The clan {} has a total of {} warnings:\n{}".format(clan, len(res), string))
            return
        else:  # list all warnings of a person in a clan
            res = database.list_warnings(ctx.guild.id, clan, name)
            await ctx.send(embed=util.format_warnings(clan, res, name))

    # add a warning
    if option == "-a":
        if name is None or value is None:
            await ctx.channel.send(
                f"'warn' requires 4~5 arguments for adding a warning. Run '{PREFIX}help warn' for details")
            return
        try:
            value = float(value)
        except:
            await ctx.channel.send("The value you entered for this warning does not look like a number, try agian.")
            return
        database.add_warning(ctx.guild.id, clan, name, value, note)
        await ctx.channel.send("Warning added for {} from the {} clan.".format(name, clan))
        return

    # clear all warnings with a person
    if option == "-c":
        if name is None:
            await ctx.channel.send(
                f"'warn' requires 4 arguments for clearing  warnings. Run '{PREFIX}help warn' for details")
            return
        database.clear_warnings(ctx.guild.id, clan, name)
        await ctx.channel.send("All warnings for {} from the {} clan are deleted.".format(name, clan))
        return
        # delete a warning
    if option == "-d":
        database.delete_warning(ctx.guild.id, clan)
        await ctx.channel.send("The warning with the ID {} has been deleted".format(clan))


@warn.error
async def warn_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(f"'warn' requires arguments. Run '{PREFIX}help warn' for details")
    elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole):
        await ctx.channel.send(
            "Users of 'warn' must have 'Manage server' permission. You do not seem to have permission to use this "
            "command")
    else:
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        error = ''.join(traceback.format_stack())
        log.error("GUILD={}, {}, ACTION=warn\n{}".format(ctx.guild.id, ctx.guild.name, error))


#########################################################
# This method is used to set up clan credit watch system
#########################################################
@bot.command(name='credit')
@commands.has_permissions(manage_guild=True)
async def credit(ctx, option: str, tag: str, *values):
    tag=util.normalise_tag(tag)

    log.info("GUILD={}, {}, ACTION=credit, arg={}".format(ctx.guild.id, ctx.guild.name, option))

    # list current registered clans
    if option == "-l":
        res = database.list_registered_clans(ctx.guild.id,tag)
        await ctx.send(embed=util.format_credit_systems(res))
        return

    # register a clan
    if option == "-a":
        try:
            clan = await coc_client.get_clan(tag)
        except coc.NotFound:
            await ctx.send("This clan doesn't exist.")
            return

        #2YGUPUU82, #2998V8JG0, #2L29RRJU9, #2PYQOV822
        result=database.registered_clan(ctx.guild.id, tag, clan.name, values)
        if len(result)!=0:
            await ctx.channel.send("Update for the clan {} has been unsuccessful. The parameters you provided maybe invalid, try again: {}".
                                   format(clan, result))
        else:
            coc_client.add_clan_updates(tag)
            await ctx.channel.send("The clan {} has been updated for the credit watch system.".format(tag))
        return

    # delete a clan
    if option == "-d":
        try:
            clan = await coc_client.get_clan(tag)
        except coc.NotFound:
            await ctx.send("This clan doesn't exist.")
            return
        database.remove_registered_clan(ctx.guild.id, tag)
        coc_client.remove_clan_updates(tag)
        await ctx.channel.send("The clan {} has been removed from the credit watch system.".format(tag))
        return

@credit.error
async def credit_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(f"'credit' requires arguments. Run '{PREFIX}help credit' for details")
    elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole):
        await ctx.channel.send(
            "Users of 'credit' must have 'Manage server' permission. You do not seem to have permission to use this "
            "command")
    else:
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


###################################################################
# This method is used to monitor to messages posted on the server, intercepts sidekick war feed,
# extracts missed attacks, and post those data to a specific channel
# see also the 'config' command
###################################################################
@bot.event
async def on_message(message):
    if SIDEKICK_NAME in message.author.name.lower() or message.content.startswith('TEST '):
        # sidekick posted a message, let's check if it is war feed
        try:
            if database.has_warmiss_fromchannel(message.guild.id, message.channel.id):
                # we captured a message from the sidekick war feed channel. Now check if it is about missed attackes
                if 'lost the war' in message.content.lower() or 'won the war' in message.content.lower():
                    log.info("GUILD={},{}, captured war end messages...".format(message.guild.id, message.guild.name))
                    time.sleep(BOT_WAIT_TIME)
                    # print("\t waiting done")

                    messages = await message.channel.history(limit=10, oldest_first=False).flatten()
                    messages.reverse()
                    missed_attacks = sidekickparser.parse_warfeed_missed_attacks(messages)

                    log.info(
                        "GUILD={},{}, prepared war miss message, total={} war miss messages...".format(message.guild.id,
                                                                                                       message.guild.name,
                                                                                                       len(missed_attacks)))
                    to_channel, clan = database.get_warmiss_tochannel(message.guild.id, message.channel.id)
                    to_channel = discord.utils.get(message.guild.channels, id=to_channel)

                    message = "War missed attack for **{} on {}**:\n" \
                              "(Double check your in-game data, Sidekick can lose attacks made in the last minutes)\n".format(
                        clan, datetime.datetime.now())

                    if len(missed_attacks) == 0:
                        message += "\tNone, everyone attacked!"
                    else:
                        for k, v in missed_attacks.items():
                            message += "\t" + str(k) + "\t" + str(v) + "\n"
                    await to_channel.send(message)
            else:
                log.info(
                    "GUILD={},{}, captured Sidekick message from warfeed channel, does not contain war end...".format(
                        message.guild.id,
                        message.guild.name))
                return
        except:
            error = ''.join(traceback.format_stack())
            log.error("GUILD={}, {}, ACTION=on_message\n{}".format(message.guild.id, message.guild.name, error))
    elif message.clean_content.strip().startswith(PREFIX):
        await bot.process_commands(message)


bot.run(TOKEN)
