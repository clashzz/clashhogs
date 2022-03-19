

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

#letter O > number 0
def normalise_tag(tag):
    return tag.replace("O","0").upper()

def prepare_help_menu(botname, prefix):
    string=f'{botname} supports the following commands ( [A] indicates admin privilege required for that command). Run **{prefix}help [command]** for how to use them. Also see ' \
    'details at https://github.com/clashzz/sidekickassist:\n' \
    '\t\t - **link**: [A] link a clan to this discord server. This must be done first before you use other commands with this bot\n' \
    '\t\t - **clanwar**: [A] analyse and produce a report for a clan\'s past war peformance\n' \
    '\t\t - **mywar**: analyse and produce a report for a player\'s past war performance\n'   \
    '\t\t - **warn**: [A] manage warnings for a clan/player\n'  \
    '\t\t - **crclan**: [A] set up the credit watch system for a clan\n' \
    '\t\t - **crplayer**: [A] manage the credits of a specific player \n' \
    '\t\t - **mycredit**: view the credits of a specific player (available to any user)'
    return string

def prepare_link_help(prefix):
    'This command is used to map your sidekick war feed channel to another channel,'
    string= 'This command must be run to link a clan to this discord server before other commands can be used. Authentication needed: ' \
            'your clan description must end with "CH22".\n ' \
            '**Usage:** {}link [option] [clantag]. Options can be:\n' \
            '\t\t\t -l: to list clans currently linked with this discord server. If [clantag] is provided, list details of that clan only\n'  \
            '\t\t\t -a: to link a clan with this discord server. [clantag] must be provided\n'   \
            '\t\t\t -r: to unlink a clan with this discord server. [clantag] must be provided'.format(prefix)

    return string

def prepare_channel_help(prefix):
    'This command is used to map your sidekick war feed channel to another channel,'
    string= 'This command is used to set up the discord channels for receiving different clan feeds.\n ' \
            '**Usage:** {}channel [option] [clantag] [channel]. Options can be:\n' \
            '\t\t\t -miss: to add [channel] for the clan [clantag] to receive missed attacks update\n'  \
            '\t\t\t -war: to add [channel] for the clan [clantag] to receive monthly war summary'.format(prefix)

    return string

def prepare_clanwar_help(prefix):
    'This command is used to generate clan war digest using data from the Sidekick clan war feed channel.\n'
    string=f'**Usage**: {prefix}clanwar [clantag] [dd/mm/yyyy] '   \
    '[OPTIONAL:dd/mm/yyyy]\n'   \
    '\t\t - [clantag]: must be provided\n' \
    '\t\t - [dd/mm/yyyy]: the first is the start date (required), the second is the end date (optional). '  \
    'When the end date is not provided, the present date will be used\n'
    return string

def prepare_mywar_help(prefix):
    'This command is used to generate personal war analysis using data from the Sidekick clan war feed '
    string= 'channel. You must have taken part in the wars to have any data for analysis.\n\n'  \
    f'**Usage**: {prefix}mywar [player_tag] [dd/mm/yyyy] [OPTIONAL:dd/mm/yyyy]\n' \
    '\t\t - [player_tag] your player tag (must include #)\n'    \
    '\t\t - [dd/mm/yyyy] the first is the start date (required), the second is the end date (optional) for '    \
    'your data. When the end date is not provided, the present date will be used\n' \
    'When the end date is not provided, the present date will be used\n'
    return string

def prepare_warn_help(prefix):
    'This command is used to manage warnings of players in a clan.\n'
    string=f'**Usage:** {prefix}warn [option] [clanname] [playername] [value] [note]\n' \
    '[option]: \n'    \
    '\t\t -l: to list all warnings of a clan, or a player in a clan (clanname is mandatory, other parameters can be ignored)\n' \
    '\t\t -a: to add a warning for a player of a clan, and assign a value to that warning (all parameters mandatory except note, which can be multi-word but must be the last parameter)\n' \
    '\t\t -c: to remove all warnings of a player in a clan (clanname and playername mandatory)\n'   \
    '\t\t -d: to delete a specific warning record. Provide [clanname] and either an ID of a record, or a ' \
           'date (yyyy-mm-dd) replace [playername]. If a date is provided, all records entered before the date' \
           ' will be deleted\n'    \
    '\nAll parameters (except [note]) must be a single word without space characters. [value] must be a number when provided'
    return string

def prepare_crclan_help(prefix, default_points:dict):
    default = ""
    for k, v in default_points.items():
        default += k + "=" + str(v) + " "
    string='This command is used to set up credit watch for a clan.\n' \
        f'**Usage:** {prefix}crclan [option] [clantag] [*value]\n'  \
        '[option]: \n'    \
        '\t\t -l: list clans currently registered. If [clantag] is supplied, only that clan will be shown. If you want to see all registered clans, use *, i.e.: crclan -l *\n'  \
        '\t\t -u: to update the points of credit watch for a clan. [clantag] is mandatory. Other multiple [value] parameters can specify the credit points and activities to be registered. '   \
        'If none provided, then: '  \
        f'*{default.strip()}*. '    \
        f'If you want to customise the values, provide them in the same format as above, each separated by a whitespace. Default values will be set when not provided in [*values]\n' \
        '\t\t -c: To delete credits for all players of a clan, specified by the [tag] (confirmation required) \n'
    return string

def prepare_crplayer_help(prefix):
    string='This command is used to manage credits for a player.\n' \
        f'**Usage:** {prefix}crplayer [option] [tag] [value] [note]\n'  \
        '- [option]: \n'    \
        '\t\t -lc: List all players\'s total credits in a clan, specified by the [tag] (must be a clan tag)\n' \
           '\t\t -lp: List a specific player\'s credit records in a clan, specified by the [tag] (must be a player tag)\n' \
           '\t\t -a: To manually add credits of [value] to a player specified by the [tag] (must be a player tag). When using this command, you must also provide a reason [note] (can be a sentence) '
    return string

def prepare_mycredit_help(prefix):
    string='This command is used to view credits for a player.\n' \
        f'**Usage:** {prefix}mycredit [tag], where [tag] must be a player tag\n'
    return string

