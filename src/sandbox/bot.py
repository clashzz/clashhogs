import os, datetime
from dotenv import load_dotenv
import discord
from discord.ext import commands
from sandbox import database, sidekickparser

##########
# Init   #
##########
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
BOT_NAME='Sidekick Assist v1'
SIDEKICK_NAME='Sidekick II'
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
@bot.command(name='config', help='This command is used to map your sidekick war feed channel to another channel,'
                                 ' where missed attacks will be automatically tallied. '
                                 '\nE.g., config sidekick-war missed-attacks'
                                 '\nAll parameters must be a single word without space characters. The channels must'
                                 ' have the # prefix')
@commands.has_role('co-leaders')
async def config(ctx, from_channel:str, to_channel:str):
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
        "Okay. Sidekick war feed from #{} will be automatically processed, with missed attacks forwarded to #{}. "
        "Please ensure {} has access to these channels (read and write)".
            format(from_channel, to_channel, BOT_NAME))

@config.error
async def config_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send("'config' requires two arguments: sidekick war feed channel, and the channel "
                               "to which missed attacks are to be forwarded (all as one word). \n"
                               "E.g., 'config sidekick-war missed-attacks'")
    if isinstance(error, commands.MissingPermissions):
        await ctx.channel.send(
            "'config' can only be used by the {} role(s). You do not seem to have permission to use this command".format('admin'))

###################################################################
#This method is used to monitor to messages posted on the server, intercepts sidekick war feed,
#extracts missed attacks, and post those data to a specific channel
#see also the 'config' command
###################################################################
@bot.event
async def on_message(message):
    if message.author.name==SIDEKICK_NAME or message.content.startswith("test "):
        #sidekick posted a message, let's check if it is war feed
        from_channel = str(message.guild.id)+"|"+str(message.channel.id)
        if from_channel in database.guild_skchannels_warmiss.keys():
            #we captured a message from the sidekick war feed channel. Now check if it is about missed attackes
            if 'remaining attack' in message.content.lower():
                missed_attacks=sidekickparser.parse_missed_attack(message.content)

                #now send the message to the right channel
                to_channel =database.guild_skchannels_warmiss[from_channel]
                to_channel = int(to_channel[to_channel.index('|')+1:])
                to_channel = discord.utils.get(message.guild.channels, id=to_channel)

                message="War missed attack on {}:\n".format(datetime.datetime.now())
                for k, v in missed_attacks.items():
                    message+="\t"+str(k)+"\t"+str(v)+"\n"
                await to_channel.send(message)
        else:
            return

    await bot.process_commands(message)
    # if 'missed attack' in message.content:
    #     await message.channel.send("missed attack recorded in {}: {}".format(message.channel.name,
    #                                                                          message.content))
    # await bot.process_commands(message)

# @bot.command(name='missed', help='This command shows the tally of missed attacks from a starting date ('
#                                  'provided in the format of DD/MM/YYYY). When the date is missing, data'
#                                  ' from the last 30 days are collected.')
# async def missed_attacks(ctx, fromdate:str):
#     try:
#         from_date=datetime.datetime.strptime(fromdate, '%d/%m/%Y')
#     except:
#         from_date=datetime.datetime.now() - datetime.timedelta(30)
#     print(from_date)
#
#     await ctx.send("Missed attacks from {}".format(from_date))

# @bot.command(name='wardigest')
# @commands.has_role('co-leaders')
# async def wardigest(ctx, fromdate:str):
#     pass

# @missed_attacks.error
# async def missedattacks_error(ctx, error):
#     if isinstance(error, commands.MissingPermissions):
#         owner = ctx.guild.owner
#         direct_message = await owner.create_dm()
#         await direct_message.send("Missing Permissions")




# @bot.event
# async def on_command_error(ctx, error):
#     if isinstance(error, commands.errors.CheckFailure):
#         await ctx.send('You do not have the correct role for this command.')


bot.run(TOKEN)