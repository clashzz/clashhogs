'''
This file implements data storage.
Currently everything saved in member.

Each guild will have a unique DB. This is identified by the guild id when the bot connects to a discord server
'''
import datetime
import sqlite3
import threading
import pickle
from pathlib import Path
from skassist import models, util
TABLE_channel_mapping_warmiss="channel_mapping_warmiss"
TABLE_member_attacks="member_attacks"
TABLE_member_warnings="member_warnings"


guilds={}

#key=guild id|clan name (e.g., 3492301120|myclan
#value=a list of tuple (x, y) where x is the sidekick channel (name) of war feed, y is the channel (name) to tally
#missed attacks
channel_mapping_warmiss={}

def connect_db(dbname):
    targetfolder = "db/"
    Path(targetfolder).mkdir(parents=True, exist_ok=True)
    con=sqlite3.connect(targetfolder+str(dbname)+'.db')
    return con

def update_channel_mapping_warmiss(guild_id, from_id, to_id,clan):
    lock = threading.Lock()
    lock.acquire()
    key = str(guild_id) + "|" + str(from_id)
    channel_mapping_warmiss[key] = str(guild_id) + "|" + str(to_id) + "|" + str(clan)
    lock.release()

def check_database(guild_id):
    con = connect_db(guild_id)
    cursor=con.cursor()

    #check if this guild's database has all necessary data tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table_names=[]
    for t in cursor.fetchall():
        table_names.append(t[0])
    #if table does not exist, create them
    if TABLE_channel_mapping_warmiss not in table_names:
        create_statement="CREATE TABLE IF NOT EXISTS {} (from_id integer PRIMARY KEY, " \
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
    con.commit()

    #populate channel mappings into memory
    cursor.execute("SELECT * FROM {};".format(TABLE_channel_mapping_warmiss))
    rows = cursor.fetchall()
    for row in rows:
        update_channel_mapping_warmiss(guild_id,row[0],row[1],row[2])
    con.close()

def add_channel_mappings_warmiss_db(pair:tuple, guild_id, clan):
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
    update_channel_mapping_warmiss(guild_id, pair[0], pair[1],clan)

def get_warmiss_mappings_for_guild_db(guild_id):
    con = connect_db(str(guild_id))
    cursor = con.cursor()
    cursor.execute('SELECT * FROM {};'.format(TABLE_channel_mapping_warmiss))
    rows = cursor.fetchall()
    res=[]
    if rows is None:
        return res
    else:
        for row in rows:
            res.append((row[0],row[1],row[2]))
    con.close()
    return res

def remove_warmiss_mappings_for_guild_db(guild_id, from_channel_id):
    key = str(guild_id) + "|" + str(from_channel_id)
    if key in channel_mapping_warmiss.keys():
        del channel_mapping_warmiss[key]

    con = connect_db(str(guild_id))
    cursor = con.cursor()
    cursor.execute('DELETE FROM {} WHERE from_id=?;'.format(TABLE_channel_mapping_warmiss),[from_channel_id])
    con.commit()
    con.close()


def save_individual_war_data(guild_id, clanwardata:models.ClanWarData):
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
            past_data=entry[2]
            past_p = pickle.loads(past_data)
            for t, atk in p._attacks.items():
                if t in past_p._attacks.keys():
                    continue
                past_p._attacks[t]=atk
            b = pickle.dumps(past_p)
            cursor.execute('UPDATE {} SET data = ? WHERE id = ?'.format(TABLE_member_attacks),
                                               [b, p._tag])

    con.commit()
    con.close()


def load_individual_war_data(guild_id, player_tag, from_date, to_date):

    lock = threading.Lock()
    lock.acquire()
    res={}
    player_tag=util.normalise_player_tag(player_tag)
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
            if time<to_date and time>from_date:
                res[time]=atk

    con.close()
    lock.release()
    return res


# def add_channel_mappings_warmiss(pair:tuple, guild_id, clan):
#     key  = str(guild_id)+"|"+str(pair[0])
#     channel_mapping_warmiss[key] = str(guild_id) + "|" + str(pair[1]) + "|"+str(clan)


def has_warmiss_fromchannel(guild_id, channel_id):
    key = str(guild_id)+"|"+str(channel_id)
    return key in channel_mapping_warmiss.keys()

def get_warmiss_tochannel(guild_id, channel_id):
    key = str(guild_id) + "|" + str(channel_id)
    values= channel_mapping_warmiss[key].split("|")
    return int(values[1]), values[2] #1 = to_channel under the same guild, 2 = clan name

def add_warning(guild_id, clan, person, point, note=None):
    if type(note) is tuple:
        note=' '.join(note)
    elif note is not None:
        note=str(note)

    con = connect_db(str(guild_id))
    cursor = con.cursor()
    cursor.execute('INSERT INTO {} (clan, name, value, date, note) VALUES (?,?,?,?,?)'.
                   format(TABLE_member_warnings),
                   [clan, person, point, datetime.datetime.now(), note])
    con.commit()
    con.close()

def list_warnings(guild_id, clan, person=None):
    res=[]
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

def delete_warning(guild_id, warning_id):
    con = connect_db(str(guild_id))
    cursor = con.cursor()
    r = cursor.execute('DELETE FROM {} WHERE id=?'.
                   format(TABLE_member_warnings), [warning_id])
    con.commit()
    con.close()


# guild_id=58686983354
# check_database(guild_id)
#
# from_channel=5475688
# to_channel=6869865
# add_channel_mappings_warmiss_db((from_channel,to_channel), guild_id, "DS")
# add_channel_mappings_warmiss_db((from_channel,to_channel), guild_id, "DS")
# add_channel_mappings_warmiss_db((from_channel,to_channel), guild_id, "DS")
# print("done")