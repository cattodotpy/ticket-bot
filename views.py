import discord
from bot_object import TicketBot


class TicketCreate(discord.ui.View):
    def __init__(self, bot: TicketBot):
        super().__init__(
            timeout=None,
        )
        self.bot = bot

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.green)
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        ticket = await self.bot.create_ticket(interaction.guild, interaction.user)
        await interaction.followup.send(f"Ticket {ticket.mention} has been created.", ephemeral=True)
        await ticket.send(
            embed=discord.Embed(
                title=ticket.name,
                description=f"{interaction.user.mention}, thank you for creating a ticket. Please wait for a staff member to respond.",
            ),
            content=interaction.user.mention,
            view=TicketControl(self.bot, ticket)
        )


class Comfirmation(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.comfirmed = None

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.comfirmed = True
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button, ):
        self.comfirmed = False
        self.stop()


class TicketControl(discord.ui.View):
    def __init__(self, bot: TicketBot, channel: discord.TextChannel):
        super().__init__(timeout=None)
        self.bot = bot
        self.channel = channel

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button, ):
        view = Comfirmation()
        await interaction.response.send_message("Are you sure you want to close this ticket?", view=view, ephemeral=True)
        await view.wait()

        if view.comfirmed:
            print('hi')
            await self.bot.close_ticket(self.channel)
        else:
            await interaction.response.edit_message(content="Cancelled", view=None)
