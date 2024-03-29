import datetime, disnake, pandas, sys, traceback, coc, logging, operator, pickle
import matplotlib.pyplot as plt
from pathlib import Path
from clashhogs import database, dataformatter, models, util, bot_functions
from coc import utils
from disnake.ext import commands
from disnake.ext import tasks

######################################
# Init                               #
######################################
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
PREFIX = properties['BOT_PREFIX']
BOT_NAME = properties['BOT_NAME']
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

    log.info('The following guilds are linked with the bot:')
    for guild in bot.guilds:
        log.info('\t{}, {}, checking databases...'.format(guild.name, guild.id))
        database.check_database(guild.id, rootfolder)
    log.info('Init completed')

@bot.event
async def on_guild_join(guild):
    log.info('{} has been added to a new server: {}'.format(BOT_NAME, guild.id))
    log.info('\t{}, {}, checking databases...'.format(guild.name, guild.id))
    database.check_database(guild.id, rootfolder)


#########################################################
# Register the help command
#########################################################
@bot.slash_command(description="Show the list of commands and a summary of their functions.")
async def help(inter, command: str = commands.Param(choices={"clanlist":"clanlist",
                                                             "show-all": "all",
                                                             "link": "link",
                                                             "channel": "channel",
                                                             "clanwar": "clanwar",
                                                             "warn": "warn",
                                                             "blacklist": "blacklist",
                                                             "crclan": "crclan",
                                                             "crplayer": "crplayer",
                                                             "waw_setup": "waw_setup",
                                                             "waw_view": "waw_view",
                                                             "mycredit": "mycredit",
                                                             "mywar": "mywar"})):
    if command == 'clanlist':
        await inter.response.send_message(embed=util.prepare_clanlist_help())
    elif command == 'all':
        await inter.response.send_message(embed=util.prepare_help_menu(BOT_NAME))
    elif command == 'link':
        await inter.response.send_message(embed=util.prepare_link_help())
    elif command == 'channel':
        await inter.response.send_message(embed=util.prepare_channel_help())
    elif command == 'clanwar':
        await inter.response.send_message(embed=util.prepare_clanwar_help())
    elif command == 'mywar':
        await inter.response.send_message(embed=util.prepare_mywar_help())
    elif command == 'warn':
        await inter.response.send_message(embed=util.prepare_warn_help())
    elif command == 'blacklist':
        await inter.response.send_message(embed=util.prepare_blacklist_help())
    elif command == 'crclan':
        await inter.response.send_message(embed=util.prepare_crclan_help(models.STANDARD_CREDITS))
    elif command == 'crplayer':
        await inter.response.send_message(embed=util.prepare_crplayer_help())
    elif command == 'waw_setup':
        await inter.response.send_message(embed=util.prepare_wawsetup_help(models.STANDARD_ATTACKUP_WEIGHTS,
                                                                           models.STANDARD_ATTACKDOWN_WEIGHTS))
    elif command == 'waw_view':
        await inter.response.send_message(embed=util.prepare_wawview_help())
    elif command == 'mycredit':
        await inter.response.send_message(embed=util.prepare_mycredit_help())
    else:
        await inter.response.send_message(f'Command {command} does not exist.')

#########################################################
# This method is used to configure the discord channels
# to automatically tally missed attacks
#########################################################
@bot.slash_command(description="Add a clan to the 'clan list' (requires admin access).")
@commands.has_permissions(manage_guild=True)
async def clanlist(inter, option: str = commands.Param(choices={"add": "-a",
                                                            "list (clan tag not required)": "-l",
                                                            "remove": "-r"}), clantag: str = None, thlevel:str=None,
                                                            rules_channel=None):
    log.info(
        "GUILD={}, {}, ACTION=clanlist, OPTION={}, user={}".format(inter.guild.id, inter.guild.name, option, inter.author))
    clantag=utils.correct_tag(clantag)
    clan = await bot_functions.check_clan(clantag, coc_client)

    if option == '-a':
        if clan is None:
            await inter.response.send_message("Cannot find a clan with the given tag: {}".format(clantag))
            return
        if thlevel is None:
            await inter.response.send_message("You must enter the minimum TH level your clan requires".format(clantag))
            return
        if rules_channel is None:
            await inter.response.send_message("You must assign a channel for the clan's rules".format(clantag))
            return

        discord_rules_channel = dataformatter.parse_channel_id(rules_channel)
        channel = disnake.utils.get(inter.guild.channels, id=discord_rules_channel)
        if channel is None:
            await inter.response.send_message(
                f"The channel {rules_channel} does not exist. Please create it first.")
            return

        database.add_clanlist(clantag, thlevel,discord_rules_channel)
        await inter.response.send_message(
            "Clan added to the clan list.")
    elif option == '-l':
        clans = database.show_clanlist()
        if len(clans)==0:
            await inter.response.send_message("No clan has been added to the list yet.".format(clantag))
            return
        embed_list = []
        for c in clans:
            ctag = c[0]
            min_th=c[1]
            #channel = disnake.utils.get(inter.guild.channels, id=c[2])
            clan = await bot_functions.check_clan(ctag, coc_client)
            embed, msg=dataformatter.format_clanlist_data(clan, min_th,'<#'+str(c[2])+'>')
            embed_list.append((msg, embed))
        embed_list=sorted(
            embed_list,
            key=lambda x: x[0]
        )

        embed_list_sorted=[]
        for t in embed_list:
            embed_list_sorted.append(t[1])
        await inter.response.send_message(embeds=embed_list_sorted)
        return
    elif option == '-r':
        if clantag is None:
            await inter.response.send_message("Clan tag must be provided")
            return
        database.remove_clanlist(clantag)
        await inter.response.send_message("Clan {} has been removed from the list.".format(clantag))
        return
    else:
        await inter.response.send_message("Option {} not supported. Run help for details.".format(option))

@clanlist.error
async def clanlist_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(f"'clanlist' requires arguments. Run /help clanlist for details")
    elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole):
        await ctx.channel.send(
            "Users of 'clanlist' must have 'Manage server' permission. You do not seem to have permission to use this "
            "command")
    else:
        print("clanlist_error: {}".format(datetime.datetime.now()))
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

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
    clantag=utils.correct_tag(clantag)
    clan = await bot_functions.check_clan(clantag, coc_client)

    if option == '-a':
        if clan is None:
            await inter.response.send_message("Cannot find a clan with the given tag: {}".format(clantag))
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
            clanwatches = database.get_clanwatch_by_guild(inter.guild.id)
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
        await ctx.channel.send(f"'link' requires arguments. Run /help link for details")
    elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole):
        await ctx.channel.send(
            "Users of 'link' must have 'Manage server' permission. You do not seem to have permission to use this "
            "command")
    else:
        print("link_error: {}".format(datetime.datetime.now()))
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

#########################################################
# This method is used to set up the discord channels
# for war missed attacks, member watch and war summary feeds
#########################################################
@bot.slash_command(
    description="Set up channels for a clan's feeds (clan must be already linked to this discord server).")
@commands.has_permissions(manage_guild=True)
async def channel(inter, clantag, to_channel, option: str = commands.Param(choices={"war-monthly": "-war",
                                                                                    "missed-attacks": "-miss",
                                                                                    "member-watch": "-member"})):
    clantag = utils.correct_tag(clantag)
    log.info(
        "GUILD={}, {}, ACTION=channel, arg={}, user={}".format(inter.guild.id, inter.guild.name, option, inter.author))
    # list current mappings
    clan = await bot_functions.check_clan(clantag, coc_client)
    if clan is None:
        await inter.response.send_message("Cannot find a clan with the given tag: {}".format(clantag))
        return
    clanwatch = database.get_clanwatch(clantag)
    if clanwatch is None:
        await inter.response.send_message("This clan has not been linked to this discord server. Run 'link' first.")
        return

    to_channel_id = dataformatter.parse_channel_id(to_channel)
    channel = disnake.utils.get(inter.guild.channels, id=to_channel_id)
    if channel is None:
        await inter.response.send_message(
            f"The channel {to_channel} does not exist. Please create it first, and give {BOT_NAME} "
            "'Send messages' permission to that channel.")
        return

    # check permissions
    res = channel.permissions_for(inter.guild.me)
    missing_perms = not res.send_messages or not res.view_channel or not res.attach_files
    if missing_perms:
        await inter.response.send_message(
            "{} does not have the right permissions and will not function properly. Please " \
            "give {} 'View Channel', 'Attach Files', and 'Send Messages' permissions to the channel, then try again.".format(
                BOT_NAME, BOT_NAME))
        return

    if option == "-miss":
        clanwatch._channel_warmiss = to_channel
        database.add_clanwatch(clantag, clanwatch)
        await inter.response.send_message("War missed attack channel has been added for this clan. ")
    elif option == "-war":
        clanwatch._channel_warsummary = to_channel
        database.add_clanwatch(clantag, clanwatch)
        await inter.response.send_message("War summary channel has been added for this clan.")
    elif option == "-member":
        clanwatch._channel_clansummary = to_channel
        database.add_clanwatch(clantag, clanwatch)
        await inter.response.send_message("Member watcg channel has been added for this clan.")
    else:
        await inter.response.send_message(
            "Option {} is not supported. Use miss/feed/war. Run help for details.".format(option))
        return

@channel.error
async def channel_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(f"'channel' requires arguments. Run /help channel for details")
    elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole):
        await ctx.channel.send(
            "Users of 'channel' must have 'Manage server' permission. You do not seem to have permission to use this "
            "command")
    else:
        print("channel_error: {}".format(datetime.datetime.now()))
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

########################################################
# This method is used to process clan war summary
#########################################################
@bot.slash_command(
    description="Product a summary of war performance for a clan that is linked with this discord server")
@commands.has_permissions(manage_guild=True)
async def clanwar(inter, clantag: str, from_date: str, to_date=None):
    clantag = utils.correct_tag(clantag)
    log.info("GUILD={}, {}, ACTION=clanwar, user={}".format(inter.guild.id, inter.guild.name, inter.author))

    clan = await bot_functions.check_clan(clantag, coc_client)
    if clan is None:
        await inter.response.send_message("Cannot find a clan with the given tag: {}".format(clantag))
        return
    clanwatch = database.get_clanwatch(clantag)
    if clanwatch is None:
        await inter.response.send_message("This clan has not been linked to this discord server. Run 'link' first.")
        return

    to_channel_id = dataformatter.parse_channel_id(clanwatch._channel_warsummary)
    if to_channel_id == -1:
        await inter.response.send_message(
            "The channel for war summary has not been set. Run '/channel' to set this up first.")
        return
    else:
        channel_to = disnake.utils.get(inter.guild.channels, id=to_channel_id)
        if channel_to is None:
            await inter.response.send_message(
                "The target channel does not exist. Please check your setting using /link")
            return
        from_date = bot_functions.check_date(from_date)
        if from_date is None:
            await inter.response.send_message(
                "The date you specified does not conform to the required format dd/mm/yyyy. Please try again")
            return
        to_date = bot_functions.check_date(to_date)
        if to_date is None:
            to_date = datetime.datetime.now()
            await inter.channel.send(
                    "End date not provided or does not conform to the format dd/mm/yyyy, using today's date as the end date")
        war_miss, cwl_miss, war_overview, war_plot, summary = \
            bot_functions.prepare_wardigest(from_date, to_date, clantag,clanwatch._name, database)
        if war_miss is None or cwl_miss is None or war_overview is None or war_plot is None:
            await inter.response.send_message("Not enough war data for {}, {}. Please try again later after a few wars.".format(clantag, clanwatch._name))
            return

        await channel_to.send(war_miss)
        await channel_to.send(cwl_miss)
        await channel_to.send(war_overview)
        await channel_to.send(file=war_plot,
                              content="**Clan war data plot ready for download**:")

    await inter.response.send_message("Done. Please see your target channel {} for the output. ".format(channel_to))

@clanwar.error
async def clanwar_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(f"'clanwar' requires four arguments. Run /help clanwar for details")
    elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole):
        await ctx.channel.send(
            "Users of 'clanwar' must have 'Manage server' permission. You do not seem to have permission to use this "
            "command")
    else:
        await ctx.channel.send(
            "Looks like I can't send messages to the target channel. Did you give me 'Send Message' and "
            "'Attach Files' permission? "
            "Run '/link list' to check the target channel you have set up for this clan.")
        print("clanwar_error: {}".format(datetime.datetime.now()))
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


#########################################################
# This method is used to record warnings
#########################################################
@bot.slash_command(description='Add a warning record to a member of a clan')
@commands.has_permissions(manage_guild=True)
async def warn(inter, clan: str, option: str = commands.Param(choices={"list": "-l",
                                                                       "add": "-a",
                                                                       "clear": "-c",
                                                                       "delete": "-d"}), name_or_id=None, points=None,
               reason=None):
    log.info(
        "GUILD={}, {}, ACTION=warn, arg={}, user={}".format(inter.guild.id, inter.guild.name, option, inter.author))

    # list current warnings
    if option == "-l":
        await inter.response.send_message("Listing warning records...")
        if name_or_id is None:  # list all warnings of a clan
            res = database.list_warnings(inter.guild.id, clan)
            warnings = dataformatter.format_warnings(clan, res)
            if len(warnings) == 1:
                await inter.followup.send("No records found.")
            else:
                for w in warnings:
                    await inter.followup.send(w)
        else:  # list all warnings of a person in a clan
            res = database.list_warnings(inter.guild.id, clan, name_or_id)
            warnings = dataformatter.format_warnings(clan, res, name_or_id)
            for w in warnings:
                await inter.followup.send(w)
        return
    # add a warning
    elif option == "-a":
        if name_or_id is None or points is None:
            await inter.response.send_message(
                f"'warn' requires 4~5 arguments for adding a warning. Run '/help warn' for details")
            return
        try:
            points = float(points)
        except:
            await inter.response.send_message(
                "The value you entered for this warning does not look like a number, try agian.")
            return
        database.add_warning(inter.guild.id, clan, name_or_id, points, reason)
        await inter.response.send_message("Warning added for {} from the {} clan.".format(name_or_id, clan))
        return
    # clear all warnings with a person
    elif option == "-c":
        if name_or_id is None:
            await inter.response.send_message(
                f"'warn' requires 4 arguments for clearing  warnings. Run '/help warn' for details")
            return

        v = util.Confirm()
        await inter.response.send_message(
            "This will delete **ALL** warning records for the player, are you sure?", view=v)
        await v.wait()
        if v.value is None:
            await inter.followup.send("Timed out.")
            return
        elif v.value:
            database.clear_warnings(inter.guild.id, clan, name_or_id)
            await inter.followup.send("All warnings for {} from the {} clan are deleted.".format(name_or_id, clan))
            return
        else:
            await inter.followup.send("Action cancelled.")
            return
        # delete a warning
    elif option == "-d":
        deleted = database.delete_warning(inter.guild.id, clan, name_or_id)
        if deleted:
            await inter.response.send_message("The warning record(s) has/have been deleted".format(clan))
        else:
            await inter.response.send_message(
                "Operation failed. Perhaps the warning ID {} and the clan name {} do not match what's in the database."
                " If you are providing a date, it must conform to the YYYY-MM-DD format.".format(name_or_id, clan))
        return
    else:
        await inter.response.send_message("Option {} not supported. Run help for details.".format(option))
        return

@warn.error
async def warn_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(f"'warn' requires arguments. Run '/help warn' for details")
    elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole):
        await ctx.channel.send(
            "Users of 'warn' must have 'Manage server' permission. You do not seem to have permission to use this "
            "command")
    else:
        print("warn_error: {}".format(datetime.datetime.now()))
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


#########################################################
# This method is used to record blacklist
#########################################################
@bot.slash_command(description='Manage the player blacklist.')
@commands.has_permissions(manage_guild=True)
async def blacklist(inter, option: str = commands.Param(choices={"list": "-l",
                                                                 "add": "-a",
                                                                 "delete": "-d"}),
                    player_tag: str = None, reason=None):
    log.info(
        "GUILD={}, {}, ACTION=blacklist, arg={}, user={}".format(inter.guild.id, inter.guild.name, option,
                                                                 inter.author))

    # list current blaclkist
    if option == "-l":
        await inter.response.send_message("Showing the current blacklist...")
        if player_tag is None:  # list all warnings of a clan
            res = database.show_blacklist(inter.guild.id, None)
            entries = dataformatter.format_blacklist(res)
        else:  # check if a player is on the list
            res = database.show_blacklist(inter.guild.id, player_tag)
            entries = dataformatter.format_blacklist(res)

        if len(entries) == 0:
            await inter.followup.send("No records found.")
        else:
            for w in entries:
                await inter.followup.send(w)

        return
    # add to blacklist
    elif option == "-a":
        if player_tag is None or reason is None:
            await inter.response.send_message(
                f"'blacklist' requires arguments for adding a player. Run '/help blacklist' for details")
            return
        author = inter.author.display_name
        player_tag = utils.correct_tag(player_tag)
        player=await bot_functions.check_player(player_tag, coc_client)
        if player is None:
            await inter.response.send_message(
                    "This player does not exist. Please check the tag and try again.")
            return

        database.add_blacklist(inter.guild.id, player.tag, player.name, author, reason)
        await inter.response.send_message("Player added to the blacklist.")
        return
    # delete a player
    elif option == "-d":
        deleted = database.delete_blacklist(inter.guild.id, player_tag)
        await inter.response.send_message("The player has been removed from the blacklist")
    else:
        await inter.response.send_message("Option {} not supported. Run help for details.".format(option))
        return

@blacklist.error
async def blacklist_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(f"'blacklist' requires arguments. Run '/help blacklist' for details")
    elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole):
        await ctx.channel.send(
            "Users of 'blacklist' must have 'Manage server' permission. You do not seem to have permission to use this "
            "command")
    else:
        print("blacklist_error: {}".format(datetime.datetime.now()))
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


#########################################################
# This method is used to set up clan credit watch system
#########################################################
@bot.slash_command(description='Set up credit points for a clan')
@commands.has_permissions(manage_guild=True)
async def crclan(inter, option: str = commands.Param(choices={"list": "-l",
                                                              "update": "-u",
                                                              "clear": "-c"}), clantag: str = None, points=None):
    if clantag is not None:
        clantag = utils.correct_tag(clantag)
    log.info(
        "GUILD={}, {}, ACTION=crclan, arg={}, user={}".format(inter.guild.id, inter.guild.name, option, inter.author))

    # list current registered clans
    if option == "-l":
        if clantag is None:
            res = database.get_clanwatch_by_guild(str(inter.guild.id))
        else:
            res = [database.get_clanwatch(clantag, str(inter.guild.id))]
        await inter.response.send_message(embed=dataformatter.format_credit_systems(res))
        return
    # register a clan
    elif option == "-u":
        if clantag is None:
            await inter.response.send_message("'tag' cannot be empty")
            return
        clan = await bot_functions.check_clan(clantag, coc_client)
        if clan is None:
            await inter.response.send_message("This clan doesn't exist.")
            return

        result = database.registered_clan_creditwatch(inter.guild.id, clantag, points)
        if result is None:
            await inter.response.send_message(
                "The clan {} has not been linked to this discord server. Run 'link' first.".format(clantag))
            return
        if len(result) != 0:
            await inter.response.send_message(
                "Update for the clan {} has been unsuccessful. The parameters you provided maybe invalid, try again: {}".
                    format(clan, result))
            return
        else:
            await inter.response.send_message(
                "The clan {} has been updated for the credit watch system.".format(clantag))
        return
    # clear all records of a clan
    elif option == "-c":
        if clantag is None:
            await inter.response.send_message("'tag' cannot be empty")
            return

        v = util.Confirm()
        await inter.response.send_message(
            "This will delete **ALL** credit records for the clan, are you sure?", view=v)
        await v.wait()
        if v.value is None:
            await inter.followup.send("Timed out.")
            return
        elif v.value:
            result = database.clear_credits_for_clan(inter.guild.id, clantag)
            if result is None:
                await inter.followup.send(
                    "The clan {} has not been linked to this discord server. Run 'link' first.".format(clantag))
                return
            await inter.followup.send("All credits for the clan {} has been removed.".format(clantag))
            return
        else:
            await inter.followup.send("Action cancelled.")
            return
    else:
        await inter.response.send_message("Option {} not supported. Run help for details.".format(option))

@crclan.error
async def crclan_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(f"'crclan' requires arguments. Run '/help crclan' for details")
    elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole):
        await ctx.channel.send(
            "Users of 'crclan' must have 'Manage server' permission. You do not seem to have permission to use this "
            "command")
    else:
        print("crclan_error: {}".format(datetime.datetime.now()))
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


#########################################################
# This method is used to set up clan credit watch system
#########################################################
@bot.slash_command(description='Set up war attack weights for a clan')
@commands.has_permissions(manage_guild=True)
async def waw_setup(inter, option: str = commands.Param(choices={"list": "-l",
                                                                 "update": "-u"}), clantag: str = None, weights=None):
    if clantag is not None:
        clantag = utils.correct_tag(clantag)
    log.info("GUILD={}, {}, ACTION=waw_setup, arg={}, user={}".format(inter.guild.id, inter.guild.name, option,
                                                                      inter.author))
    # list current registered clans
    if option == "-l":
        if clantag is None:
            res = database.get_clanwatch_by_guild(str(inter.guild.id))
        else:
            res = [database.get_clanwatch(clantag, str(inter.guild.id))]
        await inter.response.send_message(embed=dataformatter.format_war_attack_weights(res))
        return
    # update attack weights for a clan
    elif option == "-u":
        if clantag is None:
            await inter.response.send_message("'tag' cannot be empty")
            return
        clan = await bot_functions.check_clan(clantag, coc_client)
        if clan is None:
            await inter.response.send_message("This clan doesn't exist.")
            return

        result = database.registered_clan_attackweights(inter.guild.id, clantag, weights)
        if result is None:
            await inter.response.send_message(
                "The clan {} has not been linked to this discord server. Run 'link' first.".format(clantag))
            return
        if len(result) != 0:
            await inter.response.send_message(
                "Update for the clan {} has been unsuccessful. The parameters you provided maybe invalid, try again: {}".
                    format(clan, result))
            return
        else:
            await inter.response.send_message("The clan {} has been updated.".format(clantag))
        return
    else:
        await inter.response.send_message("Option {} not supported. Run help for details.".format(option))

@crclan.error
async def waw_setup(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(f"'waw_setup' requires arguments. Run '/help waw_setup' for details")
    elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole):
        await ctx.channel.send(
            "Users of 'waw_setup' must have 'Manage server' permission. You do not seem to have permission to use this "
            "command")
    else:
        print("waw_setup_error: {}".format(datetime.datetime.now()))
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

#########################################################
# This method is used to view the adjusted stars by players
#########################################################
@bot.slash_command(
    description="View players' war stars collected between two dates, adjusted by WAW multipliers.")
async def waw_view(inter, option: str = commands.Param(choices={"clan": "-lc",
                                                                "player": "-lp"}),
                   wartype: str = commands.Param(choices={"any": "all",
                                                          "regular": "random",
                                                          "cwl": "cwl"}),
                   tag: str = None,
                   from_date: str = None, to_date=None):
    #debug
    if len(database.MEM_current_cwl_wars)>0:
        log.info("\t>> DEBUG saving cwl war objects in memory...")
        with open('debug_current_war.pickle', 'wb') as handle:
            pickle.dump(database.MEM_current_cwl_wars, handle, protocol=pickle.HIGHEST_PROTOCOL)
    #debug

    for clantag, warTuple in database.MEM_current_cwl_wars.items():
        warobj=warTuple[1]
        if warobj.end_time.now < datetime.datetime.now():
            log.info("\t>> waw_view running background task (closing cwl wars...)")
            attacker_clan=await coc_client.get_clan(clantag)
            channel, misses=bot_functions.close_cwl_war(database, bot, log, attacker_clan, None, 1)
            if channel is not None and misses is not None:
                await channel.send(misses)

    if tag is None:
        await inter.response.send_message(
            "'tag' cannot be empty. This should be either a player's or a clan's tag, depending on your option.")
        return
    tag = utils.correct_tag(tag)

    from_date = bot_functions.check_date(from_date)
    if from_date is None:
        await inter.response.send_message(
            "The date you specified does not conform to the required format dd/mm/yyyy. Please try again")
        return
    to_date = bot_functions.check_date(to_date)
    if to_date is None:
        to_date = datetime.datetime.now()
        await inter.channel.send(
            "End date not provided or does not conform to the format dd/mm/yyyy, using today's date as the end date")

    log.info(
        "GUILD={}, {}, ACTION=waw_view, arg={}, user={}".format(inter.guild.id, inter.guild.name, option, inter.author))

    if wartype == "all":
        wartype = None
        wartypestr = "all"
    elif wartype == "random":
        wartypestr = "regular"
    else:
        wartypestr="cwl"

    # list total points of a clan's member
    if option == "-lc":
        clan_watch = database.get_clanwatch(tag, inter.guild.id)
        if clan_watch is None:
            await inter.response.send_message("It appears that the clan {} has not been linked with this discord server. Run '/link' first.".format(tag))
            return

        await inter.response.send_message("Listing total adjusted war stars for all members of the clan {}, war type is '{}'".format(tag, wartypestr))
        war_data = database.find_war_data(tag, from_date, to_date, wartype)
        msgs=dataformatter.format_attackstars(war_data,clan_watch)
        for m in msgs:
            await inter.followup.send(m)
        return
    # list adjusted stars of a clan's member
    elif option == "-lp":
        war_data = database.load_individual_war_data(inter.guild.id, tag, from_date, to_date, wartype)
        if len(war_data) == 0:
            await inter.response.send_message("No data found matching the search criteria. The player's clan must have been linked to this discord server using '/link'. "
                     "Also, war data must have been already collected for the player.")
            return

        await inter.response.send_message(
            "Listing every attack record with adjusted stars for player {}, war type is '{}' (If none is shown then this player may have missed all attacks).".format(tag, wartypestr))
        first_record=war_data[0]
        clan_tag=first_record[3]
        clan_watch = database.get_clanwatch(clan_tag, inter.guild.id)
        if clan_watch is None:
            await inter.response.send_message(
                "It appears that the clan {} has not been linked with this discord server. Run '/link' first.".format(
                    tag))
            return

        msgs=dataformatter.format_attack_records(war_data,clan_watch)
        for m in msgs:
            await inter.followup.send(m)
        return
    else:
        await inter.response.send_message("Option {} not supported. Run help for details.".format(option))

@waw_view.error
async def waw_view_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(f"'waw_view' requires arguments. Run '/help waw_view' for details")
    else:
        print("waw_view_error: {}".format(datetime.datetime.now()))
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

#########################################################
# This method is used to track player credits
#########################################################
@bot.slash_command(description="View or manage players' credits")
@commands.has_permissions(manage_guild=True)
async def crplayer(inter, option: str = commands.Param(choices={"list_clan": "-lc",
                                                                "list_player": "-lp",
                                                                "add": "-a"}), tag: str = None, points=None,
                   reason=None):
    if tag is None:
        await inter.response.send_message(
            "'tag' cannot be empty. This should be either a player's or a clan's tag, depending on your option.")
        return
    tag = utils.correct_tag(tag)

    log.info(
        "GUILD={}, {}, ACTION=crplayer, arg={}, user={}".format(inter.guild.id, inter.guild.name, option, inter.author))

    # list credits of a clan's member
    if option == "-lc":
        await inter.response.send_message("Listing credits for all clan members...")
        clanname, playercredits, playername, last_updated = database.sum_clan_playercredits(inter.guild.id, tag)
        msgs = dataformatter.format_playercredits(tag, clanname, playercredits, playername, last_updated)
        for m in msgs:
            await inter.followup.send(m)
        return
    # list credits of a clan's member
    elif option == "-lp":
        await inter.response.send_message("Listing credits for a player...")
        clantag, clanname, playername, records = database.list_playercredits(inter.guild.id, tag)
        msgs = dataformatter.format_playercreditrecords(tag, clantag, clanname, playername, records)
        for m in msgs:
            await inter.followup.send(m)
        return
    # manually add credits to a player
    elif option == "-a":
        player = await bot_functions.check_player(tag, coc_client)
        if player is None:
            await inter.response.send_message(
                "This player does not exist. Please check the tag and try again.")
            return

        if points is None:
            await inter.response.send_message(
                f"To manually add credits to a player, you must provide the value. Run '/help crplayer' for details")
            return
        try:
            points = float(points)
        except:
            await inter.response.send_message("The value you entered does not look like a number, try agian.")
            return
        author = inter.author.display_name
        database.add_player_credits(inter.guild.id, author, tag, player.name, player.clan.tag, player.clan.name, points,
                                    reason)
        await inter.response.send_message(
            "Credits manually updated for {} from the {} clan.".format(tag + ", " + player.name, player.clan.name))
        return
    else:
        await inter.response.send_message("Option {} not supported. Run help for details.".format(option))

@crplayer.error
async def crplayer_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(f"'crplayer' requires arguments. Run '/help crplayer' for details")
    elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole):
        await ctx.channel.send(
            "Users of 'crplayer' must have 'Manage server' permission. You do not seem to have permission to use this "
            "command")
    else:
        print("crplayer_error: {}".format(datetime.datetime.now()))
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


#########################################################
# This method is used to produce personal war summary
#########################################################
@bot.slash_command(description="Produce a summary of a player's war performance data between two days")
async def mywar(inter, player_tag: str, from_date: str, to_date=None):
    player_tag = utils.correct_tag(player_tag)
    from_date = bot_functions.check_date(from_date)
    if from_date is None:
        await inter.response.send_message(
            "The date you specified does not conform to the required format dd/mm/yyyy. Please try again")
        return
    to_date = bot_functions.check_date(to_date)
    if to_date is None:
        to_date = datetime.datetime.now()
        await inter.channel.send(
            "End date not provided or does not conform to the format dd/mm/yyyy, using today's date as the end date")

    # gather personal war data
    war_data = database.load_individual_war_data(inter.guild.id, player_tag, from_date, to_date)
    if len(war_data) < 5:
        await inter.response.send_message(
            "There are not enough war data for {} with a total of {} attacks in our database. Run the command with a wider timespan or try this later "
            "when you have warred more with us.".format(player_tag, len(war_data)))
        return

    await inter.response.send_message("Preparing data...")
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
    await inter.followup.send("Data for **{}**, between **{}** and **{}**".format(player_tag, from_date, to_date))
    await inter.followup.send(file=fileA, content="**Attack stars by target town hall levels**:")
    plt.close(figure)

    # attack stars by time
    dataframe = models.summarise_by_months(player._attacks)
    figure = dataframe.plot(kind='bar', rot=0).get_figure()
    file = targetfolder + '/{}_bytime.jpg'.format(player_tag.replace('#', '_'))
    figure.savefig(file, format='jpg')
    fileB = disnake.File(file)
    await inter.followup.send(file=fileB, content="**Attack stars by time**:")

    plt.close(figure)

@mywar.error
async def mywar_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(f"'mywar' requires four arguments. Run '/help mywar' for details")
    else:
        await ctx.channel.send(
            "Something went wrong. Check if {} has 'Send Message' and 'Attach files' permisions".format(BOT_NAME))
        print("mywar_error: {}".format(datetime.datetime.now()))
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

    if len(msgs) == 0:
        await inter.response.send_message("No records found.")
    else:
        await inter.response.send_message("Listing credits...")
        for m in msgs:
            await inter.followup.send(m)
    return

@mycredit.error
async def mycredit_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send(f"'mycredit' requires arguments. Run '/help mycredit' for details")
    else:
        print("mywar_error: {}".format(datetime.datetime.now()))
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

    if bot_functions.war_ended(old_war, new_war):  # war ended
        clan_home = old_war.clan
        log.info(
            "War ended between: {} and {}, type={}".format(old_war.clan, old_war.opponent, old_war.type))

        condition = clan_home.tag in database.MEM_mappings_clanwatch.keys()
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

            channel, misses = bot_functions.end_war(old_war,total_attacks,log,database,bot)
            if channel is not None and misses is not None:
                await channel.send(misses)

@coc_client.event
@coc.WarEvents.war_attack()  # only if the clan war is registered in MEM_mappings_clan_currentwars
async def current_war_stats(attack, war):
    attacker = attack.attacker
    if attacker.is_opponent or not war.is_cwl: #regular war end/start is ok, only during cwl the war states are messy
        return

    attacker_clan = attacker.clan
    log.info("\t New cwl attack captured. clan={}, attacker={}".format(attacker_clan.tag, attacker))

    # check if this is the start of a new cwl war
    new_cwl_war = False
    if not attacker_clan.tag in database.MEM_current_cwl_wars.keys():
        # clan does not have a cwl war previously
        database.reset_cwl_war_data(attacker_clan.tag, war)
        log.info("\t\tThis is the first cwl attack of the first war of clan {}. Saving war object".format(attacker_clan.tag))
    else:
        # clan has a cwl war previously
        channel, misses=bot_functions.close_cwl_war(database, bot, log, attacker_clan, war, 1)
        if channel is not None and misses is not None:
            await channel.send(misses)

# when member joining or leaving, send a message to discord to prompt changing their roles
@coc_client.event
@coc.ClanEvents.member_join()
async def on_clan_member_join(member, clan):
    messages, tochannel = bot_functions.log_member_movement(member.tag, member.name, clan.name, clan.tag, "joined",
                                                            database,bot)
    if len(messages) > 0:
        for m in messages:
            await tochannel.send(m)

# when member joining or leaving, send a message to discord to prompt changing their roles
@coc_client.event
@coc.ClanEvents.member_leave()
async def on_clan_member_leave(member, clan):
    messages, tochannel = bot_functions.log_member_movement(member.tag, member.name, clan.name, clan.tag, "left",
                                                            database,bot)
    if len(messages) > 0:
        for m in messages:
            await tochannel.send(m)

@tasks.loop(hours=6)
async def check_scheduled_task():
    hr=6
    now = datetime.datetime.now()
    season_end = utils.get_season_end()
    season_start=utils.get_season_start()
    log.info("\t>>> Checking scheduled task every {} hours. Time now is {}. The current season will end {}".format(hr,now,
                                                                                                                   season_end))
    hours_before_end = (season_end - now).total_seconds()/3600
    # checking un-closed wars
    for clantag, warTuple in database.MEM_current_cwl_wars.items():
        warobj=warTuple[1]
        if warobj.end_time is not None and warobj.end_time.time < datetime.datetime.now():
            log.info("\t>>> Closing un-closed cwl wars for {}".format(clantag))
            attacker_clan=await coc_client.get_clan(clantag)
            channel, misses= bot_functions.close_cwl_war(database, bot, log, attacker_clan, None, 1)
            if channel is not None and misses is not None:
                await channel.send(misses)

    #    if days_before_end <=1:
    if hours_before_end >0 and hours_before_end <= hr:
        log.info("\t>>> End of season reached ({}hr), running scheduled task. Registered clans={}".format(
            hours_before_end, len(database.MEM_mappings_clanwatch.items())))

        count_clans = 0
        most_stars = 0
        most_stars_winner = None
        least_misses = -1
        least_misses_winner = None

        # send clan war digest
        for clantag, clanwatch in database.MEM_mappings_clanwatch.items():
            try:
                count_clans += 1

                guild = bot.get_guild(clanwatch._guildid)
                if guild is not None:
                    channel_id = clanwatch._channel_warsummary
                    if channel_id is not None:
                        channel_id = dataformatter.parse_channel_id(channel_id)
                    channel = disnake.utils.get(guild.channels, id=channel_id)
                    if channel is not None:
                        fromdate = utils.get_season_start()
                        war_miss, cwl_miss, war_overview, war_plot, summary = \
                            bot_functions.prepare_wardigest(fromdate, now, clantag,clanwatch._name, database)

                        if war_miss is None or cwl_miss is None or war_overview is None or war_plot is None:
                            await channel.send("Not enough war data for {}, {}".format(clantag, clanwatch._name))
                            return
                        await channel.send("**End of Season Clan Summary** (season start {}, end {})".format(season_start, season_end))
                        await channel.send(war_miss)
                        await channel.send(cwl_miss)
                        await channel.send(war_overview)
                        await channel.send(file=war_plot,
                                           content="**Clan war data plot ready for download**:")

                        totalstars = int(summary['Total stars'])
                        totalmisses = int(summary['Total unused attacks'])
                        if totalmisses == 0 and totalmisses == 0:
                            totalmisspercent = 0
                        else:
                            totalmisspercent = round(totalmisses*100 / (totalstars + totalmisses), 1)
                        if totalstars > most_stars:
                            most_stars = totalstars
                            most_stars_winner = (clantag, clanwatch._name)
                        if least_misses == -1 or totalmisspercent < least_misses:
                            least_misses = totalmisspercent
                            least_misses_winner = (clantag, clanwatch._name)
            except:
                print("Encountered error, time {}".format(datetime.datetime.now()))
                print(traceback.format_exc())
        # send clan family performer, and update donation points
        for clantag, clanwatch in database.MEM_mappings_clanwatch.items():
            try:
                guild = bot.get_guild(clanwatch._guildid)
                if guild is not None:
                    channel_id = clanwatch._channel_warsummary
                    if channel_id is not None:
                        channel_id = dataformatter.parse_channel_id(channel_id)
                    channel = disnake.utils.get(guild.channels, id=channel_id)
                    if channel is not None:
                        msg = "**Clan Family Best Performers** ({} clans registered with {})\n".format(count_clans,
                                                                                                       BOT_NAME)
                        msg += "\tMost war stars: {} by {} \n".format(most_stars, str(most_stars_winner))
                        msg += "\tLowest missed attack: {}% by {}".format(least_misses, str(least_misses_winner))
                        await channel.send(msg)

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
            except:
                print("Encountered error, time {}".format(datetime.datetime.now()))
                print(traceback.format_exc())
    else:
        log.info("\t>>> {} hours till the end of season".format(hours_before_end))


check_scheduled_task.start()
bot.run(TOKEN)
