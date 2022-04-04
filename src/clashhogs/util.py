import disnake, re

# Define a simple View that gives us a confirmation menu
class Confirm(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @disnake.ui.button(label="Yes", style=disnake.ButtonStyle.green)
    async def confirm(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        self.value = True
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @disnake.ui.button(label="No", style=disnake.ButtonStyle.grey)
    async def cancel(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        self.value = False
        self.stop()

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

def prepare_help_menu(botname):
    embedVar= disnake.Embed(title="Commands supported by {}".format(botname),
                  description="The letter [A] indicates admin privilege required for that command). Run **/help** followed by the"
                              " name of the command for details. Also see details at https://github.com/clashzz/clashhogs")  # , color=0x00ff00
    embedVar.add_field(name="/link",
                       value="[A] link a clan to this discord server. This must be done first before you use other commands with this bot.",
                       inline=False)
    embedVar.add_field(name="/channel",
                       value="[A] set up various clan feeds for a clan that is already linked with this server.",
                       inline=False
                       )
    embedVar.add_field(name="/clanwar",
                       value="[A] analyse and produce a report for a clan\'s past war peformance.",
                       inline=False)
    embedVar.add_field(name="/war",
                       value="[A] manage warnings for a clan/player.",
                       inline=False)
    embedVar.add_field(name="/crclan",
                       value="[A] set up the credit watch system for a clan, or clear all credits of members from a clan.",
                       inline=False)
    embedVar.add_field(name="/crplayer",
                       value="[A] manage the credits of a specific player.",
                       inline=False)
    embedVar.add_field(name="/mywar",
                       value="analyse and produce a report for a player\'s past war performance.",
                       inline=False)
    embedVar.add_field(name="/mycredit",
                       value="view the credits of a specific player.",
                       inline=False)

    return embedVar

def prepare_link_help():
    embedVar = disnake.Embed(title="Command /link",
                             description="[A] This command must be run to link a clan to this discord server before other commands can be used." \
                                         " **Authentication needed**: your clan description must end with 'CH22'.")
    embedVar.add_field(name="Usage",
                       value="/link [option] [clantag]",
                       inline=False)
    embedVar.add_field(name="option",
                       value="- list: to list clans currently linked with this discord server. If [clantag] is provided, list details of that clan only. \n"
                             "- add: to link a clan with this discord server. [clantag] must be provided. \n"
                             "- remove: to unlink a clan with this discord server. [clantag] must be provided. ",
                       inline=False)
    embedVar.add_field(name="clantag",
                       value="The tag of a clan. This may or may not be needed, depending on the [option]",
                       inline=False)

    return embedVar

def prepare_channel_help():
    embedVar = disnake.Embed(title="Command /channel",
                             description="[A] This command is used to set up the discord channels for receiving different clan feeds. " \
                                         " The clan must have already been linked with this discord server using */link*.")
    embedVar.add_field(name="Usage",
                       value="/channel [clantag] [to_channel] [option]",
                       inline=False)
    embedVar.add_field(name="clantag",
                       value="The tag of a clan. This must be provided.",
                       inline=False)
    embedVar.add_field(name="to_channel",
                       value="The discord channel to receive clan feed.",
                       inline=False)
    embedVar.add_field(name="option",
                       value="- war-monthly: to receive monthly summary of a clan's war performance (e.g., missed attacks, stars against each TH level). \n"
                             "- missed-attacks: to receive a summary of missed attacks at the end of every war.",
                       inline=False)

    return embedVar

def prepare_clanwar_help():
    embedVar = disnake.Embed(title="Command /clanwar",
                             description="[A] This command is used to generate a summary of a clan's war performance. " \
                                         " The clan must have already been linked with this discord server using */link*.")
    embedVar.add_field(name="Usage",
                       value="/clanwar [clantag] [dd/mm/yyyy] [dd/mm/yyyy]",
                       inline=False)
    embedVar.add_field(name="clantag",
                       value="The tag of a clan. This must be provided.",
                       inline=False)
    embedVar.add_field(name="First [dd/mm/yyyy]",
                       value="The start date from which data are to be collected. This must be provided.",
                       inline=False)
    embedVar.add_field(name="Second [dd/mm/yyyy]",
                       value="The end date by which data are to be collected. If not provided, the current date will be used.",
                       inline=False)

    return embedVar

def prepare_mywar_help():
    embedVar = disnake.Embed(title="Command /mywar",
                             description="This command is used to generate a summary of a player's war performance. " \
                                         " The player must be in a clan that has already been linked with this discord server. Ask an admin if you are unsure.")
    embedVar.add_field(name="Usage",
                       value="/mywar [player_tag] [dd/mm/yyyy] [dd/mm/yyyy]",
                       inline=False)
    embedVar.add_field(name="playertag",
                       value="The tag of a player. This must be provided.",
                       inline=False)
    embedVar.add_field(name="First [dd/mm/yyyy]",
                       value="The start date from which data are to be collected. This must be provided.",
                       inline=False)
    embedVar.add_field(name="Second [dd/mm/yyyy]",
                       value="The end date by which data are to be collected. If not provided, the current date will be used.",
                       inline=False)

    return embedVar

def prepare_warn_help():
    embedVar = disnake.Embed(title="Command /warn",
                             description="[A] This command is used to manage warnings for a clan's members. ")
    embedVar.add_field(name="Usage",
                       value="/warn [clan] [option] [name_or_id] [points] [reason]",
                       inline=False)
    embedVar.add_field(name="clanname",
                       value="The name of a clan. Note: the value will not be validated against the C.o.C. database.",
                       inline=False)
    embedVar.add_field(name="option",
                       value="- list: to list all warnings of a clan ('clan' required), or a player in a clan (both 'clan' and 'name_or_id' required).\n" \
                             "- add: to add a warning for a player, and assign a value to that warning (all parameters required)\n" \
                             "- clear: to remove all warnings of a player in a clan ('clan' and 'name_or_id' required)\n" \
                             "- delete: to delete a specific warning record ('clan' required, 'name_or_id' matching a warning record ID required). "
                             "This option can also be used to delete all records before a date, in which case 'name_or_id' should be a value yyyy-mm-dd",
                       inline=False)
    embedVar.add_field(name="name_or_id",
                       value="A value identifying a player, or a warning record id. See 'option' above.",
                       inline=False)
    embedVar.add_field(name="points",
                       value="A numeric value assigned to a warning record. Required when using the 'add' option.",
                       inline=False)
    embedVar.add_field(name="reason",
                       value="Message assigned to a warning record. Required when using the 'add' option.",
                       inline=False)
    return embedVar

def prepare_blacklist_help():
    embedVar = disnake.Embed(title="Command /blacklist",
                             description="[A] This command is used to add/remove players to a blacklist. "\
                             "**Note**: if you add a player, your discord username will be recorded for that operation. "\
                             "If members on the black list join a clan registered using the /link and /channel comamnd, "\
                             "a warning message will be posted upon joining.")
    embedVar.add_field(name="Usage",
                       value="/blacklist [option] [player_tag] [reason]",
                       inline=False)
    embedVar.add_field(name="option",
                       value="- list: to show the current blacklist. When [player_tag] is provided, a " \
                             "the bot will search if the player is in the list.\n" \
                             "- add: to add a player to the blacklist.\n" \
                             "- delete: to delete a player from the blacklist",
                       inline=False)
    embedVar.add_field(name="player_tag",
                       value="The tag of the player. Required when adding or deleting.",
                       inline=False)
    embedVar.add_field(name="reason",
                       value="An explanation of why the player is added.",
                       inline=False)
    return embedVar

def prepare_crclan_help(default_points:dict):
    default = ""
    for k, v in default_points.items():
        default += k + "=" + str(v) + " "
    embedVar = disnake.Embed(title="Command /crclan",
                             description="[A] This command is used to set up credit watch points for a clan, or "
                                         "reset/clear all credit records for all members of a clan. ")
    embedVar.add_field(name="Usage",
                       value="/crclan [option] [clantag] [points] ",
                       inline=False)
    embedVar.add_field(name="option",
                       value="- list: list clans currently registered for credit watch and the point configurations.\n"
                             "- clear: delete all credit records for all players of a clan (confirmation requried).\n"
                             "- update: update the point configurations for a clan.",
                       inline=False)
    embedVar.add_field(name="clantag",
                       value="Required for all [option]s. When using the 'list' option, this can be '*' to list all clans.",
                       inline=False)
    embedVar.add_field(name="points",
                       value="Credit points to be assigned to different activities. Only the default activities will be " \
                             "recognised. By default, these activities and their points are: *"+default.strip()+"*\n" \
                             "To change the point values for these activities, provide them in the same format as above "\
                             "with your own point value (e.g., 'x=50'). Each activity is separated by a space character. " \
                             "If an activity is not provided, the default point value will be used.",
                       inline=False)

    return embedVar

def prepare_crplayer_help():
    embedVar = disnake.Embed(title="Command /crplayer",
                             description="[A] This command is used to manage credits for a player.")
    embedVar.add_field(name="Usage",
                       value="/crplayer [option] [tag] [points] [reason]",
                       inline=False)
    embedVar.add_field(name="option",
                       value="- list_clan: list all players's total credits in a clan. \n"
                             "- list_player: list a specific player's every credit record.\n"
                             "- add: manually add credits to a player.",
                       inline=False)
    embedVar.add_field(name="tag",
                       value="Required for all [option]s. Either a clan's or a player's tag depending on the [option].",
                       inline=False)
    embedVar.add_field(name="points",
                       value="Used with the 'add' [option]. A number indicating the points to be added (can be negative).",
                       inline=False)
    embedVar.add_field(name="reason",
                       value="Used with the 'add' [option]. A note to explain why credits are manually added.",
                       inline=False)

    return embedVar

def prepare_mycredit_help():
    embedVar = disnake.Embed(title="Command /mycredit",
                             description="This command is used to view a clan member's current credits.")
    embedVar.add_field(name="Usage",
                       value="/mycredit [player_tag]",
                       inline=False)
    embedVar.add_field(name="player_tag",
                       value="The player's tag.",
                       inline=False)

    return embedVar

def generate_variants(membername:str):
    variants=set()
    lower=membername.lower()
    variants.add(lower)
    for v in lower.split(" "):
        if len(v)>1:
            variants.add(v)
    no_punc1= re.sub(r'[^\w\s]', " ", lower)
    no_punc1.replace("_"," ").strip()
    for v in no_punc1.split(" "):
        if len(v)>1:
            variants.add(v)
    no_punc2=re.sub(r'[^\w\s]', "", lower)
    no_punc2.replace("_"," ").strip()
    for v in no_punc2.split(" "):
        if len(v)>1:
            variants.add(v)
    return variants

def find_overlap(target:set, references:dict):
    res=[]
    for k, v in references.items():
        inter=target.intersection(v)
        if len(inter)>0:
            res.append(k)
    res=sorted(res)
    return res