import datetime
import pandas as pd

from clashhogs import util, models
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
SIDEKICK_CLANACTIVITY_KEYWORDS=['upgraded','is now','boosted','pushed','unlocked']

def parse_channel_id(value:str):
    try:
        hash = value.index("#")
        return int(value[hash+1:len(value)-1])
    except:
        return -1

def parse_sidekick_war_data_export(in_csv, clanname, from_date,
                                   missed_attacks:dict,
                                   col_attacker_tag="tag",
                                   col_attacker="name", col_stars="stars",
                                   col_defenderth="defenderTH",
                                   col_attackerth="thLevel",
                                   col_ishomeclan="attacker_is_home_clan",
                                   col_wartime="war_start_time",
                                   col_defender="defenderName"
                                   ):
    player_mapping_by_name = {}

    data = pd.read_csv(in_csv, header=0, delimiter=',', quoting=0, encoding="utf-8",
                       ).fillna("none")

    attack_id=0
    for index, row in data.iterrows():
        ishomeclan = row[col_ishomeclan]
        if ishomeclan!=1:
            continue #for now ignore defence

        time=datetime.datetime.strptime(row[col_wartime], '%Y-%m-%d %H:%M:%S')
        if time < from_date:
            continue

        attack_id+=1
        player_tag=row[col_attacker_tag]
        player_name = row[col_attacker]
        player_th = row[col_attackerth]
        defenderth = row[col_defenderth]
        player_name = util.normalise_name(player_name)
        stars=row[col_stars]

        if player_name in player_mapping_by_name.keys():
            player = player_mapping_by_name[player_name]
        else:
            player = models.Player(player_tag,player_name)

        attack = models.Attack(str(attack_id), defenderth,
                            player_th, stars, True,time)
        player._attacks[time]=attack

        player_mapping_by_name[player_name] = player
        attack_id += 1

    for k, v in missed_attacks.items():
        if k in player_mapping_by_name.keys():
            player = player_mapping_by_name[k]
            player._unused_attacks=v
        else:
            player = models.Player('UNKNOWN',k)
            player._unused_attacks=v
            player_mapping_by_name[k]=player

    clan = models.ClanWarData(clanname)
    clan._players = list(player_mapping_by_name.values())
    return clan


def parse_warfeed_missed_attacks(messages:list, sidekick_name=None):
    concatenated=""
    for m in messages:
        if sidekick_name is not None and sidekick_name not in m.author.name.lower():
            continue
        if len(m.clean_content) == 0:
            continue
        concatenated+=m.clean_content+"\n"

    data=extract_missed_attacks(concatenated)

    return data

def extract_missed_attacks(message:str):
    lines=message.split("\n")

    data={}
    counter=0
    found=False
    for l in lines:
        if '2 remaining attack' in l.lower():
            #print(">>>>> remaining attacks set to 2, msg={}".format(l))
            counter=2
            found=True
            continue
        elif '1 remaining attack' in l.lower():
            counter=1
            found=True
            continue
        elif found and (l.startswith("<:b") or l.startswith("<:s") or l.startswith(":s:")):
            if ">" in l:
                startindex = l.rindex(">")
            elif ":" in l:
                startindex=l.rindex(":")
            else:
                continue
            player_name = util.normalise_name(l[startindex + 1:]).strip()
            if len(player_name)==0:
                continue

            if player_name in data.keys():
                data[player_name]+=counter
            else:
                data[player_name]=counter
        else:
            counter=0
            found=False
    data = dict(sorted(data.items(), key=lambda item: item[1], reverse=True))
    return data

def parse_clan_activity(messages:list):
    data={}
    for m in messages:
        content=m.clean_content
        if len(content)==0:
            continue

        lines=content.split("\n")
        for l in lines:
            end=util.find_first_appearance(l, SIDEKICK_CLANACTIVITY_KEYWORDS)
            if end==-1:
                continue
            l = l[:end].strip()
            textvalues=l.split(" ", 1)
            if len(textvalues)<2:
                continue
            player =textvalues[1].strip()
            if player in data.keys():
                data[player]+=1
            else:
                data[player]=1

    data=dict(sorted(data.items(), key=lambda item: item[1], reverse=True))
    return data
'''

'''
def parse_clan_best(discord_messages:list):
    data={}
    start_index, season_id=find_start_message_index(discord_messages)
    if start_index is None:
        return data, None, None

    tally = 0
    prev_fieldname = ""

    selected_messages=[]
    for i in range(start_index, len(discord_messages)):
        m=discord_messages[i]
        selected_messages.append(m)
        #the message is encoded as an embed object, containing fields
        if len(m.embeds) == 0:
            continue

        for embed in m.embeds:
            if len(embed.fields)==0:
                continue

            #check if data are in the embed fields
            found_in_field=False
            for field in embed.fields:
                fieldname=field.name
                fieldvalue=field.value
                prev_fieldname, tally, found = extract_data(fieldname,fieldvalue,prev_fieldname,tally, data)
                # the following statement checks if data are extracted from fields, but in practice, sometimes data are
                # found both in fields and description of an embed. So we need to always check description
                # if the relationship is either-or, then we should check and set the variable below accordingly.
                # if not found_in_field and found:
                #     found_in_field = True

            #sometimes data are not stored in field, then check description
            if not found_in_field and type(embed.description) is str:
                desc = embed.description.split("\n",1)
                fieldname=desc[0].strip()
                fieldvalue=desc[1].strip()
                prev_fieldname, tally, found = extract_data(fieldname, fieldvalue, prev_fieldname, tally, data)

    if prev_fieldname != "":
        data[prev_fieldname] = tally

    return data, season_id, selected_messages

def find_start_message_index(messages:list):
    for i in range(len(messages)-1, -1, -1):
        m=messages[i]
        if len(m.embeds) == 0:
            continue

        for e in m.embeds:
            if type(e.title) is str and SIDEKICK_CLANBEST_TITLE in e.title:
                desc = e.description.split("\n")
                desc = " ".join(desc[0:2])

                return i, desc.strip()
    return None, None

#the season identifier taken from sidekick /best command is parsed to a date, e.g.:
# 'Season Started: Mon Jul 26
#  Last Updated: 8h 22m ago'
def parse_season_start(season_start_str:str):
    now = datetime.datetime.now()
    try:
        start = season_start_str.split('\n')[0].strip().replace("*","")

        if ':' in start:
            start=start[start.index(':')+1:].strip()
            m1=now.month
            season_start=datetime.datetime.strptime(start, '%a %b %d')
            m2=season_start.month
            #work out the year
            if m1>m2:
                year=str(now.year)
            else:
                year=str(now.year +1 )
            season_start = datetime.datetime.strptime(start+" "+year, '%a %b %d %Y')
            return season_start
    except: #if the date is not parsable, just count back 30 days
        return (now - datetime.timedelta(days=30))

def extract_data(fieldname:str, fieldvalue:str, prev_fieldname:str, tally:int, counter:dict):
    found_in_field=False
    if SIDEKICK_CLANBEST_GOLDLOOT in fieldname:
        found_in_field=True
        if prev_fieldname != "":
            counter[prev_fieldname] = tally
            tally = 0
        prev_fieldname = SIDEKICK_CLANBEST_GOLDLOOT
        tally += extract_numbers(fieldvalue)
    elif SIDEKICK_CLANBEST_DELOOT in fieldname:
        found_in_field = True
        if prev_fieldname != "":
            counter[prev_fieldname] = tally
            tally = 0
        prev_fieldname = SIDEKICK_CLANBEST_DELOOT
        tally += extract_numbers(fieldvalue)
    elif SIDEKICK_CLANBEST_ELIXIRLOOT in fieldname:
        found_in_field = True
        if prev_fieldname != "":
            counter[prev_fieldname] = tally
            tally = 0
        prev_fieldname = SIDEKICK_CLANBEST_ELIXIRLOOT
        tally += extract_numbers(fieldvalue)
    elif SIDEKICK_CLANBEST_DONATIONS in fieldname:
        found_in_field = True
        if prev_fieldname != "":
            counter[prev_fieldname] = tally
            tally = 0
        prev_fieldname = SIDEKICK_CLANBEST_DONATIONS
        tally += extract_numbers(fieldvalue)
    elif SIDEKICK_CLANBEST_ATTACKS in fieldname:
        found_in_field = True
        if prev_fieldname != "":
            counter[prev_fieldname] = tally
            tally = 0
        prev_fieldname = SIDEKICK_CLANBEST_ATTACKS
        tally += extract_numbers(fieldvalue)
    elif fieldname == '\u200b':
        found_in_field = True
        # should continue from the previous 'name'
        tally += extract_numbers(fieldvalue)

    return prev_fieldname, tally,found_in_field
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
def extract_numbers(text:str):
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

