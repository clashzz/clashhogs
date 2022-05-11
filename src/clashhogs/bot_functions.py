import coc, datetime,disnake
from clashhogs import models, dataformatter, util
from pathlib import Path

def war_ended(old_war: coc.ClanWar, new_war: coc.ClanWar):
    if old_war.state == "inWar" and new_war.state != "inWar":
        return True
    if old_war.state == "inWar" and old_war.war_tag is not None:
        return True

async def check_clan(clantag, coc_client, ) -> coc.Clan:
    if clantag is not None:
        try:
            clan = await coc_client.get_clan(clantag)
            return clan
        except coc.NotFound:
            return None
    return None

async def check_player(playertag, coc_client, ) -> coc.Player:
    if playertag is not None:
        try:
            player = await coc_client.get_player(playertag)
            return player
        except coc.NotFound:
            return None
    return None

def check_date(date_str):
    try:
        date = datetime.datetime.strptime(date_str, "%d/%m/%Y")
        return date
    except:
        return None

def end_war(war:coc.ClanWar, total_attacks, log, database, bot):
    members = war.members
    attacks = war.attacks
    clan_home=war.clan
    missed_attacks, registered = register_war_attacks(members, attacks, war, clan_home, type, total_attacks, database)
    if registered:
        log.info(
            "\tCredits registered for: {}. Missed attacks: {}".format(war.clan, missed_attacks))
    else:
        log.info(
            "\tCredits not registered for: {}, something wrong... ".format(war.clan, missed_attacks))

    channel, misses = send_missed_attacks(missed_attacks, clan_home.tag, database, bot)
    return channel, misses

def close_cwl_war(database, bot, logger, attacker_clan, current_war_obj, total_attacks_avail):
    samewar = database.update_if_same_cwl_war(attacker_clan.tag, current_war_obj)
    if not samewar:
        # 1. register previous cwl war attacks
        prev_war = database.MEM_current_cwl_wars[attacker_clan.tag][1]
        members = prev_war.members
        attacks = prev_war.attacks
        missed_attacks, registered = register_war_attacks(members, attacks, prev_war, attacker_clan,
                                                                        prev_war.type,
                                                                        total_attacks_avail, database)
        if registered:
            logger.info(
                "\tCredits registered for: {}. Missed attacks: {}".format(attacker_clan.tag, missed_attacks))
        else:
            logger.info(
                "\tCredits not registered for: {}, something wrong... ".format(attacker_clan.tag, missed_attacks))

        channel, misses = send_missed_attacks(missed_attacks, attacker_clan.tag, database, bot)
        if channel is not None and misses is not None:
            await channel.send(misses)

        # 2. reset cwl war for this clan
        database.reset_cwl_war_data(attacker_clan.tag, current_war_obj)

def register_war_attacks(members: list, attacks: list, old_war, clan_home, type, total_attacks, database):
    attack_data = {}
    for m in members:
        if not m.is_opponent:
            attack_data[(m.name, m.tag)] = []

    for atk in attacks:
        key = (atk.attacker.name, atk.attacker.tag)
        if key in attack_data.keys():
            # id: str, target_thlvl: int, source_thlvl: int, stars: int, is_outgoing: bool,
            # time: datetime.datetime
            id = atk.attacker_tag + ">" + atk.defender_tag
            atk_obj = models.Attack(id, atk.defender.town_hall, atk.attacker.town_hall,
                                    atk.stars, True, old_war.end_time.now)
            attack_data[key].append(atk_obj)

    missed_attacks, registered = database.save_war_attacks(clan_home.tag, clan_home.name, type, total_attacks,
                                                           attack_data)
    return missed_attacks, registered

def send_missed_attacks(misses: dict, clantag: str, database, bot):
    clanwatch = database.get_clanwatch(clantag)
    guild = bot.get_guild(clanwatch._guildid)
    if guild is not None:
        channel_id = clanwatch._channel_warmiss
        if channel_id is not None:
            channel_id = dataformatter.parse_channel_id(channel_id)
        channel = disnake.utils.get(guild.channels, id=channel_id)
        if channel is not None:
            message = "War missed attack for **{} on {}**:\n".format(
                clanwatch._name, datetime.datetime.now().strftime('%d/%m/%Y'))

            if len(misses) == 0:
                message += "\tNone, everyone attacked!"
            else:
                for k, v in misses.items():
                    message += "\t" + str(k) + "\t" + str(v) + "\n"
            return channel, message
    return None, None

def prepare_wardigest(fromdate, todate, clantag, clanname, database):
    # gather missed attacks data
    war_data = database.find_war_data(clantag, fromdate, todate)
    if len(war_data) == 0:
        return None, None, None, None, None

    # gather war data
    targetfolder = "db/" + clantag
    Path(targetfolder).mkdir(parents=True, exist_ok=True)
    # now process the file and extract data
    clan_war_data, data_missed, data_cwl_missed = dataformatter.parse_war_data(war_data, clantag)
    msg = "**{} clan war summary between {} and {}**:\n\n **Missed Attacks - Total:** \n".format(
        clantag + ", " + clanname,
        fromdate.strftime('%d/%m/%Y'), todate.strftime('%d/%m/%Y'))
    count = 0
    for k, v in data_missed.items():
        msg += "\t" + str(k) + ": " + str(v) + "\n"
        count += 1
    if count == 0:
        msg += "\t(no data)"
    msg_warmiss = msg + "\n"

    msg = "\n**Missed Attacks - CWL:** \n"
    count = 0
    for k, v in data_cwl_missed.items():
        count += 1
        msg += "\t" + str(k) + ": " + str(v) + "\n"
    if count == 0:
        msg += "\t(no data)"
    msg_cwlmiss = msg + "\n"

    data_for_plot, clan_summary = clan_war_data.output_clan_war_data(targetfolder)
    msg = "\n**Clan Overview**:\n"
    for k, v in clan_summary.items():
        msg += "\t" + k + ": " + str(v) + "\n"
    war_overview = msg + "\n"

    figure = data_for_plot.plot(kind='bar', stacked=True).get_figure()
    figure.savefig(targetfolder + '/clan_war_data.jpg', format='jpg')
    # now fetch that file and send it to the channel
    fileB = disnake.File(targetfolder + "/clan_war_data.jpg")
    war_plot = fileB
    return msg_warmiss, msg_cwlmiss, war_overview, war_plot, clan_summary

def log_member_movement(membertag, membername, clanname, clantag, join_or_left: str, database, bot):
    messages = []
    to_channel = None
    if clantag in database.MEM_mappings_clanwatch.keys():
        clanwatch = database.MEM_mappings_clanwatch[clantag]
        guild = bot.get_guild(clanwatch._guildid)
        if guild is not None and clanwatch._channel_clansummary is not None:
            channel_id = dataformatter.parse_channel_id(clanwatch._channel_clansummary)
            channel = disnake.utils.get(guild.channels, id=channel_id)
            if channel is not None:
                emoji = ""
                if join_or_left == 'joined':
                    emoji = ":green_circle:"
                else:
                    emoji = ":red_circle:"
                to_channel = channel
                messages.append("{} **{}, {}** has {} the clan **{}**".format(emoji, membername,
                                                                              membertag, join_or_left,
                                                                              clanname))
                member_name_variants = util.generate_variants(membername)
                guild_member_names = {}
                for m in guild.members:
                    if not m.bot:
                        guild_member_names[m.display_name] = util.generate_variants(m.display_name)
                matching = util.find_overlap(member_name_variants, guild_member_names)

                if len(matching) > 0:
                    msg = "Please check if the member's discord roles need changing. " \
                          "Possible discord name matches found:\n"
                    for m in matching:
                        msg += "\t\t" + m + "\n"
                    messages.append(msg)
                else:
                    messages.append("I can't find similar discord names. Please check manually.")

                # check for blacklist
                if join_or_left == "joined":
                    entries = database.show_blacklist(clanwatch._guildid, membertag)
                    records = dataformatter.format_blacklist(entries)
                    if len(records) > 0:
                        msg = ":warning: **WARNING** this member is currently on our blacklist:\n"
                        messages.append(msg)
                        messages.extend(records)
    return messages, to_channel
