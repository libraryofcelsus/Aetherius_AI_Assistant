import os
from Aetherius_API.Main import *
import logging
import gradio as gr
import json
import asyncio



async def chat_with_Aetherius(message, history):
    username = "USER"
    bot_name = "Aetherius"
    user_id = username
    
    # Change Function to either "Aetherius_Chatbot" or "Aetherius_Agent"
    response = await Aetherius_Chatbot(message, username, user_id, bot_name)

    return response

# Create the ChatInterface
demo = gr.ChatInterface(
    fn=chat_with_Aetherius, 
    title="Aetherius Chatbot",
    description="Welcome to Aetherius Chatbot! Enter your message and get a response."
)

demo.launch()
