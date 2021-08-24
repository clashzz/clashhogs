import os, datetime, time
from dotenv import load_dotenv
import discord
from discord.ext import commands
from skassist import database, sidekickparser, util
import traceback
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
bot = commands.Bot(command_prefix='?')



@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    #register each connected guild to the bot database
    print('The following guilds are connected with the bot:')
    for guild in bot.guilds:
        database.guilds[guild.id] = guild.name
        print('\t{}, {}'.format(guild.name, guild.id))

#########################################################
# This method is used to configure the discord channels
# to automatically tally missed attacks
#########################################################
@bot.command(name='warmiss', help='This command is used to map your sidekick war feed channel to another channel,'
                                 ' where missed attacks will be automatically tallied. '
                                 '\nE.g., warmiss sidekick-war missed-attacks'
                                 '\nAll parameters must be a single word without space characters. The channels must'
                                 ' have the # prefix')
@commands.has_role(PERMISSION_WARMISS)
async def warmiss(ctx, from_channel:str, to_channel:str):
    #check if the channels already exist
    check_ok=True
    from_channel_id=sidekickparser.parse_channel_id(from_channel)
    to_channel_id=sidekickparser.parse_channel_id(to_channel)
    channel = discord.utils.get(ctx.guild.channels, id=from_channel_id)
    if channel is None:
        await ctx.channel.send(
            "The channel {} does not exist. Please create it first, and give {} 'Send messages' and 'Read message history'"
            " permissions to that channel.".format(from_channel, BOT_NAME))
        check_ok=False
    channel = discord.utils.get(ctx.guild.channels, id=to_channel_id)
    if channel is None:
        await ctx.channel.send(
            "The channel {} does not exist. Please create it first, and give {} 'Send messages' and 'Read message history'"
            " permissions to that channel.".format(to_channel, BOT_NAME))
        check_ok=False

    if not check_ok:
        return

    #checks complete, all good
    pair = (from_channel_id, to_channel_id)
    database.add_warmiss_mapped_channels(pair, ctx.guild.id)
    await ctx.channel.send(
        "Okay. Missed attacks from {} will be extracted and forwarded to {}. "
        "Please ensure {} has access to these channels (read and write)".
            format(from_channel, to_channel, BOT_NAME))

@warmiss.error
async def warmiss_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send("'warmiss' requires two arguments. Run ?help warmiss for details")
    if isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole):
        await ctx.channel.send(
            "'warmiss' can only be used by the {} role(s). You do not seem to have permission to use this command".format(PERMISSION_WARMISS))

#########################################################
# This method is used to process clan log summary
#########################################################
@bot.command(name='clandigest', help='This command is used to generate clan digest using data from the Sidekick clan feed channel. \n'
                                    'Usage: ?clandigest #sidekick-clan-feed-channel #output-target-channel [clanname] \n'
                                     '{} must have read and write permissions to both channels.'.format(BOT_NAME))
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
@bot.command(name='wardigest', help='This command is used to generate clan war digest using data from the Sidekick clan war feed channel. \n'
                                    'Usage: ?clanwar #sidekick-war-feed-channel #output-target-channel [clanname] [dd/mm/yyyy]\n'
                                     '{} must have read and write permissions to both channels.'.format(BOT_NAME))
@commands.has_role('developers')
async def wardigest(ctx, from_channel:str, to_channel:str, clanname:str, fromdate:str):
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
            "The date you specified does not confirm to the required format dd/mm/yyyy. The date 30 days ago from today"
            " will be used instead.".format(to_channel, BOT_NAME))
    await ctx.channel.send("This may take a few seconds while I retrieve data from Sidekick...")

    # gather missed attacks data
    messages=await channel_from.history(after=fromdate, limit=None).flatten()
    data_missed=sidekickparser.parse_warfeed_missed_attacks(messages, SIDEKICK_NAME)

    msg = "**{} clan war digest from {}**:\n\n **Missed Attacks:** \n".format(clanname, fromdate)
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
        targetfolder = "tmp/" + clanid
        Path(targetfolder).mkdir(parents=True, exist_ok=True)
        split_v1 = str(last_message.attachments).split("filename='")[1]
        filename = targetfolder+"/"+str(split_v1).split("' ")[0]
        if filename.endswith(".csv"):  # Checks if it is a .csv file
            await last_message.attachments[0].save(fp=filename)  # saves the file
        #now process the file and extract data
        clan_war_data=sidekickparser.parse_sidekick_war_data_export(filename, clanname, fromdate,data_missed)
        data_for_plot=clan_war_data.output_clan_war_data(targetfolder)
        figure = data_for_plot.plot(kind='bar',stacked=True).get_figure()
        figure.savefig(targetfolder+'/clan_war_data.jpg', format='jpg')
        #now fetch that file and send it to the channel
        fileA = discord.File(targetfolder+"/clan_war_data.csv")
        await channel_to.send(file=fileA, content="**Clan war data analysis ready for download**:")
        fileB = discord.File(targetfolder + "/clan_war_data.jpg")
        await channel_to.send(file=fileB,
                              content="**Clan war data plot ready for download**:")


@wardigest.error
async def wardigest(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send("'wardigest' requires four arguments. Run ?help wardigest for details")
    if isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingRole):
        await ctx.channel.send(
            "'wardigest' can only be used by the {} role(s). You do not seem to have permission to use this command".format(PERMISSION_CLANDIGEST))
    else:
        print("Error")

###################################################################
#This method is used to monitor to messages posted on the server, intercepts sidekick war feed,
#extracts missed attacks, and post those data to a specific channel
#see also the 'config' command
###################################################################
@bot.event
async def on_message(message):
    if message.author.name==SIDEKICK_NAME or 'DeadSages Elite' in message.content:
        #sidekick posted a message, let's check if it is war feed
        try:
            from_channel = str(message.guild.id)+"|"+str(message.channel.id)
            if database.has_warmiss_fromchannel(from_channel):
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
                    to_channel =database.get_warmiss_tochannel(from_channel)
                    to_channel = int(to_channel[to_channel.index('|')+1:])
                    to_channel = discord.utils.get(message.guild.channels, id=to_channel)

                    message="War missed attack on {}:\n".format(datetime.datetime.now())
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