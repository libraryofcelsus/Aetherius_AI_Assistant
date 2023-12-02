import os
from Aetherius_API.Main import *
import logging
import json
import asyncio

async def chat_with_Aetherius(message, history):
    username = "User"
    bot_name = "Aetherius"
    user_id = "User_Id"
    

    response = await Aetherius_Agent(message, username, user_id, bot_name)


    return response

async def main():
    history = []
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            break
        response = await chat_with_Aetherius(user_input, history)
        history.append({"user": user_input, "bot": response})

if __name__ == "__main__":
    asyncio.run(main())
