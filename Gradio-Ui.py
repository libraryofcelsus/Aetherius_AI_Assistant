import os
from Aetherius_API.Oobabooga_Import_Async import *
import logging
import gradio as gr
import json
import asyncio



async def chat_with_Aetherius(message, history):
    user_id = "libraryofcelsus"
    bot_name = "Aetheria"
    username = "Celsus"
    

    response = await Aetherius_Chatbot(message, username, user_id, bot_name)

    return response

# Create the ChatInterface
demo = gr.ChatInterface(
    fn=chat_with_Aetherius, 
    title="Aetherius Chatbot",
    description="Welcome to Aetherius Chatbot! Enter your message and get a response."
)

demo.launch()
