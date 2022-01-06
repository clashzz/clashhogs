import discord, operator
from datetime import datetime
DISCORD_MSG_MAX_LENGTH=1500

MONTHS_MAPPINGS={
    1:"Jan", 2:"Feb", 3:"Mar",4:"Apr", 5:"May", 6:"Jun",7:"Jul", 8:"Aug", 9:"Sep",10:"Oct", 11:"Nov", 12:"Dec",
}

def load_properties(file):
    params={}
    with open(file) as f:
        lines = f.readlines()
        for l in lines:
            values = l.split("=")
            if len(values)<2:
                continue
            params[values[0].strip()]=values[1].strip()
    return params


def normalise_name(text):
    text = text.encode('ascii', 'ignore').decode("utf-8")
    return text.strip().replace(" ","_")

#letter O > number 0
def normalise_tag(tag):
    return tag.replace("O","0").upper()

def value_found_in_text(text:str, values:list):
    for v in values:
        if v in text:
            return True
    return False

def find_first_appearance(text:str, keywords:list):
    index=len(text)
    found=False
    for k in keywords:
        if k in text:
            found = True
            idx = text.index(k)
            if idx<index:
                index=idx
    if found:
        return index
    else:
        return -1

def format_warnings(clan:str, records:list, player=None):
    warnings=[]
    if player is None:
        string = "**Current warning records for {}**\n\n".format(clan)
    else:
        total_points=0
        for r in records:
            try:
                total_points+=float(r[3])
            except:
                pass
        string = "**Current warning records for {} from {}**, total points={}\n\n".format(clan, player, total_points)  # , color=0x00ff00

    for r in records:
        string+="**Warning ID: {}**\n".format(r[0])
        d = datetime.fromisoformat(r[4]).strftime("%Y-%m-%d %H:%M")
        string+="\t\t*Player*: {} \t*Clan*: {}\n" \
                "\t\t*Points*: {} \t*Date*: {}\n" \
                "\t\t*Note*: {}\n".format(r[2], r[1],r[3],d,r[5])

        if len(string)>DISCORD_MSG_MAX_LENGTH:
            warnings.append(string)
            string=""

    if len(string)>0:
        warnings.append(string)
    return warnings

def format_credit_systems(res:dict):
    if len(res)==0:
        embedVar = discord.Embed(title="Clan(s) is/are not currently registered for the credit system",
                                 description="")  # , color=0x00ff00
    else:
        embedVar = discord.Embed(title="Clans currently registered for the credit system",
                                 description="")  # , color=0x00ff00
    for clantag, values in res.items():
        id="Clan Tag: {}".format(clantag)
        string=""
        for k, v in values.items():
            string+=f" *{k}*={v}\t\t "
        embedVar.add_field(name=f'**{id}**',
                    value=string,
                    inline=False)

    return embedVar

def format_playercredits(tag, clanname, playercredits, playernames, last_updated):
    msgs=[]
    if len(playercredits)==0:
        string="**Clan {}, {}** currently does not have any player credits recorded. Credit records are automatically added at war end, maybe try again later."
    else:
        string ="**Clan {}, {}, last updated at {}**\n".format(tag, clanname, last_updated)  # , color=0x00ff00
        playercredits_sorted = dict( sorted(playercredits.items(), key=operator.itemgetter(1),reverse=True))

        for pt, cr in playercredits_sorted.items():
            pn = playernames[pt]
            string+="\t\t{}\t{}, {}\n".format(cr, pt, pn)

            if len(string)>DISCORD_MSG_MAX_LENGTH:
                msgs.append(string)
                string=""

    if len(string)>0:
        msgs.append(string)
    return msgs

def format_playercreditrecords(playertag, clantag, clanname, playername, creditrecords):
    msgs = []
    if len(creditrecords)==0:
        string = "Player {}, {} from {} currently does not have any credits recorded. " \
                 "Credit records are automatically added at war end, maybe try again later."
    else:
        total=0
        for rec in creditrecords:
            total+=float(rec['credits'])
        string = "**Player {}, {}** from **{}, {}**, total credits=**{}**\n\n".format(playertag, playername, clanname, clantag, total)
        #"credits":r[5], "time":time, "reason":r[7]
        for rec in creditrecords:
            string+="\t\t**{}**: {}, {}\n".format(rec["time"], rec['credits'],rec['reason'])

            if len(string)>DISCORD_MSG_MAX_LENGTH:
                msgs.append(string)
                string=""

    if len(string)>0:
        msgs.append(string)
    return msgs

def prepare_help_menu(botname, prefix):
    string=f'{botname} supports the following commands. Run **{prefix}help [command]** for how to use them. Also see ' \
    'details at https://github.com/clashzz/sidekickassist:\n' \
    '\t\t - **warmiss**: set up a channel for forwarding missed attacks\n' \
    '\t\t - **wardigest**: analyse and produce a report for a clan\'s past war peformance\n' \
    '\t\t - **clandigest**: analyse and produce a report for a clan\'s activities (excl. war)\n'    \
    '\t\t - **warpersonal**: analyse and produce a report for a player\'s past war performance\n'   \
    '\t\t - **warn**: manage warnings for a clan/player\n'  \
    '\t\t - **crclan**: set up the credit watch system for a clan\n' \
    '\t\t - **crplayer**: manage the credits of a specific player'
    return string

def prepare_warmiss_help(prefix):
    'This command is used to map your sidekick war feed channel to another channel,'
    string= ' where missed attacks will be automatically tallied.\n'    \
    f'**Usage:** {prefix}warmiss [option] #sidekick-war #missed-attacks [clanname]\n'   \
    '\t\t - [option]: \n'   \
    '\t\t\t\t -l: to list current channel mappings (ignore other parameters when using this option)\n'  \
    '\t\t\t\t -a: to add a channel mapping\n'   \
    '\t\t\t\t -r: to remove a channel mapping:\n'   \
    '\t\t - [clanname] must be a single word\n' \
    'All parameters must be a single word without space characters. The channels must have the # prefix'
    return string

def prepare_clandigest_help(botname, prefix):
    'This command is used to generate clan digest for the current season using data from the Sidekick clan '
    string='feed channel. \n'   \
    f'**Usage**: {prefix}clandigest #sidekick-clan-feed-channel #output-target-channel [clanname]\n'    \
    '\t\t - [clanname] must be a single word\n\n'   \
    f'{botname} must have read and write permissions to both channels.'
    return string

def prepare_wardigest_help(botname, prefix):
    'This command is used to generate clan war digest using data from the Sidekick clan war feed channel.\n'
    string=f'**Usage**: {prefix}wardigest #sidekick-war-feed-channel #output-target-channel [clanname] [dd/mm/yyyy] '   \
    '[OPTIONAL:dd/mm/yyyy]\n'   \
    '\t\t - [clanname]: must be one word\n' \
    '\t\t - [dd/mm/yyyy]: the first is the start date (required), the second is the end date (optional). '  \
    'When the end date is not provided, the present date will be used\n\n'  \
    f'{botname} must have read and write permissions to both channels.'
    return string

def prepare_warpersonal_help(botname, prefix):
    'This command is used to generate personal war analysis using data from the Sidekick clan war feed '
    string= 'channel. You must have taken part in the wars to have any data for analysis.\n\n'  \
    f'**Usage**: {prefix}warpersonal [player_tag] [dd/mm/yyyy] [OPTIONAL:dd/mm/yyyy]\n' \
    '\t\t - [player_tag] your player tag (must include #)\n'    \
    '\t\t - [dd/mm/yyyy] the first is the start date (required), the second is the end date (optional) for '    \
    'your data. When the end date is not provided, the present date will be used\n' \
    'When the end date is not provided, the present date will be used\n\n'  \
    f'{botname} must have read and write permissions to both channels.'
    return string

def prepare_warn_help(prefix):
    'This command is used to manage warnings of players in a clan.\n'
    string=f'**Usage:** {prefix}warn [option] [clanname] [playername] [value] [note]\n' \
    '- [option]: \n'    \
    '\t\t -l: to list all warnings of a clan, or a player in a clan (clanname is mandatory, other parameters can be ignored)\n' \
    '\t\t -a: to add a warning for a player of a clan, and assign a value to that warning (all parameters mandatory except note, which can be multi-word but must be the last parameter)\n' \
    '\t\t -c: to remove all warnings of a player in a clan (clanname and playername mandatory)\n'   \
    '\t\t -d: to delete a specific warning record. Provide [clanname] and an ID of the record to replace [playername]\n'    \
    '\nAll parameters (except [note]) must be a single word without space characters. [value] must be a number when provided'
    return string

def prepare_crclan_help(prefix, default_points:dict):
    default = ""
    for k, v in default_points.items():
        default += k + "=" + str(v) + " "
    string='This command is used to set up credit watch for a clan.\n' \
        f'**Usage:** {prefix}crclan [option] [clantag] [*value]\n'  \
        '- [option]: \n'    \
        '\t\t -l: list clans currently registered. If [clantag] is supplied, only that clan will be shown. If you want to see all registered clans, use *, i.e.: crclan -l *\n'  \
        '\t\t -a: to register a clan for credit watch. [clantag] is mandatory. Other multiple [value] parameters can specify the credit points and activities to be registered. '   \
        'If none provided, then: '  \
        f'*{default.strip()}*. '    \
        f'If you want to customise the values, provide them in the same format as above, each separated by a whitespace. Default values will be set when not provided in [*values]' \
        '\n\t\t -d: to remove a clan from credit watch. [clantag is mandatory]\n'
    return string

def prepare_crplayer_help(prefix):
    string='This command is used to manage credits for a player.\n' \
        f'**Usage:** {prefix}crplayer [option] [tag] [value] [note]\n'  \
        '- [option]: \n'    \
        '\t\t -lc: List all players\'s total credits in a clan, specified by the [tag] (must be a clan tag)\n' \
           '\t\t -lp: List a specific player\'s credit records in a clan, specified by the [tag] (must be a player tag)\n' \
           '\t\t -a: To manually add credits of [value] to a player specified by the [tag] (must be a player tag). When using this command, you must also provide a reason [note] (can be a sentence) \n' \
           '\t\t -d: To delete credits for all players of a clan, specified by the [tag] (confirmation required) \n'
    return string

#data should conform to the format {clan_name, war_tag, type (cwl,reg, friendly), member_attacks {(tag,name):remaining attacks}}
def format_war_participants(data:dict):
    new_data={}
    for k, v in data.items():
        if type(v) is dict:
            l = len(v)
            new_data["total_members"]=l
        else:
            new_data[k]=v