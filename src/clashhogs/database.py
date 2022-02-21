'''
This file implements data storage.
Currently everything saved in member.

Each guild will have a unique DB. This is identified by the guild id when the bot connects to a discord server
'''
import time
from datetime import datetime
import datetime, sqlite3, threading, json, pickle
from pathlib import Path
from clashhogs import models, util

DB_CLAN_SETUP= "master_clan_setup"
TABLE_clanwatch="clanwatch"

TABLE_channel_mapping_warmiss = "channel_mapping_warmiss"
TABLE_member_attacks = "member_attacks"
TABLE_member_warnings = "member_warnings"
TABLE_war_attacks = "war_attacks"
TABLE_credits_watch_players = "credit_watch_players"

CLAN_NAME="clan_name"
CLAN_WAR_TAG="war_tag"
CLAN_WAR_END="war_end"
CLAN_WAR_TYPE="type"
CLAN_WAR_MEMBERS="members"
CLAN_WAR_ATTACKS="attacks"

# This needs to be initialised every time the bot starts, or updated when a clan registers for/removed from war/credit watch
MEM_mappings_clanwatch = {}  # key: clan tag; value: models.ClanWatch

# key=guild id|clan name (e.g., 3492301120|myclan
# value=a list of tuple (x, y) where x is the sidekick channel (name) of war feed, y is the channel (name) to tally
# missed attacks. This needs to be initialised every time the bot starts, or when a guild connects
MEM_mappings_guild_warmisschannel = {}

#current coc api isn't reliable in detecting war state change during cwl. as an alternative,
#we store current cwl wars for each clan, and check for the change of war id to decide if a new war has started
MEM_current_cwl_wars={} #key=clan ID, value= (war id, war object)

def reset_cwl_war_data(clantag:str, warobj=None):
    if warobj is None:
        if clantag in MEM_current_cwl_wars.keys():
            del MEM_current_cwl_wars[clantag]
    else:
        MEM_current_cwl_wars[clantag] = (warobj.war_tag, warobj)

def update_if_same_cwl_war(clantag:str, warobj):
    if clantag not in MEM_current_cwl_wars.keys():
        MEM_current_cwl_wars[clantag] = (warobj.war_tag, warobj)
        return True
    else:
        prev_war = MEM_current_cwl_wars[clantag]
        if prev_war[0] == warobj.war_tag:
            MEM_current_cwl_wars[clantag]= (warobj.war_tag, warobj)
            return True
        #this clan has a previous cwl war, and its tag is not the same as this one
        return False

def connect_db(dbname):
    targetfolder = "db/"
    Path(targetfolder).mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(targetfolder + str(dbname) + '.db')
    return con

def check_master_database():
    lock = threading.Lock()
    lock.acquire()
    con = connect_db(DB_CLAN_SETUP)
    cursor = con.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table_names = []
    for t in cursor.fetchall():
        table_names.append(t[0])
    # if table does not exist, create them
    if TABLE_clanwatch not in table_names:
        create_statement = "CREATE TABLE {} (clantag text PRIMARY KEY, guildid text NOT NULL, " \
                           "data BLOB NOT NULL);".format(TABLE_clanwatch)
        cursor.execute(create_statement)
    con.commit()
    con.close()
    lock.release()

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
    if TABLE_war_attacks not in table_names:
        create_statement = "CREATE TABLE {} (id INTEGER PRIMARY KEY, " \
                           "player_tag TEXT NOT NULL, " \
                           "player_name TEXT NOT NULL, " \
                           "clan_tag TEXT NOT NULL, " \
                           "clan_name TEXT NOT NULL, " \
                           "stars int NOT NULL, " \
                           "attacker_th int NOT NULL, " \
                           "defender_th int NOT NULL, " \
                           "time int NOT NULL," \
                           "war_type TEXT NOT NULL);".format(TABLE_war_attacks)
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

    # populate MEM_mappings_guild_warmisschannel
    cursor.execute("SELECT * FROM {};".format(TABLE_channel_mapping_warmiss))
    rows = cursor.fetchall()
    for row in rows:
        update_mappings_guild_warmisschannel(guild_id, row[0], row[1], row[2])

    lock.release()

def get_clanwatch(clantag, guildid=None):
    clanwatch=None
    lock = threading.Lock()
    lock.acquire()
    con = connect_db(DB_CLAN_SETUP)
    cursor = con.cursor()
    if guildid is None:
        cursor.execute('SELECT * FROM {} WHERE (clantag=?);'.format(TABLE_clanwatch), [clantag])
    else:
        cursor.execute('SELECT * FROM {} WHERE (clantag=?) AND (guildid=?);'.format(TABLE_clanwatch), [clantag, guildid])
    entry = cursor.fetchone()
    if entry is not None and len(entry)>0:
        clanwatch = pickle.loads(entry[2])
    con.close()
    lock.release()
    return clanwatch

def get_clanwatch_by_guild(guildid):
    res=[]
    lock = threading.Lock()
    lock.acquire()
    con = connect_db(DB_CLAN_SETUP)
    cursor = con.cursor()
    cursor.execute('SELECT * FROM {} WHERE (guildid=?);'.format(TABLE_clanwatch), [guildid])
    entry = cursor.fetchall()
    for r in entry:
        clanwatch = pickle.loads(r[2])
        res.append(clanwatch)
    con.close()
    lock.release()
    return res

def get_clanwatch_all():
    res=[]
    lock = threading.Lock()
    lock.acquire()
    con = connect_db(DB_CLAN_SETUP)
    cursor = con.cursor()
    cursor.execute('SELECT * FROM {};'.format(TABLE_clanwatch))
    entry = cursor.fetchall()
    for r in entry:
        clanwatch = pickle.loads(r[2])
        res.append(clanwatch)
    con.close()
    lock.release()
    return res

#put clan watch into memory
def init_clanwatch_all():
    clans=get_clanwatch_all()
    for c in clans:
        MEM_mappings_clanwatch[c._tag]=c
    return clans


def add_clanwatch(clantag, clanwatch):
    lock = threading.Lock()
    lock.acquire()
    con = connect_db(DB_CLAN_SETUP)
    cursor = con.cursor()
    dataobj = pickle.dumps(clanwatch)
    cursor.execute('INSERT OR IGNORE INTO {} (clantag, guildid, data) VALUES (?, ?,?)'.
                   format(TABLE_clanwatch), [clantag, clanwatch._guildid,dataobj])
    cursor.execute('UPDATE {} SET data= ?, guildid=? WHERE clantag= ?'.
                   format(TABLE_clanwatch), [dataobj, clanwatch._guildid, clantag])
    con.commit()
    con.close()
    MEM_mappings_clanwatch[clantag]=clanwatch
    lock.release()
    return clanwatch

def remove_clanwatch(clantag):
    lock = threading.Lock()
    lock.acquire()
    con = connect_db(DB_CLAN_SETUP)
    cursor = con.cursor()
    cursor.execute('DELETE FROM {} WHERE clantag=?;'.format(TABLE_clanwatch), [clantag])
    con.commit()
    con.close()
    if clantag in MEM_mappings_clanwatch.keys():
        del MEM_mappings_clanwatch[clantag]
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


def delete_warning(guild_id, clanname,warning_id):
    con = connect_db(str(guild_id))
    cursor = con.cursor()

    #delete by time
    try:
        by = datetime.datetime.fromisoformat(warning_id)
        cursor.execute('SELECT * FROM {} WHERE clan=?'.
                       format(TABLE_member_warnings), [clanname])
        rows = cursor.fetchall()
        if len(rows) == 0:
            con.commit()
            con.close()
            return False
        ids=[]
        for r in rows:
            d = r[4]
            if datetime.datetime.fromisoformat(d)< by:
                ids.append(r[0])
        for id in ids:
            r = cursor.execute('DELETE FROM {} WHERE id=?'.
                               format(TABLE_member_warnings), [id])

    except:        #delete one specific id
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

#add a clan to creditwatch. Whenever this method is called, you need to also call cocclient.add_war_updates outside this method
def registered_clan_creditwatch(guild_id, clantag, *values):
    clan_watch = get_clanwatch(clantag, guild_id)
    if clan_watch is None:
        return None

    invalid_activity_types=""

    if len(values[0])<1:
        clan_watch.reset_credits()
        add_clanwatch(clantag, clan_watch)
    else:
        credit_watch_activities_copy = models.STANDARD_CREDITS.copy()
        for v in values[0]:
            if '=' not in v:
                invalid_activity_types+="\n\t"+str(v)
                continue
            parts=v.split("=")
            if parts[0].strip() not in credit_watch_activities_copy.keys():
                invalid_activity_types+="\n\t"+str(v)
                continue
            try:
                float(parts[1].strip())
            except:
                invalid_activity_types += "\n\t" + str(v)
                continue
            else:
                credit_watch_activities_copy[parts[0].strip()]=parts[1].strip()

        clan_watch._creditwatch_points=credit_watch_activities_copy
        add_clanwatch(clantag, clan_watch)

    return invalid_activity_types

'''
"player_tag TEXT NOT NULL, player_name TEXT NOT NULL," \
                           "player_clantag TEXT NOT NULL, player_clanname TEXT NOT NULL, " \
                           "credits INT NOT NULL, time TEXT NOT NULL, reason TEXT);
'''
def save_war_attacks(clan_tag:str, clan_name:str, war_type:str, total_attacks:int, attack_data:dict, clear_cache=True):
    added=False
    missed_attacks = {}
    if clan_tag in MEM_mappings_clanwatch.keys():
        clanwatch=MEM_mappings_clanwatch[clan_tag]
        time = datetime.datetime.now()
        guild=clanwatch._guildid
        con = connect_db(str(guild))
        cursor = con.cursor()

        points = clanwatch._creditwatch_points

        if war_type == "cwl":
            atkp = points["cwl_attack"]
            miss = points["cwl_miss"]
            war = "cwl"
        else:
            atkp = points["cw_attack"]
            miss = points["cw_miss"]
            war = "regular war"

        for member, attacks in attack_data.items():
            mtag = member[1]
            mname = member[0]
            #adding attack record into database
            '''
            "player_tag TEXT NOT NULL, " \
                           "player_name TEXT NOT NULL, " \
                           "clan_tag TEXT NOT NULL, " \
                           "clan_name TEXT NOT NULL, " \
                           "stars int NOT NULL, " \
                           "attacker_th int NOT NULL, " \
                           "defender_th int NOT NULL, " \
                           "time TEXT NOT NULL," \
                           "war_type TEXT NOT NULL);
            '''
            for atk in attacks:
                cursor.execute('INSERT INTO {} (player_tag, ' \
                               'player_name, clan_tag, clan_name, stars, attacker_th,' \
                               'defender_th, time, war_type) VALUES (?,?,?,?,?,?,?,?,?)'.
                               format(TABLE_war_attacks),
                               [mtag, mname, clan_tag, clan_name, atk._stars,
                                atk._source_thlvl, atk._target_thlvl, time, war_type])

            #saving credits and work out missed attacks
            used = len(attacks)
            remaining = total_attacks-used
            if used > 0:
                cursor.execute('INSERT INTO {} (player_tag, player_name, ' \
                               'player_clantag, player_clanname, credits, time, reason) VALUES (?,?,?,?,?,?,?)'.
                               format(TABLE_credits_watch_players),
                               [mtag, mname, clan_tag, clan_name, used * int(atkp), time,
                                "Using {} attacks in {}".format(used, war)])
                #
                # print("\t\t has used {}".format(used))
                #
            if remaining > 0:
                cursor.execute('INSERT INTO {} (player_tag, player_name, ' \
                               'player_clantag, player_clanname, credits, time, reason) VALUES (?,?,?,?,?,?,?)'.
                               format(TABLE_credits_watch_players),
                               [mtag, mname, clan_tag, clan_name, remaining * int(miss), time,
                                "Missing {} attacks in {}".format(remaining, war)])
                key = (mtag, mname)
                if key in missed_attacks.keys():
                    missed_attacks[key] = int(remaining) + missed_attacks[key]
                else:
                    missed_attacks[key] = int(remaining)
                #recording missed attacks in attack data
                for i in range (0, remaining):
                    cursor.execute('INSERT INTO {} (player_tag, ' \
                                   'player_name, clan_tag, clan_name, stars, attacker_th,' \
                                   'defender_th, time, war_type) VALUES (?,?,?,?,?,?,?,?,?)'.
                                   format(TABLE_war_attacks),
                                   [mtag, mname, clan_tag, clan_name, -1,
                                    -1, -1, time, war_type])

        #access database...
        con.commit()
        con.close()
        added=True
    return missed_attacks, added

def find_war_data(clan_tag:str, start:datetime, end:datetime):
    if clan_tag in MEM_mappings_clanwatch.keys():
        clanwatch=MEM_mappings_clanwatch[clan_tag]
        guild=clanwatch._guildid
        con = connect_db(str(guild))
        cursor = con.cursor()
        cursor.execute('SELECT * FROM {} WHERE (clan_tag=?) AND (time > ?) AND (time < ?);'.format(TABLE_credits_watch_players), [clan_tag,
                                                                                                                                  start, end])
        rows = cursor.fetchall()
        return rows


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
def add_player_credits(guild_id, author, player_tag, player_name, player_clantag, player_clanname, credits, note=None):
    if type(note) is tuple:
        note = ' '.join(note)
        note += " (Added by {})".format(author)
    elif note is not None:
        note = str(note)
        note += " (Added by {})".format(author)
    else:
        note = "(Added by {})".format(author)

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
    clanwatch = get_clanwatch(clan_tag, guidid)
    if clanwatch is None:
        return None
    con = connect_db(str(guidid))
    cursor = con.cursor()
    cursor.execute('DELETE FROM {} WHERE player_clantag=?'.format(TABLE_credits_watch_players),
                   [clan_tag])
    con.commit()
    con.close()
    return True


if __name__ == "__main__":
    con = connect_db("test_db")
    cursor = con.cursor()
    create_statement = "CREATE TABLE IF NOT EXISTS mytable (main_id int PRIMARY KEY, " \
                           "time int NOT NULL);"
    cursor.execute(create_statement)

    cursor.execute('INSERT INTO mytable (time) VALUES (?)',
                   [datetime.datetime.now()])
    time.sleep(2)
    cursor.execute('INSERT INTO mytable (time) VALUES (?)',
                   [datetime.datetime.now()])
    time.sleep(2)
    cursor.execute('INSERT INTO mytable (time) VALUES (?)',
                   [datetime.datetime.now()])
    time.sleep(2)
    cursor.execute('INSERT INTO mytable (time) VALUES (?)',
                   [datetime.datetime.now()])
    time.sleep(2)
    cursor.execute('INSERT INTO mytable (time) VALUES (?)',
                   [datetime.datetime.now()])
    time.sleep(2)
    con.commit()

    cursor.execute('SELECT * FROM mytable')
    rows=cursor.fetchall()
    print("")

    date_string = "2022-02-21 21:24:00"
    start=datetime.datetime.fromisoformat(date_string)
    cursor.execute('SELECT * FROM mytable WHERE time<? AND time >?',
                   [datetime.datetime.now(), start])
    rows=cursor.fetchall()
    print("")

