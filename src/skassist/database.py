'''
This file implements data storage.
Currently everything saved in member.
TODO: use mongodb
'''
import sqlite3, threading, pickle
from pathlib import Path
from skassist import models
TABLE_channel_mapping_warmiss="channel_mapping_warmiss"
TABLE_member_attacks="member_attacks"


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
    con.commit()

    #populate channel mappings into memory
    cursor.execute("SELECT * FROM {};".format(TABLE_channel_mapping_warmiss))
    rows = cursor.fetchall()
    for row in rows:
        print(row)
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

            #convert back to player
            #update player
            #save
        #     cursor.execute('UPDATE {} SET data = ? WHERE id = ?'.format(TABLE_channel_mapping_warmiss),
        #                    [pair[1], clan, pair[0]])
        # if not p._data_populated:
        #     p.summarize_attacks()

        # self.output_player_war_data(outfolder, p)
    con.commit()
    con.close()


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



# guild_id=58686983354
# check_database(guild_id)
#
# from_channel=5475688
# to_channel=6869865
# add_channel_mappings_warmiss_db((from_channel,to_channel), guild_id, "DS")
# add_channel_mappings_warmiss_db((from_channel,to_channel), guild_id, "DS")
# add_channel_mappings_warmiss_db((from_channel,to_channel), guild_id, "DS")
# print("done")