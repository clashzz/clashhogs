import logging, pickle
import sys
import coc
from discord.ext import commands, tasks
import discord
import asyncio
from discord import app_commands


from coc import utils
# t=utils.get_season_end()
#
# file = open("/home/zz/Work/sidekickassist/tmp/tmp_currentwards.pk",'rb')
# object_file = pickle.load(file)
# print(object_file)
# exit(1)

'''
coc 1.3, using tags works
'''


bot = commands.Bot(command_prefix='=',help_command=None, intents=discord.Intents.all())

@bot.tree.command()
async def slash(interaction: discord.Interaction, number: int, string: str):
    await interaction.response.send_message(f'{number=} {string=}', ephemeral=True)

@bot.event
async def on_ready():
    print("syncing")
    await bot.tree.sync()
    print("done")

bot.run(sys.argv[3])

# After
# @tasks.loop(seconds=5)
# async def my_task():
#     print("testing")
#
#
# async def main():
#     async with bot:
#         my_task.start()
#         await bot.start(sys.arg[3])
#
# asyncio.run(main())

