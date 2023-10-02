import discord
import os
from discord.ext.commands import Bot
from Aetherius_API.Oobabooga_Import_Async import *
import logging

# Max_Tokens variable for the Response generation should be set to 350 to avoid Length Errors


TOKEN = 'REPLACE WITH DISCORD BOT TOKEN'

BOTNAME = 'Aetherius'

intents = discord.Intents.all()
client = Bot(command_prefix='!', intents=intents)

logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)

def split_response(response, limit=1999):
    """Splits the response into chunks that don't exceed the provided limit."""
    if len(response) <= limit:
        return [response]
    
    sentences = response.split('.')
    chunks, chunk = [], ""
    
    for sentence in sentences:
        # Check if adding the next sentence will exceed the limit
        if len(chunk) + len(sentence) + 1 > limit:  # +1 accounts for the period
            chunks.append(chunk)
            chunk = ""
        chunk += sentence + '.'
    if chunk:
        chunks.append(chunk)
    return chunks

@client.command()
async def Agent(ctx, *, inquiry):
    """Handle the !Agent command"""
    # Use the Aetherius_Chatbot function to generate a response to the inquiry
    response = await Aetherius_Agent(inquiry, str(ctx.author), BOTNAME)
    
    # Split and send the response
    for chunk in split_response(response):
        await ctx.send(chunk)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.guild is not None:
        if client.user not in message.mentions:
            return

    # Check if the message starts with the command prefix, if it does, skip the default response handling
    if not message.content.startswith('!'):
        response = await Aetherius_Chatbot(message.content, str(message.author), BOTNAME)
        for chunk in split_response(response):
            await message.channel.send(chunk)

    # Process commands (essential for command handling using discord.ext.commands)
    await client.process_commands(message)

client.run(TOKEN)