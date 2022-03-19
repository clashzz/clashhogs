import random,sys,coc

import disnake
from disnake.ext import commands

description = """An example bot to showcase the disnake.ext.commands extension
module.
There are a number of utility commands being showcased here."""

intents = disnake.Intents.all()


bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("?"), description=description, intents=intents
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


@bot.command()
async def roll(ctx, dice: str):
    """Rolls a dice in NdN format."""
    try:
        rolls, limit = map(int, dice.split("d"))
    except Exception:
        await ctx.send("Format has to be in NdN!")
        return

    result = ", ".join(str(random.randint(1, limit)) for r in range(rolls))
    await ctx.send(result)


@bot.command(description="For when you wanna settle the score some other way")
async def choose(ctx, *choices: str):
    """Chooses between multiple choices."""
    await ctx.send(random.choice(choices))


@bot.command()
async def repeat(ctx, times: int, content="repeating..."):
    """Repeats a message multiple times."""
    for i in range(times):
        await ctx.send(content)


@bot.command()
async def joined(ctx, member: disnake.Member):
    """Says when a member joined."""
    await ctx.send(f"{member.name} joined in {member.joined_at}")


@bot.group()
async def cool(ctx):
    """Says if a user is cool.
    In reality this just checks if a subcommand is being invoked.
    """
    if ctx.invoked_subcommand is None:
        await ctx.send(f"No, {ctx.subcommand_passed} is not cool")


@cool.command(name="bot")
async def bot_(ctx):
    """Is the bot cool?"""
    await ctx.send("Yes, the bot is cool.")

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