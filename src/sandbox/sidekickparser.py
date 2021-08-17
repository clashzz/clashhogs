from sandbox import util
'''
When client enters their channel using the format #channel-name, the value passed to the discord api will not be
exactly the channel name, or id. It needs to be parsed to get the channel ID

Currently the format will look like:
<#idnumber>, e.g., <#9330029203202>
'''
def parse_channel_id(value:str):
    hash=value.index("#")
    try:
        return int(value[hash+1:len(value)-1])
    except:
        print("Cannot parse channel ID {}".format(value))
        return -1

def parse_missed_attack(message:str):
    missed_attacks={}
    if "remaining attack" in message.lower():  # to check remaining attacks
        try:
            sidx = message.lower().index("2 remaining attack")
            remaining_attacks = 2

            text = message[sidx:]
            extract_remaining_attacks(text, remaining_attacks,missed_attacks)
        except:
            pass

        try:
            sidx = message.lower().index("1 remaining attack")
            remaining_attacks = 1

            text = message[sidx:]
            extract_remaining_attacks(text, remaining_attacks,missed_attacks)
        except:
            pass

        return missed_attacks

#todo: more testing
def extract_remaining_attacks(text:str, remaining_attacks:int, missed:dict):
    lines = text.split("\n")
    for rowidx in range(1, len(lines)):
        row = lines[rowidx]
        if (row.startswith(":b") or row.startswith(":s:")):
            startindex = row.rindex(":")
            player_name = util.normalise_name(row[startindex + 1:])
            missed[player_name]=remaining_attacks
        else:
            break