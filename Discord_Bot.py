import discord
import os
from discord.ext.commands import Bot
from Aetherius_API.Main import *
import logging

# All Indents must be enabled, give the bot admin privileges

# COMMANDS

# !Agent <ENTER QUERY TO BOT> 
# (Activates Aetherius's Sub-Agent Mode)

# !Heuristics <ENTER HEURISTIC>
# (Allows you to upload a Heuristic)

# !ImplicitSTM <ENTER SHORT TERM MEMORY>
# (Allows you to upload a Short Term Implicit Memory)

# !ExplicitSTM <ENTER SHORT TERM MEMORY>
# (Allows you to upload a Short Term Explicit Memory)

# !ImplicitLTM <ENTER LONG TERM MEMORY>
# (Allows you to upload a Long Term Implicit Memory)

# !ExplicitLTM <ENTER LONG TERM MEMORY>
# (Allows you to upload a Long Term Explicit Memory)

TOKEN = 'REPLACE WITH DISCORD BOT TOKEN'

# All Indents must be enabled in discord dev menu, give the bot admin privileges
# When in a server, you must @ the bot.  I recommend just DMing it.

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
    image_path  = None
    if ctx.message.attachments:
        # Get the URL of the first attachment (assuming it's an image)
        image_path = ctx.message.attachments[0].url
    response = await Aetherius_Agent(inquiry, str(ctx.author.display_name), str(ctx.author), BOTNAME, image_path)

    for chunk in split_response(response):
        await ctx.send(chunk)
        
@client.command()
async def Heuristics(ctx, *, query):
    """Handle the !Heuristics command"""
    response = await Upload_Heuristics(query, str(ctx.author.display_name), str(ctx.author), BOTNAME)
    for chunk in split_response(response):
        await ctx.send(chunk)

@client.command()
async def ImplicitSTM(ctx, *, query):
    """Handle the !ImplicitSTM command"""
    response = await Upload_Implicit_Short_Term_Memories(query, str(ctx.author.display_name), str(ctx.author), BOTNAME)
    for chunk in split_response(response):
        await ctx.send(chunk)

@client.command()
async def ExplicitSTM(ctx, *, query):
    """Handle the !ExplicitSTM command"""
    response = await Upload_Explicit_Short_Term_Memories(query, str(ctx.author.display_name), str(ctx.author), BOTNAME)
    for chunk in split_response(response):
        await ctx.send(chunk)

@client.command()
async def ImplicitLTM(ctx, *, query):
    """Handle the !ImplicitLTM command"""
    response = await Upload_Implicit_Long_Term_Memories(query, str(ctx.author.display_name), str(ctx.author), BOTNAME)
    for chunk in split_response(response):
        await ctx.send(chunk)

@client.command()
async def ExplicitLTM(ctx, *, query):
    """Handle the !ExplicitLTM command"""
    response = await Upload_Explicit_Long_Term_Memories(query, str(ctx.author.display_name), str(ctx.author), BOTNAME)
    for chunk in split_response(response):
        await ctx.send(chunk)
        
@client.command()
async def WebScrape(ctx, *, query):
    """Handle the !WebScrape command"""
    await async_chunk_text_from_url(query, str(ctx.author.display_name), str(ctx.author), BOTNAME)
    await ctx.send("WebScrape command received and is being processed.")  # Acknowledgment message
        

@client.event
async def on_message(message):
    image_path = None
    # Avoid responding to ourselves
    if message.author == client.user:
        return

    # If the bot is not mentioned in a guild, do nothing
    if message.guild is not None and client.user not in message.mentions:
        return
        
    if message.attachments:
        # Get the URL of the first attachment (assuming it's an image)
        image_path = message.attachments[0].url
    
    # If the message doesn't start with '!', interact as a chatbot
    if not message.content.startswith('!'):
        response = await Aetherius_Chatbot(message.content, str(message.author.display_name), str(message.author), BOTNAME, image_path)
        for chunk in split_response(response):
            await message.channel.send(chunk)

    # Let the commands extension handle commands
    await client.process_commands(message)


client.run(TOKEN)