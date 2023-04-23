import discord
from discord.ext import commands
import os
# import regex
import logging
from database import JsonDatabase#, MongoDatabase
import json
import time
import dotenv

dotenv.load_dotenv()

PREFIX = os.getenv("PREFIX")
MONGO_URI = os.getenv("MONGO_URI")

class TicketBot(commands.Bot):
    def __init__(self, config_file: os.path):
        # can edit intents, but for now, all.
        super().__init__(command_prefix=PREFIX, intents=discord.Intents.all())
        self.config_file = config_file
        self.config = self.load_config()
        self.logger = logging.getLogger(__file__)
        self.logger.warning("No MONGO_URI found, using JSON database")
        self.database = None


    def load_config(self):
        with open(self.config_file, "r") as f:
            config = json.load(f)

        assert "ticket_category" in config, "'ticket_category' is not in config"
        assert "closed" in config.get(
            "ticket_category"), "'closed' is not in ticket_category"
        assert "opening" in config.get(
            "ticket_category"), "'open' is not in ticket_category"
        assert "manager_role" in config, "'manager_role' is not in config"
        print(config)
        return config

    async def on_ready(self):
        self.logger.info(
            f"Logged in as {self.user.name}#{self.user.discriminator}")
        self.logger.info(f"ID: {self.user.id}")
        self.logger.info(f"Prefix: {PREFIX}")
        self.logger.info(f"Total guilds: {len(self.guilds)}")
        async with JsonDatabase("database.json") as db:
            self.database = db

    async def create_ticket(self, guild: discord.Guild, user: discord.Member) -> discord.TextChannel:
        self.logger.info(f"Creating ticket for {user.name}#{user.discriminator} ({user.id}) in {guild.name} ({guild.id})")
        category = await guild.fetch_channel(self.config.get("ticket_category").get("opening"))
        role = discord.utils.get(guild.roles, id=self.config.get("manager_role"))

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        if role:
            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        channel = await guild.create_text_channel(f"ticket-{user.name}", category=category, overwrites=overwrites)
        await self.database.set(key=str(channel.id), value={"user": str(user.id), "guild": str(guild.id), "created_at": time.time(), "closed": False, "closed_at": None, "messages": []})
        self.logger.info(
            f"Created {channel.name} ({channel.id}) in {guild.name} ({guild.id}) for {user.name}#{user.discriminator} ({user.id})"
        )
        return channel

    async def close_ticket(self, channel: discord.TextChannel):
        self.logger.info(f"Closing ticket {channel.name} ({channel.id}) in {channel.guild.name} ({channel.guild.id})")
        category = await channel.guild.fetch_channel(self.config.get("ticket_category").get("closed"))
        await channel.edit(category=category, sync_permissions=True, name=f"closed-{channel.name[6:]}")

        ticket = await self.database.get(key=str(channel.id))
        ticket["closed"] = True
        ticket["closed_at"]: time.time()
        self.logger.info(f"Fetching ticket messages for {channel.name} ({channel.id}) in {channel.guild.name} ({channel.guild.id})")
        messages = [message async for message in channel.history(limit=None)]
        
        ticket["messages"] = [{"author": str(message.author), "content": message.clean_content} for message in messages]

        self.logger.info("Updating ticket in database")
        return await self.database.set(key=str(channel.id), value=ticket)
    
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.channel.category.id == self.config.get("ticket_category").get("opening"):
            await message.delete()
            await message.channel.send("Please do not send messages here, this is a ticket channel. If you want to close the ticket, use the `close` command.")

        await self.process_commands(message)
    