import os, datetime, time
from dotenv import load_dotenv
import discord
from discord.ext import commands
from skassist import database, sidekickparser
import traceback, sys
from pathlib import Path

##########
# Init   #
##########
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
BOT_NAME='Sidekick Assist v1'
SIDEKICK_NAME='Sidekick II'
PERMISSION_WARMISS="admin"
PERMISSION_WARDIGEST="developers"
PERMISSION_CLANDIGEST="developers"
BOT_WAIT_TIME=20
bot = commands.Bot(command_prefix='?', help_command=None)


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    #register each connected guild to the bot database
    print('The following guilds are connected with the bot:')
    for guild in bot.guilds:
        database.guilds[guild.id] = guild.name
        print('\t{}, {}'.format(guild.name, guild.id))
        database.check_database(guild.id)#todo

#########################################################
# Register the help command
#########################################################
@bot.command()
async def help(context, command=None):
    if command is None:
        await context.send("{} supports the following commands. Run **?help [command]** for how to use them. Also see"
                           " details at https://github.com/clashzz/sidekickassist:\n"
                       "\t\t - **warmiss**: set up a channel for forwarding missed attacks\n"
                       "\t\t - **wardigest**: analyse and produce a report for a clan's past war peformance\n"
                       "\t\t - **clandigest**: analyse and produce a report for a clan's activities (excl. war)".format(BOT_NAME))
    elif command == 'warmiss':
        await context.send('This command is used to map your sidekick war feed channel to another channel,'
                                 ' where missed attacks will be automatically tallied. '
                                 '\n**Usage:** ?warmiss [option] #sidekick-war #missed-attacks [clanname] \n'
                                 '\t\t - [option]: \n'
                                 '\t\t\t\t -l: to list current channel mappings (ignore other parameters when using this option) \n'
                           '\t\t\t\t -a: to add a channel mapping \n'
                           '\t\t\t\t -r: to remove a channel mapping: \n'
                                 '\t\t - [clanname] must be a single word'
                                 '\nAll parameters must be a single word without space characters. The channels must'
                                 ' have the # prefix')
    elif command == 'clandigest':
        await context.send('This command is used to generate clan digest for the current season '
                                     'using data from the Sidekick clan feed channel. \n\n'
                                    '**Usage**: ?clandigest #sidekick-clan-feed-channel #output-target-channel [clanname] \n'
                                     '\t\t - [clanname] must be a single word\n'
                                     '\n{} must have read and write permissions to both channels.'.format(BOT_NAME))
    elif command == 'wardigest':
        await context.send('This command is used to generate clan war digest using data from the Sidekick clan war feed channel. \n\n'
                                    '**Usage**: ?wardigest #sidekick-war-feed-channel #output-target-channel [clanname] [dd/mm/yyyy]'
                                    ' [OPTIONAL:dd/mm/yyyy]\n'
                                    '\t\t - [clanname]: must be one word\n'
                                    '\t\t - [dd/mm/yyyy]: the first is the start date (required), the second is the end date (optional). '
                                    'When the end date is not provided, the present date will be used\n'
                                     '\n{} must have read and write permissions to both channels.'.format(BOT_NAME))
    else:
        await context.send('Command {} does not exist.'.format(command))

#########################################################
# This method is used to configure the discord channels
# to automatically tally missed attacks
#########################################################
@bot.command(name='warmiss')
@commands.has_role(PERMISSION_WARMISS)
async def warmiss(ctx, option:str, from_channel=None, to_channel=None, clan=None):
    #list current mappings
    if option=="-l":
        mappings = database.get_warmiss_mappings_for_guild_db(ctx.guild.id)
        msg="The follow channels are mapped for war missed attacks:\n"
        for m in mappings:
            fc = discord.utils.get(ctx.guild.channels, id=m[0])
            tc = discord.utils.get(ctx.guild.channels, id=m[1])
            clanname=m[2]
            msg+="\t\tFrom: **{}**,\tTo: **{}**,\t Clan: **{}**\n".format(fc.mention, tc.mention, clanname)
        await ctx.channel.send(msg)
        return

    #if other options, then the other three params are required
    if from_channel is None or to_channel is None or clan is None:
        await ctx.channel.send("'warmiss' requires arguments. Run ?help warmiss for details")
        return

    # check if the channels already exist
    check_ok = True
    from_channel_id = sidekickparser.parse_channel_id(from_channel)
    to_channel_id = sidekickparser.parse_channel_id(to_channel)
    channel = discord.utils.get(ctx.guild.channels, id=from_channel_id)
    if channel is None:
        await ctx.channel.send(
                "The channel {} does not exist. Please create it first, and give {} 'Send messages' and 'Read message history'"
                " permissions to that channel.".format(from_channel, BOT_NAME))
        check_ok = False
    channel = discord.utils.get(ctx.guild.channels, id=to_channel_id)
    if channel is None:
        await ctx.channel.send(
                "The channel {} does not exist. Please create it first, and give {} 'Send messages' and 'Read message history'"
                " permissions to that channel.".format(to_channel, BOT_NAME))
        check_ok = False

    if not check_ok:
        return

    # checks complete, all good

    if option=="-a": #adding a mapping
        pair = (from_channel_id, to_channel_id)
        database.add_channel_mappings_warmiss_db(pair, ctx.guild.id, clan) #TODO
        await ctx.channel.send(
            "Okay. Missed attacks for **{}** from {} will be extracted and forwarded to {}. "
            "Please ensure {} has access to these channels (read and write)".
                format(clan, from_channel, to_channel, BOT_NAME))

    if option=="-r": #remove a channel
        database.remove_warmiss_mappings_for_guild_db(ctx.guild.id, from_channel_id)
        await ctx.channel.send(
            "Mapping removed")

@warmiss.error
async def warmiss_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send("'warmiss' requires arguments. Run ?help warmiss for details")
    if isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole):
        await ctx.channel.send(
            "'warmiss' can only be used by the {} role(s). You do not seem to have permission to use this command".format(PERMISSION_WARMISS))
    else:
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

#########################################################
# This method is used to process clan log summary
#########################################################
@bot.command(name='clandigest')
@commands.has_role('developers')
async def clandigest(ctx, from_channel:str, to_channel:str, clanname:str):
    #check if the channels already exist
    check_ok=True
    from_channel_id=sidekickparser.parse_channel_id(from_channel)
    to_channel_id=sidekickparser.parse_channel_id(to_channel)
    channel_from = discord.utils.get(ctx.guild.channels, id=from_channel_id)
    if channel_from is None:
        await ctx.channel.send(
            "The channel {} does not exist. This should be your sidekick clan feed channel, and allows 'Read message history'"
            " and 'Send messages' permissions for {}.".format(from_channel, BOT_NAME))
        check_ok=False
    channel_to = discord.utils.get(ctx.guild.channels, id=to_channel_id)
    if channel_to is None:
        await ctx.channel.send(
            "The channel {} does not exist. Please create it first, and give {} 'Send messages'"
            " permissions to that channel.".format(to_channel, BOT_NAME))
        check_ok=False

    if not check_ok:
        return

    #start_time=datetime.datetime.now() -datetime.timedelta(seconds=BOT_WAIT_TIME)
    messages = await channel_from.history(limit=20, oldest_first=False).flatten()
    messages.reverse()
    data_clanbest, season_id, sidekick_messages=sidekickparser.parse_clan_best(messages)

    date_season_start=sidekickparser.parse_season_start(season_id)
    messages=await channel_from.history(after=date_season_start, limit=None).flatten()
    data_clanactivity=sidekickparser.parse_clan_activity(messages)

    msg = "{} clan feed digest - {}:\n\n **Loots and Attacks:**".format(clanname, season_id.replace("\n"," "))
    for k, v in data_clanbest.items():
        msg+="\t"+k+": "+str(v)+"\n"
    await channel_to.send(msg+"\n")

    msg="**Member Activity Counts** (upgrade completes, league promotion, super troop boosts etc):\n"
    for k, v in data_clanactivity.items():
        msg+="\t"+k+": "+str(v)+"\n"
    await channel_to.send(msg+"\n")

    #msg = "\n**Clan Best Messages Forward:**"
    # for m in sidekick_messages:
    #     if len(m.embeds)>0:
    #         await channel_to.send(content=m.content, embed=m.embeds[0])
    #     else:
    #         await channel_to.send(content=m.content)

@clandigest.error
async def clandigest(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send("'clandigest' requires three arguments. Run ?help clandigest for details")
    if isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole):
        await ctx.channel.send(
            "'clandigest' can only be used by the {} role(s). You do not seem to have permission to use this command".format(PERMISSION_CLANDIGEST))


#########################################################
# This method is used to process clan war summary
#########################################################
@bot.command(name='wardigest')
@commands.has_role('developers')
async def wardigest(ctx, from_channel:str, to_channel:str, clanname:str, fromdate:str, todate=None):
    #check if the channels already exist
    check_ok=True
    from_channel_id=sidekickparser.parse_channel_id(from_channel)
    to_channel_id=sidekickparser.parse_channel_id(to_channel)
    channel_from = discord.utils.get(ctx.guild.channels, id=from_channel_id)
    if channel_from is None:
        await ctx.channel.send(
            "The channel {} does not exist. This should be your sidekick war feed channel, and allows 'Read message history'"
            " and 'Send messages' permissions for {}.".format(from_channel, BOT_NAME))
        check_ok=False
    channel_to = discord.utils.get(ctx.guild.channels, id=to_channel_id)
    if channel_to is None:
        await ctx.channel.send(
            "The channel {} does not exist. Please create it first, and give {} 'Send messages'"
            " permissions to that channel.".format(to_channel, BOT_NAME))
        check_ok=False

    if not check_ok:
        return

    try:
        fromdate=datetime.datetime.strptime(fromdate, "%d/%m/%Y")
    except:
        fromdate=datetime.datetime.now() -datetime.timedelta(30)
        await ctx.channel.send(
            "The start date you specified does not confirm to the required format dd/mm/yyyy. The date 30 days ago from today"
            " will be used instead.".format(to_channel, BOT_NAME))
    try:
        if todate is not None:
            todate=datetime.datetime.strptime(todate, "%d/%m/%Y")
        else:
            todate=datetime.datetime.now()
    except:
        todate=datetime.datetime.now()
        await ctx.channel.send(
            "The end date you specified does not confirm to the required format dd/mm/yyyy. The current date"
            " will be used instead.".format(to_channel, BOT_NAME))

    delta = todate - fromdate
    if delta.days > 60:
        await ctx.channel.send("Fetching data covering more than 60 days is not recommended as this leads to slow response"
                               " time. If you wish to analyse historical data, set your start and end dates accordingly.")
        return

    await ctx.channel.send("This may take a few seconds while I retrieve data from Sidekick...")

    # gather missed attacks data
    messages=await channel_from.history(after=fromdate, limit=None).flatten()
    data_missed=sidekickparser.parse_warfeed_missed_attacks(messages, SIDEKICK_NAME)

    msg = "**{} clan war digest between {} and {}**:\n\n **Missed Attacks:** \n".format(clanname, fromdate, todate)
    for k, v in data_missed.items():
        msg+="\t"+k+": "+str(v)+"\n"
    await channel_to.send(msg+"\n")

    #gather war data
    last_message=messages[len(messages)-1]
    if str(last_message.attachments) == "[]":  # Checks if there is an attachment on the message
        await ctx.channel.send("Cannot find the Sidekick war data export in the {} channel. Run **/export ...** "
                               "in that channel first and ensure no other messages are sent before you run this command.".format(from_channel))
    else:  # If there is it gets the filename from message.attachments
        clanid = str(ctx.guild.id)
        targetfolder = "db/" + clanid
        Path(targetfolder).mkdir(parents=True, exist_ok=True)
        split_v1 = str(last_message.attachments).split("filename='")[1]
        filename = targetfolder+"/"+str(split_v1).split("' ")[0]
        if filename.endswith(".csv"):  # Checks if it is a .csv file
            await last_message.attachments[0].save(fp=filename)  # saves the file
        #now process the file and extract data
        clan_war_data=sidekickparser.parse_sidekick_war_data_export(filename, clanname, fromdate,data_missed)
        data_for_plot, clan_summary=clan_war_data.output_clan_war_data(targetfolder)
        msg = "\n**Clan Overview**:\n"
        for k, v in clan_summary.items():
            msg += "\t" + k + ": " + str(v) + "\n"
        await channel_to.send(msg + "\n")

        figure = data_for_plot.plot(kind='bar',stacked=True).get_figure()
        figure.savefig(targetfolder+'/clan_war_data.jpg', format='jpg')
        #now fetch that file and send it to the channel
        fileA = discord.File(targetfolder+"/clan_war_data.csv")
        await channel_to.send(file=fileA, content="**Clan war data analysis ready for download**:")
        fileB = discord.File(targetfolder + "/clan_war_data.jpg")
        await channel_to.send(file=fileB,
                              content="**Clan war data plot ready for download**:")

        #save individual war data
        print("\tsaving war data for individuals ({})...".format(datetime.datetime.now()))
        database.save_individual_war_data(ctx.guild.id,clan_war_data)
        print("\tdone ({})".format(datetime.datetime.now()))



@wardigest.error
async def wardigest(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send("'wardigest' requires four arguments. Run ?help wardigest for details")
    if isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole):
        await ctx.channel.send(
            "'wardigest' can only be used by the {} role(s). You do not seem to have permission to use this command".format(PERMISSION_CLANDIGEST))
    else:
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

###################################################################
#This method is used to monitor to messages posted on the server, intercepts sidekick war feed,
#extracts missed attacks, and post those data to a specific channel
#see also the 'config' command
###################################################################
@bot.event
async def on_message(message):
    #debugging#
    print("botname:"+message.author.name)
    print("sidekick in name:"+str(SIDEKICK_NAME in message.author.name))
    print("has remaining attacks:"+str('remaining attack' in message.content.lower())+"\n")
    #debugging#

    if SIDEKICK_NAME in message.author.name or 'DeadSages Elite' in message.content:
        #sidekick posted a message, let's check if it is war feed
        try:
            if database.has_warmiss_fromchannel(message.guild.id,message.channel.id):
                #we captured a message from the sidekick war feed channel. Now check if it is about missed attackes
                if 'remaining attack' in message.content.lower():
                    print("\t captured war miss messages...")
                    time.sleep(BOT_WAIT_TIME)
                    print("\t waiting done")

                    messages = await message.channel.history(limit=10, oldest_first=False).flatten()
                    messages.reverse()
                    missed_attacks=sidekickparser.parse_warfeed_missed_attacks(messages)
                    # message_content=""
                    # for m in messages:
                    #     #if m.author == BOT_NAME:# or m.author.
                    #         message_content+=m.content+"\n"
                    #
                    # missed_attacks=sidekickparser.parse_missed_attack(message_content)

                    #now send the message to the right channel
                    print("\tmessage prepared for: {}"+str(missed_attacks))
                    to_channel, clan =database.get_warmiss_tochannel(message.guild.id,message.channel.id)
                    to_channel = discord.utils.get(message.guild.channels, id=to_channel)

                    message="War missed attack for **{} on {}**:\n".format(clan, datetime.datetime.now())
                    for k, v in missed_attacks.items():
                        message+="\t"+str(k)+"\t"+str(v)+"\n"
                    await to_channel.send(message)
            else:
                return
        except:
            print(traceback.format_exc())
    else:
        await bot.process_commands(message)

bot.run(TOKEN)