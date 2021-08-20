from sandbox import util
import re
'''
When client enters their channel using the format #channel-name, the value passed to the discord api will not be
exactly the channel name, or id. It needs to be parsed to get the channel ID

Currently the format will look like:
<#idnumber>, e.g., <#9330029203202>
'''

NUMBER_REGEX=r'^\d{1,3}(,\d{3})*(\.\d+)?$'
SIDEKICK_COMMAND_CLANBEST="/best"
SIDEKICK_CLANBEST_GOLDLOOT="Gold Looted"
SIDEKICK_CLANBEST_ELIXIRLOOT="Elixir Looted"
SIDEKICK_CLANBEST_DELOOT="Dark Elixir Looted"
SIDEKICK_CLANBEST_DONATIONS="Donations"
SIDEKICK_CLANBEST_ATTACKS="Attack Wins"
SIDEKICK_CLANBEST_TITLE="Gainers This Season"

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

'''

'''
def parse_clan_best(discord_messages:list):
    data={}
    start_index, title=find_start_message_index(discord_messages)
    if start_index is None:
        return data

    tally = 0
    property = ""
    for i in range(start_index, len(discord_messages)):
        m=discord_messages[i]
        #the message is encoded as an embed object, containing fields
        if len(m.embeds) == 0:
            continue

        for embed in m.embeds:
            if len(embed.fields)==0:
                continue


            for field in embed.fields:
                if SIDEKICK_CLANBEST_GOLDLOOT in field.name:
                    if property!="":
                        data[property]=tally
                        tally=0

                    property = SIDEKICK_CLANBEST_GOLDLOOT
                    tally+=extract_values(field.value)
                elif SIDEKICK_CLANBEST_DELOOT in field.name:
                    if property!="":
                        data[property]=tally
                        tally=0

                    property=SIDEKICK_CLANBEST_DELOOT
                    tally+=extract_values(field.value)
                elif SIDEKICK_CLANBEST_ELIXIRLOOT in field.name:
                    if property!="":
                        data[property]=tally
                        tally=0

                    property = SIDEKICK_CLANBEST_ELIXIRLOOT
                    tally+=extract_values(field.value)
                elif SIDEKICK_CLANBEST_DONATIONS in field.name:
                    if property!="":
                        data[property]=tally
                        tally=0

                    property=SIDEKICK_CLANBEST_DONATIONS
                    tally += extract_values(field.value)
                elif SIDEKICK_CLANBEST_ATTACKS in field.name:
                    if property!="":
                        data[property]=tally
                        tally=0

                    property=SIDEKICK_CLANBEST_ATTACKS
                    tally += extract_values(field.value)
                elif field.name=='\u200b':
                    #should continue from the previous 'name'
                    tally+=extract_values(field.value)

    if property != "":
        data[property] = tally

    return data

def find_start_message_index(messages:list):
    for i in range(len(messages)-1, -1, -1):
        m=messages[i]
        if len(m.embeds) == 0:
            continue

        for e in m.embeds:
            if type(e.title) is str and SIDEKICK_CLANBEST_TITLE in e.title:
                return i, e.description
    return None, None


#example text: '<:s:351520745203171329> Gold Looted'
# def extract_name(text:str):
#     start = text.index(">")
#     return text[start+1:].strip()
'''
example text:

<:s:357251235964911637>` 159,064,963 ` `     Jerebear `
<:s:357251236250255361>` 118,775,700 ` `      nicktsy `
<:s:357251236686462979>` 100,097,712 ` ` Jerebear III `
<:s:357251236082352131>`  76,284,745 ` `          Z.Z `
<:s:357251236472291328>`  69,690,122 ` `       Arnold `
'''
def extract_values(text:str):
    lines=text.split("\n")
    sum=0
    for l in lines:
        if '>' in l:
            l=re.sub("[^0-9a-zA-Z\s]+", "", l[l.index('>')+1:].strip()) .strip()
        try:
            sum+=int(l.split()[0])
        except:
            pass
    return sum