import discord
from datetime import datetime

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
    if player is None:
        embedVar = discord.Embed(title="Current warning records", description="Clan: {}".format(clan)) #, color=0x00ff00
    else:
        total_points=0
        for r in records:
            try:
                total_points+=float(r[3])
            except:
                pass
        embedVar = discord.Embed(title="Current warning records",
                                 description="Clan: {}, Player: {}, Total points: {}".format(clan, player, total_points))  # , color=0x00ff00
    for r in records:
        id="Warning ID: {}".format(r[0])
        d = datetime.fromisoformat(r[4]).strftime("%Y-%m-%d %H:%M")
        embedVar.add_field(name=f'**{id}**',
                    value=f'> *Player*: {r[2]}\t\t *Clan*: {r[1]}\n> *Points*: {r[3]}\t\t *Date*: {d} \n> *Note*: {r[5]}',
                    inline=False)

    return embedVar

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

def prepare_help_menu(botname, prefix):
    string=f'{botname} supports the following commands. Run **{prefix}help [command]** for how to use them. Also see ' \
    'details at https://github.com/clashzz/sidekickassist:\n' \
    '\t\t - **warmiss**: set up a channel for forwarding missed attacks\n' \
    '\t\t - **wardigest**: analyse and produce a report for a clan\'s past war peformance\n' \
    '\t\t - **clandigest**: analyse and produce a report for a clan\'s activities (excl. war)\n'    \
    '\t\t - **warpersonal**: analyse and produce a report for a player\'s past war performance\n'   \
    '\t\t - **warn**: manage warnings for a clan/player\n'  \
    '\t\t - **credit**: manage a clan members\' credits\n'
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
    '\t\t -d: to delete a specific warning record. Supply the warning record ID as a value for [clanname]\n'    \
    '\nAll parameters (except [note]) must be a single word without space characters. [value] must be a number when provided'
    return string

def prepare_credit_help(prefix, default_points:dict):
    default = ""
    for k, v in default_points.items():
        default += k + "=" + str(v) + " "
    string='This command is used to manage credits of a clan\'s members.\n' \
        f'**Usage:** {prefix}credit [option] [clantag or playertag] [*value] [note]\n'  \
        '- [option]: \n'    \
        '\t\t -l: If [clantag] is supplied, only that clan will be shown. If you want to see all registered clans, use *, i.e.: credit -l *\n'  \
        '\t\t -a: to register a clan for credit watch. [clantag] is mandatory. Other multiple [value] parameters can specify the credit points and activities to be registered. '   \
        'If none provided, then: '  \
        f'*{default.strip()}*. '    \
        f'If you want to customise the values, provide them in the same format as above, each separated by a whitespace. Default values will be set when not provided in [*values]' \
        '\n\t\t -d: to remove a clan from credit watch. [clantag is mandatory]\n'
    return string

