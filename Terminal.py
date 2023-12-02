import os
from Aetherius_API.Main import *
import logging
import json
import asyncio

async def chat_with_Aetherius(message, history, mode, username, user_id):
    bot_name = "Aetherius"

    if mode == "chat_bot":
        response = await Aetherius_Chatbot(message, username, user_id, bot_name)
    else:  # Default to Agent mode
        response = await Aetherius_Agent(message, username, user_id, bot_name)

    return response

async def main():
    history = []
    user_info = input("Enter your username and user ID separated by a space: ")
    username, user_id = user_info.split()

    mode = input("Select mode (chat_bot/Agent): ").lower()
    while mode not in ["chat_bot", "agent"]:
        print("Invalid mode. Please choose 'chat_bot' or 'Agent'.")
        mode = input("Select mode (chat_bot/Agent): ").lower()

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break
        response = await chat_with_Aetherius(user_input, history, mode, username, user_id)
        history.append({"user": user_input, "bot": response})

if __name__ == "__main__":
    asyncio.run(main())
