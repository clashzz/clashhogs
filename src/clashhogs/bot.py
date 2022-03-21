import datetime, disnake, pandas, sys, traceback, coc, logging, asyncio, operator
import matplotlib.pyplot as plt
from pathlib import Path
from clashhogs import database, dataformatter, models, util
from coc import utils
from disnake.ext import commands
from disnake.ext import tasks

######################################
# Init                               #
######################################
# DSN=802849247179309067
# Dev=880595096461004830

# There must be a env.config file within the same folder of this source file, and this needs to have the following two
# properties
if len(sys.argv) < 1:
    print("Please provide the path to the folder containing your .env file")
    exit(0)
rootfolder = sys.argv[1]
if not rootfolder.endswith("/"):
    rootfolder += "/"
properties = util.load_properties(rootfolder + "env.config")
if 'DISCORD_TOKEN' not in properties.keys() or 'BOT_NAME' not in properties.keys() \
        or 'BOT_PREFIX' not in properties.keys() or 'CoC_API_EMAIL' not in properties.keys() \
        or 'CoC_API_PASS' not in properties.keys():
    print(
        "Some of the required properties are missing, please check you have the following properties in your .env file: "
        "\n\t{}\n\t{}\n\t{}\n\t{}\n\t{}".format("BOT_NAME", "BOT_PREFIX", "DISCORD_TOKEN",
                                                "CoC_API_EMAIL", "CoC_API_PASS"))
    exit(0)

# CoC.py api client object
coc_client = coc.login(
    properties["CoC_API_EMAIL"],
    properties["CoC_API_PASS"],
    key_names="Clash Hogs",
    client=coc.EventsClient,
)

# Bot information and properties
TOKEN = properties['DISCORD_TOKEN']
BOT_NAME = properties['BOT_NAME']
PREFIX = properties['BOT_PREFIX']
DESCRIPTION = "A utility bot for Clash of Clans clan management"
intents = disnake.Intents.all()
bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(PREFIX), help_command=None, description=DESCRIPTION, intents=intents,
    test_guilds=[880595096461004830, 802849247179309067],
    sync_commands_debug=True
)

# logging
logging.basicConfig(stream=sys.stdout,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    level=logging.INFO,
                    datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger(BOT_NAME)


##################################################
# Bot events
##################################################
@bot.event
async def on_ready():
    # check if master database exists
    database.check_master_database()
    # register clans for coc event watch
    log.info('The following clans are linked with the bot:')
    for clan in database.init_clanwatch_all():
        coc_client.add_war_updates(clan._tag)
        coc_client.add_clan_updates(clan._tag)
        log.info("\t{}, {}, guild={}, {}".format(clan._tag, clan._name, clan._guildid, clan._guildname))
        # coc_client.add_war_updates(clan._tag)

    log.info('The following guilds are linked with the bot:')
    for guild in bot.guilds:
        log.info('\t{}, {}, checking databases...'.format(guild.name, guild.id))
        database.check_database(guild.id, rootfolder)
    log.info('Init completed')
    # print("debugging")
    # coc_client.add_war_updates("#2YGUPUU82")
    # coc_client.add_clan_updates("#2YGUPUU82")


@bot.event
async def on_guild_join(guild):
    log.info('{} has been added to a new server: {}'.format(BOT_NAME, guild.id))
    log.info('\t{}, {}, checking databases...'.format(guild.name, guild.id))
    database.check_database(guild.id, rootfolder)


#########################################################
# Register the help command
#########################################################
@bot.slash_command(description="Show the list of commands and a summary of their functions.")
async def help(inter, command: str = commands.Param(choices={"show-all": "all",
                                                             "link": "link",
                                                             "channel": "channel",
                                                             "clanwar": "clanwar",
                                                             "mywar": "mywar",
                                                             "warn": "warn",
                                                             "crclan": "crclan",
                                                             "crplayer": "crplayer",
                                                             "mycredit": "mycredit"})):
    if command == 'all':
        await inter.response.send_message(
            util.prepare_help_menu(BOT_NAME, PREFIX))
    elif command == 'link':
        await inter.response.send_message(util.prepare_link_help(PREFIX))
    elif command == 'channel':
        await inter.response.send_message(util.prepare_channel_help(PREFIX))
    elif command == 'clanwar':
        await inter.response.send_message(
            util.prepare_clanwar_help(PREFIX))
    elif command == 'mywar':
        await inter.response.send_message(
            util.prepare_mywar_help(PREFIX))
    elif command == 'warn':
        await inter.response.send_message(util.prepare_warn_help(PREFIX))
    elif command == 'crclan':
        await inter.response.send_message(util.prepare_crclan_help(PREFIX, models.STANDARD_CREDITS))
    elif command == 'crplayer':
        await inter.response.send_message(util.prepare_crplayer_help(PREFIX))
    elif command == 'mycredit':
        await inter.response.send_message(util.prepare_mycredit_help(PREFIX))
    else:
        await inter.response.send_message(f'Command {command} does not exist.')


#########################################################
# This method is used to configure the discord channels
# to automatically tally missed attacks
#########################################################
@bot.slash_command(description="Link a clan to this discord server (requires admin access).")
@commands.has_permissions(manage_guild=True)
async def link(inter, option: str = commands.Param(choices={"add": "-a",
                                                            "list (clan tag not required)": "-l",
                                                            "remove": "-r"}), clantag: str = None):
    log.info(
        "GUILD={}, {}, ACTION=link, OPTION={}, user={}".format(inter.guild.id, inter.guild.name, option, inter.author))

    if clantag is not None:
        clantag = utils.correct_tag(clantag)
        try:
            clan = await coc_client.get_clan(clantag)
        except coc.NotFound:
            await inter.response.send_message("This clan doesn't exist.")
            return

    if option == '-a':
        if clantag is None:
            await inter.response.send_message("Clan tag required.")
            return

        desc = clan.description
        if desc is None:
            desc = ""
        if not desc.lower().endswith("ch22"):
            await inter.response.send_message(
                "Authentication failed. Please add 'CH22' to the end of your clan description. This is only "
                "needed once to verify you are the owner of the clan. Each clan can only be linked to one "
                "discord server.")
            return

        clanwatch = database.get_clanwatch(clantag)
        if clanwatch is None:
            clanwatch = models.ClanWatch(clantag, clan.name, inter.guild.id, inter.guild.name)
        else:
            clanwatch.clear()
            clanwatch._tag = clantag
            clanwatch._name = clan.name
            clanwatch._guildid = inter.guild.id
            clanwatch._guildname = inter.guild.name
        database.add_clanwatch(clantag, clanwatch)
        coc_client.add_war_updates(clantag)
        coc_client.add_clan_updates(clantag)
        await inter.response.send_message(
            "Clan linked to this discord server. You will need to re-add all the channel mappings for this clan.")
    elif option == '-l':
        if clantag is None:
            clanwatches = database.get_clanwatch_all()
            if len(clanwatches) == 0:
                await inter.response.send_message("No clans have been linked to this discord server.")
            else:
                embed_list = []
                for cw in clanwatches:
                    embed_list.append(dataformatter.format_clanwatch_data(cw))
                await inter.response.send_message(embeds=embed_list)
            return

        clanwatch = database.get_clanwatch(clantag)
        await inter.response.send_message(embed=dataformatter.format_clanwatch_data(clanwatch))
        return
    elif option == '-r':
        if clantag is None:
            await inter.response.send_message("Clan tag must be provided")
            return
        database.remove_clanwatch(clantag)
        coc_client.remove_war_updates(clantag)
        await inter.response.send_message("Clan {} has been unlinked from this discord server.".format(clantag))
        return
    else:
        await inter.response.send_message("Option {} not supported. Run help for details.".format(option))


@link.error
async def link_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(f"'link' requires arguments. Run {PREFIX}help link for details")
    elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole):
        await ctx.channel.send(
            "Users of 'link' must have 'Manage server' permission. You do not seem to have permission to use this "
            "command")
    else:
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


#########################################################
# This method is used to set up the discord channels
# for war missed attacks, clan summary and war summary feeds
#########################################################
@bot.slash_command(
    description="Set up channels for a clan's feeds (clan must be already linked to this discord server).")
@commands.has_permissions(manage_guild=True)
async def channel(inter, clantag, to_channel, option: str = commands.Param(choices={"war-monthly": "-war",
                                                                                    "missed-attacks": "-miss"})):
    clantag = utils.correct_tag(clantag)
    log.info(
        "GUILD={}, {}, ACTION=channel, arg={}, user={}".format(inter.guild.id, inter.guild.name, option, inter.author))
    # list current mappings
    try:
        clan = await coc_client.get_clan(clantag)
        clanwatch = database.get_clanwatch(clantag)
        if clanwatch is None:
            await inter.response.send_message("This clan has not been linked to this discord server. Run 'link' first.")
            return
    except coc.NotFound:
        await inter.response.send_message("This clan '{}' doesn't exist.".format(clan))
        return

    to_channel_id = dataformatter.parse_channel_id(to_channel)
    channel = disnake.utils.get(inter.guild.channels, id=to_channel_id)
    if channel is None:
        await inter.response.send_message(
            f"The channel {to_channel} does not exist. Please create it first, and give {BOT_NAME} "
            "'Send messages' permission to that channel.")
        return

    if option == "-miss":
        clanwatch._channel_warmiss = to_channel
        database.add_clanwatch(clantag, clanwatch)
        await inter.response.send_message("War missed attack channel has been added for this clan. Please make sure "
                                          f"{BOT_NAME} has 'Send messages' permission to that channel, or this will not work.")
    elif option == "-war":
        clanwatch._channel_warsummary = to_channel
        database.add_clanwatch(clantag, clanwatch)
        await inter.response.send_message("War summary channel has been added for this clan. Please make sure "
                                          f"{BOT_NAME} has 'Send messages' permission to that channel, or this will not work.")
    # elif option == "-feed":
    #     clanwatch._channel_clansummary=to_channel
    #     database.add_clanwatch(clantag, clanwatch)
    #     await ctx.send("Clan feed summary channel has been added for this clan. Please make sure "
    #                    f"{BOT_NAME} has 'Send messages' permission to that channel, or this will not work.")
    else:
        await inter.response.send_message(
            "Option {} is not supported. Use miss/feed/war. Run help for details.".format(option))
        return


@channel.error
async def channel_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(f"'channel' requires arguments. Run {PREFIX}help channel for details")
    elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole):
        await ctx.channel.send(
            "Users of 'channel' must have 'Manage server' permission. You do not seem to have permission to use this "
            "command")
    else:
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


#########################################################
# This method is used to process clan war summary
#########################################################
@bot.slash_command(
    description="Product a summary of war performance for a clan that is linked with this discord server")
@commands.has_permissions(manage_guild=True)
async def clanwar(inter, clantag: str, from_date: str, to_date=None):
    clantag = utils.correct_tag(clantag)
    log.info("GUILD={}, {}, ACTION=clanwar, user={}".format(inter.guild.id, inter.guild.name, inter.author))

    try:
        clan = await coc_client.get_clan(clantag)
        clanwatch = database.get_clanwatch(clantag)
        if clanwatch is None:
            await inter.response.send_message("This clan has not been linked to this discord server. Run 'link' first.")
            return
    except coc.NotFound:
        await inter.response.send_message("This clan tag '{}' doesn't exist.".format(clantag))
        return

    to_channel_id = dataformatter.parse_channel_id(clanwatch._channel_warsummary)
    if to_channel_id == -1:
        await inter.response.send_message(
            "The channel for war digest has not been set. Run '/channel' to set this up first.")
        return
    else:
        channel_to = disnake.utils.get(inter.guild.channels, id=to_channel_id)
        if channel_to is None:
            await inter.response.send_message(
                "The target channel does not exist. Please check your setting using /link")
            return
        try:
            from_date = datetime.datetime.strptime(from_date, "%d/%m/%Y")
        except:
            from_date = datetime.datetime.now() - datetime.timedelta(30)
            await inter.response.send_message(
                "The date you specified does not confirm to the required format dd/mm/yyyy. The date 30 days ago from today"
                " will be used instead.")
            return
        try:
            if to_date is not None:
                to_date = datetime.datetime.strptime(to_date, "%d/%m/%Y")
            else:
                to_date = datetime.datetime.now()
                await inter.channel.send(
                    "End date not provided, using today's date as the end date")
        except:
            to_date = datetime.datetime.now()
            await inter.response.send_message(
                "The date you specified does not confirm to the required format dd/mm/yyyy. The current date"
                " will be used instead.")
            return

        war_miss, cwl_miss, war_overview, war_plot = send_wardigest(from_date, to_date, clantag, clanwatch._name)
        if war_miss is None or cwl_miss is None or war_overview is None or war_plot is None:
            await channel_to.send("Not enough war data for {}, {}".format(clantag, clanwatch._name))
            return

        await channel_to.send(war_miss)
        await channel_to.send(cwl_miss)
        await channel_to.send(war_overview)
        await channel_to.send(file=war_plot,
                              content="**Clan war data plot ready for download**:")

    await inter.response.send_message("Done. Please see your target channel for the output. ")


@clanwar.error
async def clanwar_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(f"'clanwar' requires four arguments. Run {PREFIX}help clanwar for details")
    elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole):
        await ctx.channel.send(
            "Users of 'clanwar' must have 'Manage server' permission. You do not seem to have permission to use this "
            "command")
    else:
        await ctx.channel.send(
            "Looks like I can't send messages to the target channel. Did you give me 'Send Message' and "
            "'Attach Files' permission? "
            "Run '/link list' to check the target channel you have set up for this clan.")
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


#########################################################
# This method is used to log warnings
#########################################################
@bot.slash_command(description='Add a warning record to a member of a clan')
@commands.has_permissions(manage_guild=True)
async def warn(inter, clan: str, option: str = commands.Param(choices={"list": "-l",
                                                                       "add": "-a",
                                                                       "clear": "-c",
                                                                       "delete": "-d"}), name=None, value=None, **note):
    log.info(
        "GUILD={}, {}, ACTION=warn, arg={}, user={}".format(inter.guild.id, inter.guild.name, option, inter.author))

    # list current warnings
    # todo: change warning records - first as header, rest as records
    if option == "-l":
        if name is None:  # list all warnings of a clan
            res = database.list_warnings(inter.guild.id, clan)
            warnings = dataformatter.format_warnings(clan, res)
            for w in warnings:
                await inter.channel.send(w)
        else:  # list all warnings of a person in a clan
            res = database.list_warnings(inter.guild.id, clan, name)
            warnings = dataformatter.format_warnings(clan, res, name)
            for w in warnings:
                await inter.channel.send(w)

        await inter.response.send_message("See data below")
        return
    # add a warning
    elif option == "-a":
        if name is None or value is None:
            await inter.response.send_message(
                f"'warn' requires 4~5 arguments for adding a warning. Run '{PREFIX}help warn' for details")
            return
        try:
            value = float(value)
        except:
            await inter.response.send_message(
                "The value you entered for this warning does not look like a number, try agian.")
            return
        database.add_warning(inter.guild.id, clan, name, value, note)
        await inter.response.send_message("Warning added for {} from the {} clan.".format(name, clan))
        return
    # clear all warnings with a person
    elif option == "-c":
        if name is None:
            await inter.response.send_message(
                f"'warn' requires 4 arguments for clearing  warnings. Run '{PREFIX}help warn' for details")
            return
        database.clear_warnings(inter.guild.id, clan, name)
        await inter.response.send_message("All warnings for {} from the {} clan are deleted.".format(name, clan))
        return
        # delete a warning
    elif option == "-d":
        deleted = database.delete_warning(inter.guild.id, clan, name)
        if deleted:
            await inter.response.send_message("The warning record(s) has/have been deleted".format(clan))
        else:
            await inter.response.send_message(
                "Operation failed. Perhaps the warning ID {} and the clan name {} do not match what's in the database."
                " If you are providing a date, it must conform to the YYYY-MM-DD format.".format(name, clan))
        return
    else:
        await inter.response.send_message("Option {} not supported. Run help for details.".format(option))
        return


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


#########################################################
# This method is used to set up clan credit watch system
#########################################################
@bot.slash_command(description='Set up credit points for a clan')
@commands.has_permissions(manage_guild=True)
async def crclan(inter, tag: str, option: str = commands.Param(choices={"list": "-l",
                                                                      "update": "-u",
                                                                      "clear": "-c"}), *values):
    if tag != '*':
        tag = utils.correct_tag(tag)
    log.info("GUILD={}, {}, ACTION=crclan, arg={}, user={}".format(inter.guild.id, inter.guild.name, option, inter.author))

    # list current registered clans
    if option == "-l":
        if tag == "*":
            res = database.get_clanwatch_by_guild(str(inter.guild.id))
        else:
            res = [database.get_clanwatch(tag, str(inter.guild.id))]
        await inter.response.send_message(embed=dataformatter.format_credit_systems(res))
        return
    # register a clan
    elif option == "-u":
        try:
            clan = await coc_client.get_clan(tag)
        except coc.NotFound:
            await inter.response.send_message("This clan doesn't exist.")
            return

        result = database.registered_clan_creditwatch(inter.guild.id, tag, values)
        if result is None:
            await inter.response.send_message(
                "The clan {} has not been linked to this discord server. Run 'link' first.".format(tag))
            return
        if len(result) != 0:
            await inter.response.send_message(
                "Update for the clan {} has been unsuccessful. The parameters you provided maybe invalid, try again: {}".
                format(clan, result))
        else:
            coc_client.add_war_updates(tag)
            await inter.response.send_message("The clan {} has been updated for the credit watch system.".format(tag))
        return
    # clear all records of a clan
    elif option == "-c":
        def check(msg):
            return msg.author == inter.author and msg.channel == inter.channel and \
                   msg.content in ["YES", "NO"]

        await inter.response.send_message(
            "This will delete **ALL** credit records for the clan, are you sure? Enter 'YES' if yes, or 'NO' else if not.")
        msg = "NO"
        #todo: test this
        try:
            msg = await bot.wait_for("message", check=check, timeout=30)  # 30 seconds to reply
        except asyncio.TimeoutError:
            await inter.response.send_message("Sorry, you didn't reply in time!")

        if msg.clean_content == "YES":
            result = database.clear_credits_for_clan(inter.guild.id, tag)
            if result is None:
                await inter.response.send_message(
                    "The clan {} has not been linked to this discord server. Run 'link' first.".format(tag))
                return
            await inter.response.send_message("All credits for the clan {} has been removed.".format(tag))
        else:
            await inter.response.send_message("Action cancelled.".format(tag))
        return
    # temporary debugging
    else:
        await inter.response.send_message("Option {} not supported. Run help for details.".format(option))


@crclan.error
async def crclan_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(f"'crclan' requires arguments. Run '{PREFIX}help crclan' for details")
    elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole):
        await ctx.channel.send(
            "Users of 'crclan' must have 'Manage server' permission. You do not seem to have permission to use this "
            "command")
    else:
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


#########################################################
# This method is used to track player credits
#########################################################
@bot.slash_command(description="Update a player's credits")
@commands.has_permissions(manage_guild=True)
async def crplayer(inter, tag: str, option: str = commands.Param(choices={"list_clan": "-lc",
                                                                      "list_player": "-lp",
                                                                      "add": "-a"}), value=None, *note):
    tag = utils.correct_tag(tag)

    log.info("GUILD={}, {}, ACTION=crplayer, arg={}, user={}".format(inter.guild.id, inter.guild.name, option, inter.author))

    # list credits of a clan's member
    if option == "-lc":
        clanname, playercredits, playername, last_updated = database.sum_clan_playercredits(inter.guild.id, tag)
        msgs = dataformatter.format_playercredits(tag, clanname, playercredits, playername, last_updated)
        for m in msgs:
            await inter.response.send_message(m)
        return
    # list credits of a clan's member
    elif option == "-lp":
        clantag, clanname, playername, records = database.list_playercredits(inter.guild.id, tag)
        msgs = dataformatter.format_playercreditrecords(tag, clantag, clanname, playername, records)
        for m in msgs:
            await inter.response.send_message(m)
        return
    # manually add credits to a player
    elif option == "-a":
        try:
            player = await coc_client.get_player(tag)
        except coc.NotFound:
            await inter.response.send_message("This player doesn't exist.")
            return

        if value is None:
            await inter.response.send_message(
                f"To manually add credits to a player, you must provide the value. Run '{PREFIX}help warn' for details")
            return
        try:
            value = float(value)
        except:
            await inter.response.send_message("The value you entered does not look like a number, try agian.")
            return
        #todo test this
        author = inter.message.author.mention
        database.add_player_credits(inter.guild.id, author, tag, player.name, player.clan.tag, player.clan.name, value,
                                    note)
        await inter.response.send_message("Credits manually updated for {} from the {} clan.".format(tag, player.clan.name))
        return
    else:
        await inter.response.send_message("Option {} not supported. Run help for details.".format(option))


@crplayer.error
async def crplayer_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(f"'crplayer' requires arguments. Run '{PREFIX}help crplayer' for details")
    elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole):
        await ctx.channel.send(
            "Users of 'crplayer' must have 'Manage server' permission. You do not seem to have permission to use this "
            "command")
    else:
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


#########################################################
# This method is used to produce personal war summary
#########################################################
@bot.slash_command(description="Produce a summary of a player's war performance data between two days")
async def mywar(inter, player_tag: str, from_date: str, to_date=None):
    player_tag = utils.correct_tag(player_tag)
    # check if the channels already exist
    try:
        from_date = datetime.datetime.strptime(from_date, "%d/%m/%Y")
    except:
        from_date = datetime.datetime.now() - datetime.timedelta(30)
        await inter.channel.send(
            "The start date you specified does not conform to the required format dd/mm/yyyy. The date 30 days ago from today"
            " will be used instead.".format(inter.channel, BOT_NAME))
    try:
        if to_date is not None:
            to_date = datetime.datetime.strptime(to_date, "%d/%m/%Y")
        else:
            to_date = datetime.datetime.now()
    except:
        to_date = datetime.datetime.now()
        await inter.channel.send(
            "The end date you specified does not confirm to the required format dd/mm/yyyy. The current date"
            " will be used instead.".format(inter.channel, BOT_NAME))

    # gather personal war data
    war_data = database.load_individual_war_data(inter.guild.id, player_tag, from_date, to_date)
    if len(war_data) < 5:
        await inter.response.send_message(
            "There are not enough war data for {} with a total of {} attacks in our database. Run the command with a wider timespan or try this later "
            "when you have warred more with us.".format(inter.channel, BOT_NAME))
        return

    player = models.Player(player_tag, player_tag)
    dataformatter.parse_personal_war_data(war_data, player)
    player.summarize_attacks()

    # attack stars by town hall
    data_as_list, row_index, header = models.summarise_by_townhalls(player._thlvl_attacks, player._thlvl_stars)
    data_for_plot = pandas.DataFrame(data_as_list, columns=header, index=row_index)
    targetfolder = "db/"
    Path(targetfolder).mkdir(parents=True, exist_ok=True)
    figure = data_for_plot.plot(kind='bar', stacked=True).get_figure()
    file = targetfolder + '/{}_byth.jpg'.format(player_tag.replace('#', '_'))
    figure.savefig(file, format='jpg')
    fileA = disnake.File(file)
    #todo: fix this, cannot send two messages
    await inter.channel.send("Data for **{}**, between **{}** and **{}**".format(player_tag, from_date, to_date))
    await inter.channel.send(file=fileA, content="**Attack stars by target town hall levels**:")
    plt.close(figure)

    # attack stars by time
    dataframe = models.summarise_by_months(player._attacks)
    figure = dataframe.plot(kind='bar', rot=0).get_figure()
    file = targetfolder + '/{}_bytime.jpg'.format(player_tag.replace('#', '_'))
    figure.savefig(file, format='jpg')
    fileB = disnake.File(file)
    await inter.channel.send(file=fileB, content="**Attack stars by time**:")
    await inter.response.send_message("Done")
    plt.close(figure)


@mywar.error
async def mywar_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(f"'mywar' requires four arguments. Run {PREFIX}help mywar for details")
    else:
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

#########################################################
# This method is used to track player credits
#########################################################
@bot.slash_command(description="Show the credits obtained by a player")
async def mycredit(inter, player_tag: str):
    player_tag = utils.correct_tag(player_tag)

    log.info("GUILD={}, {}, ACTION=mycredit, user={}".format(inter.guild.id, inter.guild.name, inter.author))

    clantag, clanname, playername, records = database.list_playercredits(inter.guild.id, player_tag)
    msgs = dataformatter.format_playercreditrecords(player_tag, clantag, clanname, playername, records)
    #todo: test this. multiple message sending....
    for m in msgs:
        await inter.channel.send(m)
    await inter.response.send_message("Done")
    return


@mycredit.error
async def mycredit_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(f"'mycredit' requires arguments. Run '{PREFIX}help mycredit' for details")
    else:
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


#############################################
# CoC api events
#############################################
# @coc_client.event  # Pro Tip : if you don't have @client.event then your events won't run! Don't forget it!
# @coc.ClanEvents.member_donations()
# async def on_clan_member_donation(old_member, new_member):
#     final_donated_troops = new_member.donations - old_member.donations
#     log.info(f"{new_member} of {new_member.clan} just donated {final_donated_troops} troops.")

@coc_client.event
@coc.WarEvents.state()  # notInWar, inWar, preparation, warEnded; should capture state change for any clans registered for credit watch
async def current_war_state(old_war: coc.ClanWar, new_war: coc.ClanWar):
    log.info("War state changed, old war = {}, new war = {}".format(old_war.state, new_war.state))
    try:
        if new_war.clan is None:
            nwclan = "None"
        else:
            nwclan = new_war.clan
        print("new war clan=" + str(nwclan))
    except:
        print("trying to print clan failed")

    if war_ended(old_war, new_war):  # war ended
        clan_home = old_war.clan
        log.info(
            "War ended between: {} and {}, type={}".format(old_war.clan, old_war.opponent, old_war.type))

        condition = clan_home.tag in database.MEM_mappings_clanwatch.keys()
        log.info("debug {}".format(database.MEM_mappings_clanwatch.keys()))
        log.info("debug {}".format(condition))

        # print("condition={}".format(condition))
        if condition:
            type = old_war.type
            if type == "friendly":
                log.info("Friendly war, ignored")
                return
            if type == "cwl":
                total_attacks = 1
                # cwl war state change, let's also reset the cache for current wars
                database.reset_cwl_war_data(clan_home.tag)
            else:
                total_attacks = 2

            members = old_war.members
            attacks = old_war.attacks
            missed_attacks, registered = register_war_attacks(members, attacks, old_war, clan_home, type, total_attacks)
            if registered:
                log.info(
                    "\tCredits registered for: {}. Missed attacks: {}".format(old_war.clan, missed_attacks))
            else:
                log.info(
                    "\tCredits not registered for: {}, something wrong... ".format(old_war.clan, missed_attacks))

            channel, misses = send_missed_attacks(missed_attacks, clan_home.tag)
            if channel is not None and misses is not None:
                await channel.send(misses)


@coc_client.event
@coc.WarEvents.war_attack()  # only if the clan war is registered in MEM_mappings_clan_currentwars
async def current_war_stats(attack, war):
    attacker = attack.attacker
    if attacker.is_opponent or not war.is_cwl:
        return

    attacker_clan = attacker.clan
    log.info("\t New cwl attack captured. clan={}, attacker={}".format(attacker_clan.tag, attacker))

    # check if this is the start of a new cwl war
    new_cwl_war = False
    if not attacker_clan.tag in database.MEM_current_cwl_wars.keys():
        # clan does not have a cwl war previously
        database.reset_cwl_war_data(attacker_clan.tag, war)
    else:
        # clan has a cwl war previously
        samewar = database.update_if_same_cwl_war(attacker_clan.tag, war)
        if not samewar:
            # 1. register previous cwl war attacks
            prev_war = database.MEM_current_cwl_wars[attacker_clan.tag][1]
            members = prev_war.members
            attacks = prev_war.attacks
            missed_attacks, registered = register_war_attacks(members, attacks, prev_war, attacker_clan, prev_war.type,
                                                              1)
            if registered:
                log.info(
                    "\tCredits registered for: {}. Missed attacks: {}".format(attacker_clan.tag, missed_attacks))
            else:
                log.info(
                    "\tCredits not registered for: {}, something wrong... ".format(attacker_clan.tag, missed_attacks))

            channel, misses = send_missed_attacks(missed_attacks, attacker_clan.tag)
            if channel is not None and misses is not None:
                await channel.send(misses)

            # 2. reset cwl war for this clan
            database.reset_cwl_war_data(attacker_clan.tag, war)


def register_war_attacks(members: list, attacks: list, old_war, clan_home, type, total_attacks):
    attack_data = {}
    for m in members:
        if not m.is_opponent:
            attack_data[(m.name, m.tag)] = []

    for atk in attacks:
        key = (atk.attacker.name, atk.attacker.tag)
        if key in attack_data.keys():
            # id: str, target_thlvl: int, source_thlvl: int, stars: int, is_outgoing: bool,
            # time: datetime.datetime
            id = atk.attacker_tag + ">" + atk.defender_tag
            atk_obj = models.Attack(id, atk.defender.town_hall, atk.attacker.town_hall,
                                    atk.stars, True, old_war.end_time.now)
            attack_data[key].append(atk_obj)

    missed_attacks, registered = database.save_war_attacks(clan_home.tag, clan_home.name, type, total_attacks,
                                                           attack_data)
    return missed_attacks, registered


def send_missed_attacks(misses: dict, clantag: str):
    clanwatch = database.get_clanwatch(clantag)
    guild = bot.get_guild(clanwatch._guildid)
    if guild is not None:
        channel_id = clanwatch._channel_warmiss
        if channel_id is not None:
            channel_id = dataformatter.parse_channel_id(channel_id)
        channel = disnake.utils.get(guild.channels, id=channel_id)
        if channel is not None:
            message = "War missed attack for **{} on {}**:\n".format(
                clanwatch._name, datetime.datetime.now())

            if len(misses) == 0:
                message += "\tNone, everyone attacked!"
            else:
                for k, v in misses.items():
                    message += "\t" + str(k) + "\t" + str(v) + "\n"
            return channel, message
    return None, None


def send_wardigest(fromdate, todate, clantag, clanname):
    # gather missed attacks data
    war_data = database.find_war_data(clantag, fromdate, todate)
    if len(war_data) == 0:
        return None, None, None, None

    # gather war data
    targetfolder = "db/" + clantag
    Path(targetfolder).mkdir(parents=True, exist_ok=True)
    # now process the file and extract data
    clan_war_data, data_missed, data_cwl_missed = dataformatter.parse_war_data(war_data, clantag)
    msg = "**{} clan war digest between {} and {}**:\n\n **Missed Attacks - Total:** \n".format(
        clantag + ", " + clanname,
        fromdate, todate)
    count=0
    for k, v in data_missed.items():
        msg += "\t" + str(k) + ": " + str(v) + "\n"
        count+=1
    if count==0:
        msg+="\t(no data)"
    msg_warmiss = msg + "\n"

    msg = "\n**Missed Attacks - CWL:** \n"
    count=0
    for k, v in data_cwl_missed.items():
        count+=1
        msg += "\t" + str(k) + ": " + str(v) + "\n"
    if count==0:
        msg+="\t(no data)"
    msg_cwlmiss = msg + "\n"

    data_for_plot, clan_summary = clan_war_data.output_clan_war_data(targetfolder)
    msg = "\n**Clan Overview**:\n"
    for k, v in clan_summary.items():
        msg += "\t" + k + ": " + str(v) + "\n"
    war_overview = msg + "\n"

    figure = data_for_plot.plot(kind='bar', stacked=True).get_figure()
    figure.savefig(targetfolder + '/clan_war_data.jpg', format='jpg')
    # now fetch that file and send it to the channel
    fileB = disnake.File(targetfolder + "/clan_war_data.jpg")
    war_plot = fileB
    return msg_warmiss, msg_cwlmiss, war_overview, war_plot
    # await channel_to.send(file=fileB,
    #                       content="**Clan war data plot ready for download**:")


def war_ended(old_war: coc.ClanWar, new_war: coc.ClanWar):
    if old_war.state == "inWar" and new_war.state != "inWar":
        return True
    if old_war.state == "inWar" and old_war.war_tag is not None:
        return True


def regular_war_started(old_war: coc.ClanWar, new_war: coc.ClanWar):
    return old_war.state == "preparation" and new_war.state == "inWar"


def regular_war_ended(old_war: coc.ClanWar, new_war: coc.ClanWar):
    return new_war.state == "warEnded" and old_war.state == "inWar"


def cwl_war_started(old_war: coc.ClanWar, new_war: coc.ClanWar):
    return old_war.state == "notInWar" and new_war.state == "inWar" and new_war.type == "cwl"


####################################################
# for debugging                                    #
####################################################
@coc_client.event  # Pro Tip : if you don't have @client.event then your events won't run! Don't forget it!
@coc.ClanEvents.member_donations()
async def on_clan_member_donation(old_member, new_member):
    final_donated_troops = new_member.donations - old_member.donations
    log.info(f"{new_member} of {new_member.clan} just donated {final_donated_troops} troops.")


@coc_client.event
@coc.ClanEvents.points()
async def on_clan_trophy_change(old_clan, new_clan):
    log.info(f"{new_clan.name} total trophies changed from {old_clan.points} to {new_clan.points}")


@tasks.loop(hours=23)
# @tasks.loop(minutes=1)
async def check_scheduled_task():
    now = datetime.datetime.now()
    season_end = utils.get_season_end()
    log.info("\t>>> Checking scheduled task every 23 hour. Time now is {}. The current season will end {}".format(now,
                                                                                                                  season_end))
    days_before_end = abs((season_end - now).days)
    #    if days_before_end <=1:
    if days_before_end <= 1:
        log.info("\t>>> End of season reached, running scheduled task.")

        for clantag, clanwatch in database.MEM_mappings_clanwatch.items():
            # clan war digest
            guild = bot.get_guild(clanwatch._guildid)
            if guild is not None:
                channel_id = clanwatch._channel_warsummary
                if channel_id is not None:
                    channel_id = dataformatter.parse_channel_id(channel_id)
                channel = disnake.utils.get(guild.channels, id=channel_id)
                if channel is not None:
                    fromdate = utils.get_season_start()
                    war_miss, cwl_miss, war_overview, war_plot = send_wardigest(fromdate, now, clantag, clanwatch._name)

                    if war_miss is None or cwl_miss is None or war_overview is None or war_plot is None:
                        await channel.send("Not enough war data for {}, {}".format(clantag, clanwatch._name))
                        return

                    await channel.send(war_miss)
                    await channel.send(cwl_miss)
                    await channel.send(war_overview)
                    await channel.send(file=war_plot,
                                       content="**Clan war data plot ready for download**:")

            # credits for donations
            clan = await coc_client.get_clan(clantag)
            members = clan.members
            donations = {}
            for m in members:
                donations[(m.tag, m.name)] = m.donations
            doantions_sorted = sorted(donations.items(), key=operator.itemgetter(1), reverse=True)
            top = 0
            for p in doantions_sorted:
                if top == 0 and 'donation#1' in clanwatch._creditwatch_points.keys():
                    pts = int(clanwatch._creditwatch_points['donation#1'])
                    database.add_player_credits(clanwatch._guildid,
                                                'bot', p[0][0], p[0][1], clantag, clanwatch._name, pts,
                                                'donation #1')
                elif top == 1 and 'donation#2' in clanwatch._creditwatch_points.keys():
                    pts = int(clanwatch._creditwatch_points['donation#2'])
                    database.add_player_credits(clanwatch._guildid,
                                                'bot', p[0][0], p[0][1], clantag, clanwatch._name, pts,
                                                'donation #2')
                elif top == 2 and 'donation#3' in clanwatch._creditwatch_points.keys():
                    pts = int(clanwatch._creditwatch_points['donation#3'])
                    database.add_player_credits(clanwatch._guildid,
                                                'bot', p[0][0], p[0][1], clantag, clanwatch._name, pts,
                                                'donation #3')
                top += 1
                if top >= 2:
                    break
    else:
        log.info("\t>>> {} days till the end of season".format(days_before_end))


# async def main():
#     async with bot:
#         check_scheduled_task.start()
#         await bot.start(TOKEN)
#
# asyncio.run(main())
check_scheduled_task.start()
bot.run(TOKEN)
