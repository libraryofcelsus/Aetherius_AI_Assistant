import discord
import sys
import os
import json
import logging
import asyncio
import uuid
import time
from discord.ext import commands
from flask import Flask, request, jsonify
from Aetherius_API.Main import *
from threading import Thread

# Flask app setup
app = Flask(__name__)

def timestamp_func():
    try:
        return time.time()
    except:
        return time()

def split_response(response, limit=1999):
    """Splits the response into chunks that don't exceed the provided limit."""
    if len(response) <= limit:
        return [response]

    chunks = []
    current_chunk = ""
    for sentence in response.split('.'):
        if len(current_chunk) + len(sentence) + 1 > limit:
            chunks.append(current_chunk)
            current_chunk = ""
        current_chunk += sentence + '.'
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

# Function to run asynchronous coroutine
def run_async(coroutine):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # No running loop, create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coroutine)

# Generate a standardized chat completion response
def generate_chat_completion_response(content):
    return {
        "id": str(uuid.uuid4()),
        "object": "chat.completion",
        "created": int(timestamp_func()),  # Changed from int(time())
        "model": "Aetherius",
        "system_fingerprint": "NA",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": content,
            },
            "logprobs": None,
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": len(content.split()),
            "total_tokens":  len(content.split())
        }
    }

# Load settings
with open('API_Settings.json') as config_file:
    settings = json.load(config_file)

# Discord bot setup variables
TOKEN = settings.get('discord_bot_token', '')  # Default to empty string if not found
BOTNAME = settings.get('bot_name', 'Aetherius')
intents = discord.Intents.all()

# Function to check if the Discord token is provided and potentially valid
def is_token_valid(token):
    return token and len(token) > 59  # Basic check for length, Discord tokens are typically longer

# Initialize the Discord bot
client = commands.Bot(command_prefix='!', intents=intents)

logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)

# Discord command to handle !Agent
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

# Event to handle incoming messages
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

# Function to run the Discord bot
def run_discord_bot():
    client.run(TOKEN)

# Flask route to handle chat completions
@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    with open('API_Settings.json') as config_file:
        settings = json.load(config_file)

    data = request.json
    message_content = ''
    message_type = ''
    for message in data.get('messages', []):
        if message.get('role') == 'user':
            message_content = message.get('content', '')
            if message_content.startswith('!Agent'):
                message_type = 'agent'
            else:
                message_type = 'chatbot'

    user_name = settings.get('username', 'USER')
    user_id = settings.get('user_id', 'USER')
    bot_name = settings.get('bot_name', 'Aetherius')

    if message_type == 'agent':
        response_content = run_async(Aetherius_Agent(message_content, user_name, user_id, bot_name))
    else:
        response_content = run_async(Aetherius_Chatbot(message_content, user_name, user_id, bot_name))

    response = generate_chat_completion_response(response_content)
    return jsonify(response)

# Function to run the Flask app
def run_flask_app():
    app.run(use_reloader=False)

# Run the Discord bot and Flask app concurrently
if __name__ == '__main__':
    if is_token_valid(TOKEN):
        discord_thread = Thread(target=run_discord_bot)
        discord_thread.start()
    else:
        print("No valid Discord bot token provided. Running API only.")

    run_flask_app()
