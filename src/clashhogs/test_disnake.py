import random,sys,coc

import disnake
from disnake.ext import commands

description = """An example bot to showcase the disnake.ext.commands extension
module.
There are a number of utility commands being showcased here."""

intents = disnake.Intents.all()

bot = commands.Bot(
    command_prefix='!',
    test_guilds=[880595096461004830],
    # In the list above you can specify the IDs of your test guilds.
    # Why is this kwarg called test_guilds? This is because you're not meant to use
    # local registration in production, since you may exceed the rate limits.
    sync_commands_debug=True
)

client = coc.login(
    sys.argv[2],
    sys.argv[3],
    key_names="coc.py tests",
    client=coc.EventsClient,
)



@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")


@bot.command()
async def add(ctx, left: int, right: int):
    """Adds two numbers together."""
    await ctx.send(left + right)
    clan = await client.get_clan("#2YGUPUU82")
    print("done")

@bot.slash_command(description="Responds with 'World'")
async def hello(inter):
    await inter.response.send_message("World")

@client.event  # Pro Tip : if you don't have @client.event then your events won't run! Don't forget it!
@coc.ClanEvents.member_donations()
async def on_clan_member_donation(old_member, new_member):
    final_donated_troops = new_member.donations - old_member.donations
    print(f"{new_member} of {new_member.clan} just donated {final_donated_troops} troops.")


@client.event
@coc.ClanEvents.points()
async def on_clan_trophy_change(old_clan, new_clan):
    print(f"{new_clan.name} total trophies changed from {old_clan.points} to {new_clan.points}")


@client.event
@coc.ClanEvents.member_versus_trophies()
async def clan_member_versus_trophies_changed(old_member, new_member):
    print(f"{new_member} versus trophies changed from {old_member.versus_trophies} to {new_member.versus_trophies}")

tags=["#2L29RRJU9","#2YGUPUU82"]
for t in tags:
    print("adding {} to updates ".format(t))
    client.add_war_updates(t)
    client.add_clan_updates(t)

bot.run(sys.argv[1])