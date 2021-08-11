import os

import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user or message.channel.name!="dev-test":
        return

    if 'missed attack' in message.content:
        await message.channel.send("missed attack recorded in {}: {}".format(message.channel.name,
                                                                             message.content))

client.run(TOKEN)