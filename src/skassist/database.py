'''
This file implements data storage.
Currently everything saved in member.

Each guild will have a unique DB. This is identified by the guild id when the bot connects to a discord server
'''
from datetime import datetime
import datetime, sqlite3, threading, json, pickle
from pathlib import Path
from skassist import models, util

TABLE_channel_mapping_warmiss = "channel_mapping_warmiss"
TABLE_member_attacks = "member_attacks"
TABLE_member_warnings = "member_warnings"
TABLE_credits_watch_clans = "credit_watch_clans"
TABLE_credits_watch_players = "credit_watch_players"

CLAN_NAME="clan_name"
CLAN_WAR_TYPE="type"
CLAN_WAR_MEMBERS="members"
CLAN_WAR_ATTACKS="attacks"

CREDIT_WATCH_ACTIVITIES={"cw_attack":10, "cw_miss":-10, "cwl_attack":10, "cwl_miss":-10}

# This is not persisted. It is populated everytime a guild connects to the bot
MEM_mappings_guild_id_name = {}

# key=guild id|clan name (e.g., 3492301120|myclan
# value=a list of tuple (x, y) where x is the sidekick channel (name) of war feed, y is the channel (name) to tally
# missed attacks. This needs to be initialised every time the bot starts, or when a guild connects
MEM_mappings_guild_warmisschannel = {}

# key:clan tag; value: discord guild id. Needed by the credit watch system
# This needs to be initialised every time the bot starts, or updated when a clan registers for war/credit watch
MEM_mappings_clan_guild={}

# This needs to be initialised every time the bot starts, or updated when a clan registers for/removed from war/credit watch
MEM_mappings_clan_creditwatch = {}  # key: clan tag; value: {clan name, cw_attack, cw_miss, cwl_attack,cwl_miss}

# NB: this object is not persisted so if the bot crashes, data will be lost
# This is updated every time an attack is made from a clan registered for war/credit watch
## key: clan tag; value: {clan_name, type (cwl,reg, friendly), member_attacks {(tag,name):remaining attacks}}
## if the key is found in this mapping, it should also be present in the MEM_mappings_clan_creditwatch mapping
MEM_mappings_clan_currentwars={}

def connect_db(dbname):
    targetfolder = "db/"
    Path(targetfolder).mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(targetfolder + str(dbname) + '.db')
    return con

#check, initialise, and populate the database for a discord guild
def check_database(guild_id, data_folder):
    lock = threading.Lock()
    lock.acquire()

    con = connect_db(guild_id)
    cursor = con.cursor()

    # check if this guild's database has all necessary data tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table_names = []
    for t in cursor.fetchall():
        table_names.append(t[0])
    # if table does not exist, create them
    if TABLE_channel_mapping_warmiss not in table_names:
        create_statement = "CREATE TABLE IF NOT EXISTS {} (from_id integer PRIMARY KEY, " \
                           "to_id integer NOT NULL," \
                           "clan text NOT NULL);".format(TABLE_channel_mapping_warmiss)
        cursor.execute(create_statement)
    if TABLE_member_attacks not in table_names:
        create_statement = "CREATE TABLE {} (id text PRIMARY KEY, " \
                           "name TEXT NOT NULL, " \
                           "data BLOB NOT NULL);".format(TABLE_member_attacks)
        cursor.execute(create_statement)
    if TABLE_member_warnings not in table_names:
        create_statement = "CREATE TABLE {} (id INTEGER PRIMARY KEY, " \
                           "name TEXT NOT NULL, clan TEXT NOT NULL, total DOUBLE NOT NULL," \
                           "date TEXT NOT NULL, note TEXT);".format(TABLE_member_warnings)
        cursor.execute(create_statement)
    # else:
    #     print("deleting the wrong warning table")
    #     cursor.execute("DROP TABLE {}".format(TABLE_member_warnings))
    #     create_statement = "CREATE TABLE {} (id INTEGER PRIMARY KEY, " \
    #                        "clan TEXT NOT NULL, name TEXT NOT NULL, value DOUBLE NOT NULL," \
    #                        "date TEXT NOT NULL, note TEXT);".format(TABLE_member_warnings)
    #     cursor.execute(create_statement)

    if TABLE_credits_watch_clans not in table_names:
        create_statement = "CREATE TABLE {} (id INTEGER PRIMARY KEY, " \
                           "credit_type TEXT NOT NULL, clan_name TEXT NOT NULL," \
                           "clan_tag TEXT NOT NULL, points INT NOT NULL);".format(TABLE_credits_watch_clans)
        cursor.execute(create_statement)
    # else:
    #     print("deleting the wrong creditwatchpoints table")
    #     cursor.execute("DROP TABLE {}".format(TABLE_credits_watch_points))

    if TABLE_credits_watch_players not in table_names:
        create_statement = "CREATE TABLE {} (id INTEGER PRIMARY KEY, " \
                           "player_tag TEXT NOT NULL, player_name TEXT NOT NULL," \
                           "player_clantag TEXT NOT NULL, player_clanname TEXT NOT NULL, " \
                           "credits INT NOT NULL, time TEXT NOT NULL, reason TEXT);".format(TABLE_credits_watch_players)
        cursor.execute(create_statement)

    con.commit()

    # Populate MEM_mappings_clan_guild
    if len(MEM_mappings_clan_guild) == 0:
        file = data_folder + "/clan2guild.json"
        try:
            with open(file) as json_file:
                MEM_mappings_clan_guild.update(json.load(json_file))
        except:
            print("Unable to load the clan-guild mapping. Reset to empty. File does not exist: {}".format(file))

    # populate MEM_mappings_guild_warmisschannel
    cursor.execute("SELECT * FROM {};".format(TABLE_channel_mapping_warmiss))
    rows = cursor.fetchall()
    for row in rows:
        update_mappings_guild_warmisschannel(guild_id, row[0], row[1], row[2])

    # populate MEM_mappings_clan_creditwatch
    cursor.execute('SELECT * FROM {};'.format(TABLE_credits_watch_clans))
    rows = cursor.fetchall()
    update_mappings_clan_creditwatch(rows, MEM_mappings_clan_creditwatch)
    con.close()

    lock.release()

def update_mappings_guild_warmisschannel(guild_id, from_id, to_id, clan):
    lock = threading.Lock()
    lock.acquire()
    key = str(guild_id) + "|" + str(from_id)
    MEM_mappings_guild_warmisschannel[key] = str(guild_id) + "|" + str(to_id) + "|" + str(clan)
    lock.release()

def add_channel_mappings_warmiss(pair: tuple, guild_id, clan):
    con = connect_db(guild_id)
    cursor = con.cursor()
    cursor.execute('SELECT * FROM {} WHERE (from_id=?);'.format(TABLE_channel_mapping_warmiss), [pair[0]])
    entry = cursor.fetchone()

    if entry is None:
        cursor.execute('INSERT INTO {} (from_id, to_id, clan) VALUES (?,?,?)'.format(TABLE_channel_mapping_warmiss),
                       [pair[0], pair[1], clan])
    else:
        cursor.execute('UPDATE {} SET to_id = ? , clan = ? WHERE from_id = ?'.format(TABLE_channel_mapping_warmiss),
                       [pair[1], clan, pair[0]])

    con.commit()
    con.close()
    update_mappings_guild_warmisschannel(guild_id, pair[0], pair[1], clan)

def get_warmiss_mappings_for_guild(guild_id):
    con = connect_db(str(guild_id))
    cursor = con.cursor()
    cursor.execute('SELECT * FROM {};'.format(TABLE_channel_mapping_warmiss))
    rows = cursor.fetchall()
    res = []
    if rows is None:
        return res
    else:
        for row in rows:
            res.append((row[0], row[1], row[2]))
    con.close()
    return res

def remove_warmiss_mappings_for_guild(guild_id, from_channel_id):
    key = str(guild_id) + "|" + str(from_channel_id)
    if key in MEM_mappings_guild_warmisschannel.keys():
        del MEM_mappings_guild_warmisschannel[key]

    con = connect_db(str(guild_id))
    cursor = con.cursor()
    cursor.execute('DELETE FROM {} WHERE from_id=?;'.format(TABLE_channel_mapping_warmiss), [from_channel_id])
    con.commit()
    con.close()

def save_individual_war_data(guild_id, clanwardata: models.ClanWarData):
    con = connect_db(str(guild_id))
    cursor = con.cursor()
    for p in clanwardata._players:
        cursor.execute('SELECT * FROM {} WHERE (id=?);'.format(TABLE_member_attacks), [p._tag])
        entry = cursor.fetchone()

        if entry is None:
            b = pickle.dumps(p)
            cursor.execute('INSERT INTO {} (id, name, data) VALUES (?,?,?)'.format(TABLE_member_attacks),
                           [p._tag, p._name, b])
        else:
            past_data = entry[2]
            past_p = pickle.loads(past_data)
            for t, atk in p._attacks.items():
                if t in past_p._attacks.keys():
                    continue
                past_p._attacks[t] = atk
            b = pickle.dumps(past_p)
            cursor.execute('UPDATE {} SET data = ? WHERE id = ?'.format(TABLE_member_attacks),
                           [b, p._tag])

    con.commit()
    con.close()

def load_individual_war_data(guild_id, player_tag, from_date, to_date):
    lock = threading.Lock()
    lock.acquire()
    res = {}
    player_tag = util.normalise_tag(player_tag)
    con = connect_db(str(guild_id))
    cursor = con.cursor()

    cursor.execute('SELECT * FROM {} WHERE (id=?);'.format(TABLE_member_attacks), [player_tag])
    entry = cursor.fetchone()

    if entry is None:
        return res
    else:
        war_data = entry[2]
        player = pickle.loads(war_data)
        for time, atk in player._attacks.items():
            if time < to_date and time > from_date:
                res[time] = atk

    con.close()
    lock.release()
    return res

def has_warmiss_fromchannel(guild_id, channel_id):
    key = str(guild_id) + "|" + str(channel_id)
    return key in MEM_mappings_guild_warmisschannel.keys()

def get_warmiss_tochannel(guild_id, channel_id):
    key = str(guild_id) + "|" + str(channel_id)
    values = MEM_mappings_guild_warmisschannel[key].split("|")
    return int(values[1]), values[2]  # 1 = to_channel under the same guild, 2 = clan name


def add_warning(guild_id, clan, person, point, note=None):
    if type(note) is tuple:
        note = ' '.join(note)
    elif note is not None:
        note = str(note)

    con = connect_db(str(guild_id))
    cursor = con.cursor()
    cursor.execute('INSERT INTO {} (clan, name, value, date, note) VALUES (?,?,?,?,?)'.
                   format(TABLE_member_warnings),
                   [clan, person, point, datetime.datetime.now(), note])
    con.commit()
    con.close()


def list_warnings(guild_id, clan, person=None):
    res = []
    con = connect_db(str(guild_id))
    cursor = con.cursor()
    if person is None:
        cursor.execute('SELECT * FROM {} WHERE (clan=?);'.format(TABLE_member_warnings), [clan])
        rows = cursor.fetchall()
        for row in rows:
            res.append(row)
    else:
        cursor.execute('SELECT * FROM {} WHERE (clan=?) AND (name=?);'.format(TABLE_member_warnings), [clan, person])
        rows = cursor.fetchall()
        for row in rows:
            res.append(row)

    con.close()
    return res


def clear_warnings(guild_id, clan, person):
    con = connect_db(str(guild_id))
    cursor = con.cursor()
    cursor.execute('DELETE FROM {} WHERE name=? AND clan=?'.
                   format(TABLE_member_warnings), [person, clan])
    con.commit()
    con.close()


def delete_warning(guild_id, warning_id, clanname):
    con = connect_db(str(guild_id))
    cursor = con.cursor()
    cursor.execute('SELECT * FROM {} WHERE id=? AND clan=?'.
                       format(TABLE_member_warnings), [warning_id, clanname])
    rows = cursor.fetchall()
    if len(rows)==0:
        con.commit()
        con.close()
        return False

    r = cursor.execute('DELETE FROM {} WHERE id=?'.
                       format(TABLE_member_warnings), [warning_id])
    con.commit()
    con.close()
    return True

'''
returned format
 # key: clan tag; value: {clan name, cw_attack, cw_miss, cwl_attack,cwl_miss}
'''
def update_mappings_clan_creditwatch(database_search_res, res: dict):
    for row in database_search_res:
        clantag = row[3]
        clanname = row[2]
        credittype = row[1]
        points = int(row[4])
        if clantag in res.keys():
            values = res[clantag]
            values[credittype] = points
        else:
            values = {"name": clanname, credittype: points}
            res[clantag] = values
    return res

def list_registered_clans_creditwatch(guild_id, clantag="*"):
    con = connect_db(str(guild_id))
    cursor = con.cursor()
    res={}
    if clantag =="*":
        cursor.execute('SELECT * FROM {};'.format(TABLE_credits_watch_clans))
        rows = cursor.fetchall()
        update_mappings_clan_creditwatch(rows, res)
    else:
        cursor.execute('SELECT * FROM {} WHERE (clan_tag=?) ;'.format(TABLE_credits_watch_clans), [clantag])
        rows = cursor.fetchall()
        update_mappings_clan_creditwatch(rows, res)

    con.close()
    return res

#add a clan to creditwatch. Whenever this method is called, you need to also call cocclient.add_war_updates outside this method
def registered_clan_creditwatch(data_folder, guild_id, clantag, clanname, *values):
    remove_registered_clan_creditwatch(guild_id, clantag,data_folder)

    MEM_mappings_clan_guild[clantag]=guild_id
    with open(data_folder+'/clan2guild.json', 'w') as fp:
        json.dump(MEM_mappings_clan_guild, fp)

    con = connect_db(str(guild_id))
    cursor = con.cursor()

    invalid_activity_types=""

    if len(values[0])<1:
        for k, v in CREDIT_WATCH_ACTIVITIES.items():
            cursor.execute('INSERT INTO {} (clan_tag, clan_name, credit_type, points) VALUES (?,?,?,?)'.
                           format(TABLE_credits_watch_clans),
                           [clantag, clanname, k, v])
    else:
        credit_watch_activities_copy = CREDIT_WATCH_ACTIVITIES.copy()
        for v in values[0]:
            if '=' not in v:
                invalid_activity_types+="\n\t"+str(v)
                continue
            parts=v.split("=")
            if parts[0].strip() not in CREDIT_WATCH_ACTIVITIES.keys():
                invalid_activity_types+="\n\t"+str(v)
                continue
            try:
                float(parts[1].strip())
            except:
                invalid_activity_types += "\n\t" + str(v)
                continue
            else:
                credit_watch_activities_copy[parts[0].strip()]=parts[1].strip()

        for k, v in credit_watch_activities_copy.items():
            cursor.execute('INSERT INTO {} (clan_tag, clan_name, credit_type, points) VALUES (?,?,?,?)'.
                           format(TABLE_credits_watch_clans),
                           [clantag, clanname, k, v])
    con.commit()

    # re-populate credit_watch_points
    if len(invalid_activity_types)==0:
        cursor.execute('SELECT * FROM {};'.format(TABLE_credits_watch_clans))
        rows = cursor.fetchall()
        update_mappings_clan_creditwatch(rows, MEM_mappings_clan_creditwatch)

    con.close()
    return invalid_activity_types

#add a clan to creditwatch. Whenever this method is called, you need to also call cocclient.remove_clan_updates outside this method
def remove_registered_clan_creditwatch(guild_id, clantag, data_folder):
    if clantag in MEM_mappings_clan_creditwatch.keys():
        del MEM_mappings_clan_creditwatch[clantag]
    if clantag in MEM_mappings_clan_guild.keys():
        del MEM_mappings_clan_guild[clantag]
    with open(data_folder+'/clan2guild.json', 'w') as fp:
        json.dump(MEM_mappings_clan_guild, fp)

    con = connect_db(str(guild_id))
    cursor = con.cursor()
    cursor.execute('DELETE FROM {} WHERE clan_tag=?'.
                   format(TABLE_credits_watch_clans), [clantag])
    con.commit()
    con.close()

# the clan_war_participants must conform to the format described above for the value of a current_wars entry
'''
"player_tag TEXT NOT NULL, player_name TEXT NOT NULL," \
                           "player_clantag TEXT NOT NULL, player_clanname TEXT NOT NULL, " \
                           "credits INT NOT NULL, time TEXT NOT NULL, reason TEXT);
'''
def register_war_credits(clan_tag:str, clan_name:str, rootfolder:str, clear_cache=True):
    #temporary code for debugging
    with open(rootfolder + "tmp_currentwards.pk", 'wb') as handle:
        pickle.dump(MEM_mappings_clan_currentwars, handle)
    with open(rootfolder + "tmp_clanguild.pk", 'wb') as handle:
        pickle.dump(MEM_mappings_clan_guild, handle)
    #

    if clan_tag in MEM_mappings_clan_currentwars.keys() and clan_tag in MEM_mappings_clan_guild.keys():
        time = str(datetime.datetime.now())
        guild=MEM_mappings_clan_guild[clan_tag]
        con = connect_db(str(guild))
        cursor = con.cursor()

        clan_war_participants = MEM_mappings_clan_currentwars[clan_tag]
        total_attacks=clan_war_participants[CLAN_WAR_ATTACKS]
        type = clan_war_participants[CLAN_WAR_TYPE]
        points = list_registered_clans_creditwatch(MEM_mappings_clan_guild[clan_tag], clan_tag)

        if points is not None and len(points)>0:
            points = points[clan_tag]
            if type=="cwl":
                atk = points["cwl_attack"]
                miss = points["cwl_miss"]
                war="cwl"
            else:
                atk = points["cw_attack"]
                miss = points["cw_miss"]
                war="regular war"

            #debug
            # print("registering credits for {} members".format(len(clan_war_participants[CLAN_WAR_MEMBERS])))
            # count=0
            #

            for member, remaining in clan_war_participants[CLAN_WAR_MEMBERS].items():
                #
                # count+=1
                # print("\t {}, {}".format(member, remaining))
                #

                mtag=member[0]
                mname=member[1]
                used = total_attacks-remaining
                if used>0:
                    cursor.execute('INSERT INTO {} (player_tag, player_name, ' \
                               'player_clantag, player_clanname, credits, time, reason) VALUES (?,?,?,?,?,?,?)'.
                               format(TABLE_credits_watch_players),
                               [mtag, mname, clan_tag, clan_name, used*int(atk), time,
                                "Using {} attacks in {}".format(used,war)])
                    #
                    #print("\t\t has used {}".format(used))
                    #
                if remaining>0:
                    cursor.execute('INSERT INTO {} (player_tag, player_name, ' \
                                   'player_clantag, player_clanname, credits, time, reason) VALUES (?,?,?,?,?,?,?)'.
                                   format(TABLE_credits_watch_players),
                                   [mtag, mname, clan_tag, clan_name, remaining * int(miss), time,
                                    "Missing {} attacks in {}".format(remaining, war)])
                    #
                    #print("\t\t has missed {}".format(remaining))
                    #
        #access database...
        con.commit()
        con.close()
        if clear_cache:
            del MEM_mappings_clan_currentwars[clan_tag]
        save_mappings_clan_currentwars(rootfolder)

#todo: this should be done by databases
#every time a war starts or ends, we must call this method
def save_mappings_clan_currentwars(folder):
    try:
        with open(folder+"current_wars.pk", 'wb') as handle:
            pickle.dump(MEM_mappings_clan_currentwars, handle)
    except:
        print("Unable to save current war data to file: {}".format(folder+"current_wars.pk"))

#todo: this should be done by databases
#every time the bot starts, we must call this method
def load_mappings_clan_currentwars(folder):
    try:
        with open(folder+"current_wars.pk", 'rb') as handle:
            MEM_mappings_clan_currentwars.update(pickle.load(handle))
    except:
        print("Unable to load current war data to file: {}".format(folder+"current_wars.pk"))


#player_tag, player_name, player_clantag, player_clanname, credits, time, reason
def list_playercredits(guild_id, playertag:str):
    con = connect_db(str(guild_id))
    cursor = con.cursor()
    cursor.execute('SELECT * FROM {} WHERE (player_tag=?);'.format(TABLE_credits_watch_players), [playertag])
    #cursor.execute('SELECT * FROM {} ;'.format(TABLE_credits_watch_players))

    rows = cursor.fetchall()

    records=[]
    clantag=""
    clanname=""
    playername=""
    for r in rows:
        clantag=r[3]
        clanname = r[4]
        playername = r[2]

        time=datetime.datetime.fromisoformat(r[6]).strftime("%Y-%m-%d %H:%M")
        records.append({"credits":r[5], "time":time, "reason":r[7]})

    con.close()
    return clantag, clanname, playername, records


#player_tag, player_name, player_clantag, player_clanname, credits, time, reason
def sum_clan_playercredits(guild_id, clantag:str):
    con = connect_db(str(guild_id))
    cursor = con.cursor()
    cursor.execute('SELECT * FROM {} WHERE (player_clantag=?) ;'.format(TABLE_credits_watch_players), [clantag])
    #cursor.execute('SELECT * FROM {} ;'.format(TABLE_credits_watch_players))

    rows = cursor.fetchall()
    clanname=""
    player_credits={}
    player_name={}

    last_updated=None
    for r in rows:
        time=datetime.datetime.fromisoformat(r[6]).strftime("%Y-%m-%d %H:%M")
        if last_updated is None or last_updated<time:
            last_updated=time

        clanname=r[4]
        if r[1] in player_credits.keys():
            player_credits[r[1]]=player_credits[r[1]]+float(r[5])
        else:
            player_credits[r[1]] = float(r[5])
            player_name[r[1]]=r[2]

    con.close()
    return clanname, player_credits, player_name, last_updated

#player_tag, player_name, player_clantag, player_clanname, credits, time, reason
def add_player_credits(guild_id, player_tag, player_name, player_clantag, player_clanname, credits, note=None):
    if type(note) is tuple:
        note = ' '.join(note)
    elif note is not None:
        note = str(note)

    time = str(datetime.datetime.now())
    con = connect_db(str(guild_id))
    cursor = con.cursor()
    cursor.execute('INSERT INTO {} (player_tag, player_name, ' \
                   'player_clantag, player_clanname, credits, time, reason) VALUES (?,?,?,?,?,?,?)'.
                   format(TABLE_credits_watch_players),
                   [player_tag, player_name, player_clantag, player_clanname, credits, time,
                    note])
    con.commit()
    con.close()

def clear_credits_for_clan(guidid, clan_tag):
    con = connect_db(str(guidid))
    cursor = con.cursor()
    cursor.execute('DELETE FROM {} WHERE player_clantag=?'.format(TABLE_credits_watch_players),
                   [clan_tag])
    con.commit()
    con.close()