import disnake, operator, datetime
from clashhogs import models

DISCORD_MSG_MAX_LENGTH=1500

def parse_channel_id(value:str):
    if value is None:
        return -1
    try:
        hash = value.index("#")
        return int(value[hash+1:len(value)-1])
    except:
        return -1
#for index, see database.py line 108
def parse_war_data(rows:list, clantag,
                   col_attacker_tag=1,
                   col_attacker=2,
                   col_stars=5,
                   col_defenderth=7,
                   col_attackerth=6,
                   col_wartime=8,
                   col_wartype=9
                   ):
    player_mapping_by_tag = {}
    missed_attacks={}
    missed_cwl_attacks={}

    attack_id=0
    for row in rows:
        time=datetime.datetime.strptime(row[col_wartime], '%Y-%m-%d %H:%M:%S.%f')
        attack_id+=1
        player_tag=row[col_attacker_tag]
        player_name = row[col_attacker]
        player_th = row[col_attackerth]
        defenderth = row[col_defenderth]
        stars=row[col_stars]

        if player_tag in player_mapping_by_tag.keys():
            player = player_mapping_by_tag[player_tag]
        else:
            player = models.Player(player_tag,player_name)

        if stars==-1:
            player._unused_attacks+=1
            key = (player_tag, player_name)
            #missed attacks total
            if key in missed_attacks.keys():
                missed_attacks[key]+=1
            else:
                missed_attacks[key]=1
            #missed attacks cwl
            if row[col_wartype]=='cwl':
                if key in missed_cwl_attacks.keys():
                    missed_cwl_attacks[key] += 1
                else:
                    missed_cwl_attacks[key] = 1

        else:
            attack = models.Attack(str(attack_id), defenderth,
                            player_th, stars, True,time)
            player._attacks[row[0]]=attack

        player_mapping_by_tag[player_tag] = player
        attack_id += 1

    clan = models.ClanWarData(clantag)
    clan._players = list(player_mapping_by_tag.values())

    data_miss = dict(sorted(missed_attacks.items(), key=lambda item: item[1], reverse=True))
    data_cwl_miss = dict(sorted(missed_cwl_attacks.items(), key=lambda item: item[1], reverse=True))

    return clan, data_miss, data_cwl_miss


def parse_personal_war_data(rows:list, player:models.Player,
                   col_stars=5,
                   col_defenderth=7,
                   col_attackerth=6,
                   col_wartime=8
                   ):

    attack_id=0
    for row in rows:
        time=datetime.datetime.strptime(row[col_wartime], '%Y-%m-%d %H:%M:%S.%f')
        attack_id+=1
        player_th = row[col_attackerth]
        defenderth = row[col_defenderth]
        stars=row[col_stars]

        if stars==-1:
            player._unused_attacks+=1
        else:
            attack = models.Attack(str(attack_id), defenderth,
                            player_th, stars, True,time)
            player._attacks[row[0]]=attack

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
    warnings.append(string)

    string=""
    for r in records:
        string+="**Warning ID: {}**\n".format(r[0])
        d = datetime.datetime.fromisoformat(r[4]).strftime("%Y-%m-%d %H:%M")
        string+="\t\t*Player*: {} \t*Clan*: {}\n" \
                "\t\t*Points*: {} \t*Date*: {}\n" \
                "\t\t*Note*: {}\n".format(r[2], r[1],r[3],d,r[5])

        if len(string)>DISCORD_MSG_MAX_LENGTH:
            warnings.append(string)
            string=""

    if len(string)>0:
        warnings.append(string)
    return warnings

def format_blacklist(entries:list):
    records=[]
    if (len(entries)==0):
        return records

    for e in entries:
        if e is None:
            continue
        string="*Player tag*: {} \t*name*: {}\n" \
                "*Added by*: {} \t *on*: {}\n"  \
                "*Reason*:{}\n".format(e[0], e[1], e[3], e[4], e[2])
        records.append(string)
    return records

def format_credit_systems(res:dict):
    if len(res)==0:
        embedVar = disnake.Embed(title="Clan(s) is/are not currently linked with this discord server or registered for the credit system",
                                 description="")  # , color=0x00ff00
    else:
        embedVar = disnake.Embed(title="Clans currently registered for the credit system",
                                 description="")  # , color=0x00ff00
    for clanwatch in res:
        if clanwatch is None:
            continue
        clantag=clanwatch._tag
        points = clanwatch._creditwatch_points
        id="Clan: {}".format(str(clantag)+", "+str(clanwatch._name) )
        string=""
        for k, v in points.items():
            string+=f" *{k}*={v}\t\t "
        embedVar.add_field(name=f'**{id}**',
                    value=string,
                    inline=False)

    return embedVar

def format_war_attack_weights(res:dict):
    if len(res)==0:
        embedVar = disnake.Embed(title="Clan(s) is/are not currently linked with this discord server. Run /link first.",
                                 description="")  # , color=0x00ff00
    else:
        embedVar = disnake.Embed(title="Clans and their war attack weight multipliers. ",
                                 description="Run '/help waw_setup' for information on how the multipliers are used " \
                                             "to adjust stars gained in an attack depending on the attacker and defender's TH levels.")  # , color=0x00ff00
    for clanwatch in res:
        if clanwatch is None:
            continue
        clantag=clanwatch._tag
        if not hasattr(clanwatch, '_attackup_weights') or not hasattr(clanwatch, '_attackdown_weights'):
            clanwatch.reset_attackweights()

        id="Clan: {}, attacking up (u) or down (d) weights".format(str(clantag)+", "+str(clanwatch._name) )
        string=""
        weights = clanwatch._attackup_weights
        for k, v in weights.items():
            string+=f" *{k}*={v}\t\t "
        weights = clanwatch._attackdown_weights
        for k, v in weights.items():
            string+=f" *{k}*={v}\t\t "
        embedVar.add_field(name=f'**{id}**',
                    value=string,
                    inline=False)

    return embedVar

def format_playercredits(tag, clanname, playercredits, playernames, last_updated):
    msgs=[]
    if len(playercredits)==0:
        string="**Clan {}, {}** currently does not have any player credits recorded. Credit records are automatically added at war end, maybe try again later.".format(tag, clanname)
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
                 "Credit records are automatically added at war end, maybe try again later.".format(playertag, playername, clanname)
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

'''
id INTEGER PRIMARY KEY, " \
                           "player_tag TEXT NOT NULL, " \
                           "player_name TEXT NOT NULL, " \
                           "clan_tag TEXT NOT NULL, " \
                           "clan_name TEXT NOT NULL, " \
                           "stars int NOT NULL, " \
                           "attacker_th int NOT NULL, " \
                           "defender_th int NOT NULL, " \
                           "time int NOT NULL," \
                           "war_type TEXT NOT NULL
'''
def format_attackstars(records:list, clanwatch:models.ClanWatch):
    msgs=[]
    if len(records)==0:
        string="No data found matching the search criteria. The clan must have been linked to this discord server using '/link'. " \
               "Also, war data must have been already collected for the clan."
        msgs.append(string)
        return msgs

    points={}
    for r in records:
        player_tag=r[1]
        player_name=r[2]
        player = (player_tag, player_name)
        stars=r[5]
        player_th=r[6]
        if player_th==-1: #player missed this attack
            continue
        defender_th=r[7]
        thdff=player_th-defender_th
        if thdff>0:
            if thdff >3:
                thdff=3
            key = "d"+str(thdff)
            mult=clanwatch._attackdown_weights[key]
        elif thdff<0:
            if thdff<-3:
                thdff=-3
            key="u"+str(-thdff)
            mult=clanwatch._attackup_weights[key]
        else:
            mult=1

        if player in points.keys():
            adjusted_stars=points[player] + round(stars*mult, 1)
        else:
            adjusted_stars=round(stars*mult, 1)
        points[player]=adjusted_stars

    points_sorted = dict(sorted(points.items(), key=operator.itemgetter(1), reverse=True))
    string=""
    for player, points in points_sorted.items():
        string += "{}, \t{}\n".format(str(player), str(round(points,1)))

        if len(string) > DISCORD_MSG_MAX_LENGTH:
            msgs.append(string)
            string = ""
    if len(string)>0:
        msgs.append(string)
    return msgs

def format_attack_records(records:list,clanwatch:models.ClanWatch):
    msgs=[]
    player=None
    string = ""
    for r in records:
        player_tag=r[1]
        player_name=r[2]
        if player is None:
            player=(player_tag, player_name)

        stars=r[5]
        player_th=r[6]
        defender_th=r[7]
        time = r[8]
        thdff=player_th-defender_th
        if thdff>0:
            if thdff >3:
                thdff=3
            key = "d"+str(thdff)
            mult=clanwatch._attackdown_weights[key]
        elif thdff<0:
            if thdff<-3:
                thdff=-3
            key="u"+str(-thdff)
            mult=clanwatch._attackup_weights[key]
        else:
            mult=1

        adjusted_stars= round(stars*mult, 1)
        string+="{}, \t{} stars TH{}>TH{}, \tadjusted by x{}={}\n".format(datetime.datetime.fromisoformat(time).strftime('%d/%m/%Y'),
                                              stars, player_th, defender_th,
                                              mult, adjusted_stars)

        if len(string) > DISCORD_MSG_MAX_LENGTH:
            msgs.append(string)
            string = ""
    if len(string)>0:
        msgs.append(string)
    return msgs

def format_clanwatch_data(clan):
    if clan is None:
        embedVar = disnake.Embed(title="Clan Setup",
                                 description="This clan has not been linked to this discord server")  # , color=0x00ff00
    else:
        embedVar = disnake.Embed(title="Clan Setup",
                                 description="")  # , color=0x00ff00
        embedVar.add_field(name='Tag',
                    value=clan._tag,
                    inline=True)
        embedVar.add_field(name='Name',
                           value=clan._name,
                           inline=True)
        embedVar.add_field(name='Discord server',
                           value=clan._guildname,
                           inline=True)
        embedVar.add_field(name='Missed attacks channel',
                           value=clan._channel_warmiss,
                           inline=True)
        embedVar.add_field(name='War summary channel',
                           value=clan._channel_warsummary,
                           inline=True)
        embedVar.add_field(name='Member join/leave channel',
                           value=clan._channel_clansummary,
                           inline=True)

    return embedVar

def format_clanlist_data(clan, minTH, rules_channel):
    if clan is None:
        embedVar = disnake.Embed(title="Not Found",
                                 description="This clan cannot be found.")  # , color=0x00ff00
    else:
        embedVar = disnake.Embed(title="{}, {}, Level {}".format(clan.name, clan.tag, clan.level),
                                 description=clan.share_link)  # , color=0x00ff00
        embedVar.add_field(name='Required TH',
                    value=minTH,
                    inline=True)
        embedVar.add_field(name='CWL',
                           value=clan.war_league.name,
                           inline=True)
        embedVar.add_field(name='Rules',
                           value=rules_channel,
                           inline=True)

    return embedVar, clan.name