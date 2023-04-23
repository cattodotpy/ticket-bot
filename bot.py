import discord
from discord.ext import commands
import dotenv
import os
import logging
from bot_object import TicketBot
from views import TicketCreate, TicketControl


dotenv.load_dotenv()
discord.utils.setup_logging(level=logging.INFO)

TOKEN = os.getenv("TOKEN")


bot = TicketBot(
    "config.json"
)


@bot.command()
async def panel(ctx: commands.Context):
    await ctx.send(
        "Click the button below to create a ticket.",
        view=TicketCreate(bot)
    )



def main():
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
