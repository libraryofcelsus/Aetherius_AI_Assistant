import discord
import os
from discord.ext import commands
from Aetherius_API.Oobabooga_Import import Aetherius_Chatbot
import logging

# To use this script, move it to the main Aetherius Root Folder

TOKEN = 'ENTER DISCORD BOT TOKEN HERE'

intents = discord.Intents.all()
client = discord.Client(command_prefix='!', intents=intents)

logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)

@client.event
async def on_message(message):
    # Only respond to messages from other users, not from the bot itself
    if message.author == client.user:
        return

    # Use the Aetherius_Chatbot function to generate a response to the message
    response = Aetherius_Chatbot(message.content, str(message.author), 'Aetherius')
    
    # Send the response as a message
    await message.channel.send(response)

# Start the bot
client.run(TOKEN)