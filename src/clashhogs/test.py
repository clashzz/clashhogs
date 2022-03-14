import logging, pickle
import sys
import coc
from discord.ext import commands, tasks
import asyncio

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

client = coc.login(
    sys.argv[1], sys.argv[2],
    key_names="coc.py tests",
    client=coc.EventsClient,
)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger()
bot = commands.Bot(command_prefix='?', help_command=None)

# After
@tasks.loop(seconds=5)
async def my_task():
    print("testing")


async def main():
    async with bot:
        my_task.start()
        await bot.start('replace')

asyncio.run(main())

client.loop.run_forever()