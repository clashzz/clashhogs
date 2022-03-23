import disnake,sys
from disnake.ext import commands

intents = disnake.Intents.all()

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', test_guilds=[880595096461004830],
            sync_commands_debug=True, intents=intents)

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")

class Confirm(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @disnake.ui.button(label="Confirm", style=disnake.ButtonStyle.green)
    async def confirm(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await interaction.response.send_message("Confirmed")
        self.value = True
        self.stop()

    @disnake.ui.button(label="Cancel", style=disnake.ButtonStyle.grey)
    async def cancel(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await interaction.response.send_message("Cancelled")
        self.value = False
        self.stop()

bot = Bot()

@bot.slash_command(description="testing button.")
async def ask(inter):
    """Asks the user a question to confirm something."""
    # We create the view and assign it to a variable so we can wait for it later.
    view = Confirm()
    await inter.response.send_message("Do you want to continue?", view=view)
    # Wait for the View to stop listening for input...
    if await view.wait():
        await inter.followup.send_message("Timed out...")
    await inter.followup.send("all done, this is to test followup")
    # if view.value is None:
    #     await inter.response.send_message("Timed out...")
    # elif view.value:
    #     await inter.response.send_message("Confirmed...")
    # else:
    #     await inter.response.send_message("Cancelled...")


bot.run(sys.argv[1])