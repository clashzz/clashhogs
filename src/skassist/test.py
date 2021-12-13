import logging
import os
import sys

import coc

from coc import utils

client = coc.login(
    sys.argv[1], sys.argv[2],
    key_names="coc.py tests",
    client=coc.EventsClient,
)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger()


clan_tags = [] #ds, tb, dse, ds


@client.event  # Pro Tip : if you don't have @client.event then your events won't run! Don't forget it!
@coc.ClanEvents.member_donations(tags=clan_tags)
async def on_clan_member_donation(old_member, new_member):
    final_donated_troops = new_member.donations - old_member.donations
    print(f"{new_member} of {new_member.clan} just donated {final_donated_troops} troops.")

"""War Events"""
@client.event
@coc.WarEvents.state(tags=clan_tags)
async def current_war_state(old_war, new_war):
    print(">> old war: {}, state={}".format(old_war, old_war.state))
    print(">> new war: {}, state={}".format(new_war, new_war.state))
    print(new_war.members)
    for m in new_war.members:
        print("\t{}, {}".format(m.tag, m.name))


@client.event
@coc.WarEvents.war_attack(tags=clan_tags)
async def current_war_stats(attack, war):
    print(f"Attack number {attack.order}\n({attack.attacker.map_position}).{attack.attacker} of {attack.attacker.clan} "

             f"attacked ({attack.defender.map_position}).{attack.defender} of {attack.defender.clan}")

# @client.event
# @coc.ClanEvents.member_received(tags=clan_tags)
# async def on_clan_member_donation_receive(old_member, new_member):
#     final_received_troops = new_member.received - old_member.received
#     print(f"{new_member} of {new_member.clan} just received {final_received_troops} troops.")
#
#
# @client.event
# @coc.ClanEvents.member_join(tags=clan_tags)
# async def on_clan_member_join(member, clan):
#     print(f"{member.name} has joined {clan.name}")

#
# @client.event
# @coc.ClanEvents.member_leave(tags=clan_tags)
# async def on_clan_member_leave(member, clan):
#     print(f"{member.name} has left {clan.name}")



# async def add_clan_players():
#     async for clan in client.get_clans(clan_tags):
#         client.add_player_updates(*[member.tag for member in clan.members])

#client.loop.run_until_complete(add_clan_players())
for clan in ["#2YGUPUU82","#2L29RRJU9"]:
    client.add_clan_updates(clan)

client.loop.run_forever()