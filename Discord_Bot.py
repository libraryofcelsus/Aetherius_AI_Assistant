import discord
import os
from discord.ext.commands import Bot
from Aetherius_API.Oobabooga_Import_Async import *
import logging

# Max_Tokens variable for the Response generation should be set to 350 to avoid Length Errors


TOKEN = 'MTE1NzA5NzA5ODA0MzQ2OTkzNw.GIbjLS.yUiDGIzhIyH-kecPQb6psn5XjNzGJh2Rw0FK9w'

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
        if len(chunk) + len(sentence) + 1 > limit:  
            chunks.append(chunk)
            chunk = ""
        chunk += sentence + '.'
    if chunk:
        chunks.append(chunk)
    return chunks

@client.command()
async def Agent(ctx, *, inquiry):
    """Handle the !Agent command"""
    response = await Aetherius_Agent(inquiry, str(ctx.author), BOTNAME)

    for chunk in split_response(response):
        await ctx.send(chunk)
        
@client.command()
async def Heuristics(ctx, *, query):
    """Handle the !Heuristics command"""
    response = await Upload_Heuristics(query, str(ctx.author), BOTNAME)
    for chunk in split_response(response):
        await ctx.send(chunk)

@client.command()
async def ImplicitSTM(ctx, *, query):
    """Handle the !ImplicitSTM command"""
    response = await Upload_Implicit_Short_Term_Memories(query, str(ctx.author), BOTNAME)
    for chunk in split_response(response):
        await ctx.send(chunk)

@client.command()
async def ExplicitSTM(ctx, *, query):
    """Handle the !ExplicitSTM command"""
    response = await Upload_Explicit_Short_Term_Memories(query, str(ctx.author), BOTNAME)
    for chunk in split_response(response):
        await ctx.send(chunk)

@client.command()
async def ImplicitLTM(ctx, *, query):
    """Handle the !ImplicitLTM command"""
    response = await Upload_Implicit_Long_Term_Memories(query, str(ctx.author), BOTNAME)
    for chunk in split_response(response):
        await ctx.send(chunk)

@client.command()
async def ExplicitLTM(ctx, *, query):
    """Handle the !ExplicitLTM command"""
    response = await Upload_Explicit_Long_Term_Memories(query, str(ctx.author), BOTNAME)
    for chunk in split_response(response):
        await ctx.send(chunk)
        
@client.command()
async def WebScrape(ctx, *, query):
    """Handle the !WebScrape command"""
    await async_chunk_text_from_url(query, str(ctx.author), BOTNAME)
    await ctx.send("WebScrape command received and is being processed.")  # Acknowledgment message
        

@client.event
async def on_message(message):
    # Avoid responding to ourselves
    if message.author == client.user:
        return

    # If the bot is not mentioned in a guild, do nothing
    if message.guild is not None and client.user not in message.mentions:
        return
    
    # If the message doesn't start with '!', interact as a chatbot
    if not message.content.startswith('!'):
        response = await Aetherius_Chatbot(message.content, str(message.author), BOTNAME)
        for chunk in split_response(response):
            await message.channel.send(chunk)

    # Let the commands extension handle commands
    await client.process_commands(message)


client.run(TOKEN)