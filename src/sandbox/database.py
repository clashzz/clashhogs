'''
This file implements data storage.
Currently everything saved in member.
TODO: use mongodb
'''

#guild id and name
guilds={}

#key=guild id|clan name (e.g., 3492301120|myclan
#value=a list of tuple (x, y) where x is the sidekick channel (name) of war feed, y is the channel (name) to tally
#missed attacks
guild_skchannels_warmiss={}

'''
Add a mapped triple to war missed attacks channels
- pair: is a tuple (x, y) where x is the sidekick channel (name) of war feed, y is the channel (name) to tally
missed attacks, z is the clan name
- guild_id: the discord id of the guild
'''
def add_warmiss_mapped_channels(pair:tuple, guild_id):
    key  = str(guild_id)+"|"+str(pair[0])
    guild_skchannels_warmiss[key] = str(guild_id)+"|"+str(pair[1])