import logging, pickle
import sys
import coc

from coc import utils
# t=utils.get_season_end()
#
# file = open("/home/zz/Work/sidekickassist/tmp/tmp_currentwards.pk",'rb')
# object_file = pickle.load(file)
# print(object_file)
# exit(1)

'''
coc 1.3, using tags works
'''

print(str(None))

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
    print("War state changed, old war = {}, new war = {}".format(old_war.state, new_war.state))
    log.info("War state changed, old war = {}, new war = {}".format(old_war.state, new_war.state))
    if old_war.clan is not None and old_war.state != "notInWar":
        log.info("\t old war home clan is {}".format(old_war.clan))
    if new_war.clan is not None and new_war.state != "notInWar":
        log.info("\t new war home clan is {}".format(new_war.clan))


    ##########################
    # set up for the new war
    ##########################
    if old_war.state == "preparation" and new_war.state == "inWar":
        log.info(
            "War started between: {} and {}, type={}".format(new_war.clan, new_war.opponent, new_war.type))
        clan_home = new_war.clan

    print("finished")


@client.event
@coc.WarEvents.war_attack()
async def current_war_stats(attack, war):
    print(f"Attack number {attack.order}\n({attack.attacker.map_position}).{attack.attacker} of {attack.attacker.clan} "

             f"attacked ({attack.defender.map_position}).{attack.defender} of {attack.defender.clan}")

#adding clans to receive update for, seems not working for war events
clans=["#2YGUPUU82","#2L29RRJU9","#2998V8JG0","#2PYQOV822"]
for c in clans:
    client.add_clan_updates(c)
    client.add_war_updates(c)

client.loop.run_forever()