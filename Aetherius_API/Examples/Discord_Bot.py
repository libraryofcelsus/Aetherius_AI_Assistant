import discord
import os
from discord.ext import commands
from Aetherius_API.Oobabooga_Import import Aetherius_Chatbot
import logging
import concurrent.futures
import asyncio

TOKEN = 'REPLACE WITH DISCORD BOT TOKEN'

intents = discord.Intents.all()
client = discord.Client(command_prefix='!', intents=intents)

logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)

def chatbot_response(message):
    return Aetherius_Chatbot(message.content, str(message.author), 'Aetherius')

@client.event
async def on_message(message):
    # Only respond to messages from other users, not from the bot itself
    if message.author == client.user:
        return

    # Execute the chatbot_response function in a separate thread
    with concurrent.futures.ThreadPoolExecutor() as executor:
        response = await asyncio.get_event_loop().run_in_executor(
            executor, chatbot_response, message
        )
    
    # Send the response as a message
    await message.channel.send(response)

# Start the bot
client.run(TOKEN)