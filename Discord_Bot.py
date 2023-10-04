import discord
import os
from discord.ext.commands import Bot
from Aetherius_API.Oobabooga_Import_Async import Aetherius_Chatbot
import logging


TOKEN = 'REPLACE WITH BOT TOKEN'

intents = discord.Intents.all()
client = Bot(command_prefix='!', intents=intents)


logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)

@client.event
async def on_message(message):
    # Only respond to messages from other users, not from the bot itself
    if message.author == client.user:
        return
    # Respond only if the bot is mentioned
    if client.user in message.mentions:
        # Use the Aetherius_Chatbot function to generate a response to the message
        response = await Aetherius_Chatbot(message.content, str(message.author), 'Aetherius')
        
        # Send the response as a message
        await message.channel.send(response)

    # If you're using discord.ext.commands, this is essential to process commands
    await client.process_commands(message)

# Start the bot
client.run(TOKEN)