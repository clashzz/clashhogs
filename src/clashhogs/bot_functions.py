import coc, datetime, models, dataformatter,disnake

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

def war_register_attacks_and_misses(war:coc.ClanWar, total_attacks, log, database, bot):
    members = war.members
    attacks = war.attacks
    clan_home=war.clan
    missed_attacks, registered = register_war_attacks(members, attacks, war, clan_home, type, total_attacks)
    if registered:
        log.info(
            "\tCredits registered for: {}. Missed attacks: {}".format(war.clan, missed_attacks))
    else:
        log.info(
            "\tCredits not registered for: {}, something wrong... ".format(war.clan, missed_attacks))

    channel, misses = send_missed_attacks(missed_attacks, clan_home.tag, database, bot)
    return channel, misses

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
                clanwatch._name, datetime.datetime.now())

            if len(misses) == 0:
                message += "\tNone, everyone attacked!"
            else:
                for k, v in misses.items():
                    message += "\t" + str(k) + "\t" + str(v) + "\n"
            return channel, message
    return None, None
