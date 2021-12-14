import logging
import sys
import coc

from coc import utils
'''
coc 1.3, using tags works
'''

client = coc.login(
    sys.argv[1], sys.argv[2],
    key_names="coc.py tests",
    client=coc.EventsClient,
)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger()

# method 1 for registering what clans to receive update for. This works for all events
clan_tags = ["#2YGUPUU82","#2L29RRJU9","#2998V8JG0","#2PYQOV822"]
clan_tags = None

@client.event  # Pro Tip : if you don't have @client.event then your events won't run! Don't forget it!
@coc.ClanEvents.member_donations()
async def on_clan_member_donation(old_member, new_member):
    final_donated_troops = new_member.donations - old_member.donations
    print(f"{new_member} of {new_member.clan} just donated {final_donated_troops} troops.")

"""War Events"""
@client.event
@coc.WarEvents.state() #when no war, old_war state is 'notInWar'
async def current_war_state(old_war, new_war):
    print(">> old war: {}, state={}".format(old_war, old_war.state))
    print(">> new war: {}, state={}".format(new_war, new_war.state))
    print(new_war.members)
    for m in new_war.members:
        print("\t{}, {}".format(m.tag, m.name))


@client.event
@coc.WarEvents.war_attack()
async def current_war_stats(attack, war):
    print(f"Attack number {attack.order}\n({attack.attacker.map_position}).{attack.attacker} of {attack.attacker.clan} "

             f"attacked ({attack.defender.map_position}).{attack.defender} of {attack.defender.clan}")

#adding clans to receive update for, seems not working for war events
clans=["#2YGUPUU82","#2L29RRJU9","#2998V8JG0","#2PYQOV822"]
client.add_clan_updates(*clans)
client.add_war_updates(*clans)

client.loop.run_forever()