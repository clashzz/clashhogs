import logging
import os

import coc, sys

from coc import utils
'''
#2PQ9RCU8U #2PV9JQUYP #2Q28RRQPJ #2YGUPUU82 #2L29RRJU9 #2PVQOV822 #GQPQPJC #2G89JOOLU

A. Nation #2PQ9RCU8U CWL M2 (AN, or just A) for non rushed TH14+.
- Link: https://link.clashofclans.com/en?action=OpenClanProfile&tag=2PQ9RCU8U
- Rules: 「📜」clan-rules-an 

B. Nation #2PV9JQUYP CWL C2  (BN, or just B) rushed or non-rushed TH12+
- Link: https://link.clashofclans.com/en?action=OpenClanProfile&tag=2PV9JQUYP
- Rules: 「📜」clan-rules-bn 

C. Nation #2Q28RRQPJ CWL C3  (CN, or just C) at least max TH10
- Link: https://link.clashofclans.com/en?action=OpenClanProfile&tag=2Q28RRQPJ
- Rules: 「📜」clan-rules-cn 

DeadSages #2YGUPUU82 CWL C1  (DS) for TH11+ (rushed or non-rushed). 
- Link: https://link.clashofclans.com/en?action=OpenClanProfile&tag=2YGUPUU82
- Rules: 「📜」clan-rules-ds 

DeadSages Elite #2L29RRJU9  CWL C3 (DSE) for non-rushed,TH11+
- Link: https://link.clashofclans.com/en?action=OpenClanProfile&tag=2L29RRJU9
- Rules: 「📜」clan-rules-dse

DeadSages Max #2PVQOV822 CWL G2 (DSM) for TH9+ (any)
- Link: https://link.clashofclans.com/en?action=OpenClanProfile&tag=#2PVQOV822
- Rules: 「📜」clan-rules-dsm

Late Knighters #GQPQPJC CWL G1 (LK) for TH11+ (non rushed)
- Link: https://link.clashofclans.com/en?action=OpenClanProfile&tag=GQPQPJC
- Rules: 「📜」clan-rules-lk

Ultra Knighters #2G89JOOLU S2 (UK) for TH3+
- Link: https://link.clashofclans.com/en?action=OpenClanProfile&tag=2G89J00LU
- Rules: 「📜」clan-rules-uk 
'''
client = coc.login(
    sys.argv[2],
    sys.argv[3],
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