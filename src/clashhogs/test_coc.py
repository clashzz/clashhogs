import logging
import os

import coc, sys

from coc import utils

client = coc.login(
    sys.argv[1],
    sys.argv[2],
    key_names="coc.py tests",
    client=coc.EventsClient,
)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger()


"""Clan Events"""

@client.event  # Pro Tip : if you don't have @client.event then your events won't run! Don't forget it!
@coc.ClanEvents.member_donations()
async def on_clan_member_donation(old_member, new_member):
    final_donated_troops = new_member.donations - old_member.donations
    log.info(f"{new_member} of {new_member.clan} just donated {final_donated_troops} troops.")


@client.event
@coc.ClanEvents.points()
async def on_clan_trophy_change(old_clan, new_clan):
    log.info(f"{new_clan.name} total trophies changed from {old_clan.points} to {new_clan.points}")


@client.event
@coc.ClanEvents.member_versus_trophies()
async def clan_member_versus_trophies_changed(old_member, new_member):
    log.info(f"{new_member} versus trophies changed from {old_member.versus_trophies} to {new_member.versus_trophies}")


"""War Events"""


@client.event
@coc.WarEvents.war_attack()
async def current_war_stats(attack, war):
    log.info(f"Attack number {attack.order}\n({attack.attacker.map_position}).{attack.attacker} of {attack.attacker.clan} "
             f"attacked ({attack.defender.map_position}).{attack.defender} of {attack.defender.clan}")

"""Client Events"""


@client.event
@coc.ClientEvents.maintenance_start()
async def on_maintenance():
    log.info("Maintenace Started")


@client.event
@coc.ClientEvents.maintenance_completion()
async def on_maintenance_completion(time_started):
    log.info("Maintenace Ended; started at %s", time_started)


@client.event
@coc.ClientEvents.new_season_start()
async def season_started():
    log.info("New season started, and will finish at %s", str(utils.get_season_end()))


tags=["#2L29RRJU9","#2YGUPUU82"]
for t in tags:
    print("adding {} to updates ".format(t))
    client.add_war_updates(t)
    client.add_clan_updates(t)



client.loop.run_forever()