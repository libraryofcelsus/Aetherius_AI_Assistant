# Aetherius
Version 0.028 of the Aetherius Personal Assistant by LibraryofCelsus.com
https://github.com/libraryofcelsus

Inspired by https://github.com/daveshap/

![](http://www.libraryofcelsus.com/wp-content/uploads/2023/04/Aetherius-Menu-Gif.gif)

![](http://www.libraryofcelsus.com/wp-content/uploads/2023/04/Aetherius-Example-gif.gif)

# Current Version Information
Welcome to the first pre-alpha release of Aetherius, a highly customizable AI assistant designed to adapt to your specific needs. 

Aetherius aims to provide a modular, personalized AI assistant experience by enabling the addition of task-specific Modules and Sub-Modules. If all goes as planned, Aetherius will support integration with other open-source projects.

## Changelog:
0.028

-Cadence DB Rework, upload cadence from DB management

0.027

-Implemented Cadence DB (More of a test, may be removed due to token useage.)

-Various Bug Fixes

## Future Plans
-Give Aetherius tools like web-search

-Improve Aetherius's self reflection

-Provide more personality examples

-Detailed guide on how to initially "train" Aetherius to get a desired personality

-NPC submodule for World Creator

-Text-Rpg submodule for World Creator

-Generative Q/A Module from own Dataset

# Installation Guide

## Windows Installation

1. Install Git: **https://git-scm.com/**

2. Install Python 3.10.6, Make sure you add it to PATH: **https://www.python.org/downloads/release/python-3106/**

3. Run git clone: **git clone https://github.com/libraryofcelsus/Aetherius_AI_Assistant.git**

4. Open CMD as Admin

5. Navigate to Project folder: **cd PATH**

6. Create a virtual environment: **python -m venv venv**

7. Activate the environment: **.\venv\scripts\activate**

8. Install the required packages: **pip install -r requirements.txt**

9. Copy your OpenAI api key to key_openai

10. Create a Index on pinecone.io titled: "aetherius" with 1536 dimensions and cosine as the metric. I usually do a P1 instance.

11. Copy Api key for that Index and paste it in key_pinecone.txt

12. Edit the .txt files in the "config" folder to customize the bot.

13. Run main.py with **python main.py** to start Aetherius, Select DB Management.

14. Select DB Upload Heuristics to upload secondary Heuristics for the bot, this DB can also function as a Personality DB. An example of how to do this can be found in "personality_db_input_examples.txt" in the config folder.

14. Type "Exit" twice to return to the main menu. Now select "Main Bot"

15. Select one of the "Manual" chatbot modes, this will enable you to choose what gets uploaded to the chatbots memories.  It also enables a summary of Aetherius's inner loop, avoid uploading irrelivant information to the inner loop DB as they tend to take priority over other memories.  Using the Auto mode can cause an undesired personality to emerge from the bot if it doesn't have established memories.

15. Once the chatbots memories have been established, type "Exit" and then select one of the Auto chatbots, this mode will have the bot decide for itself if it should upload to its memory DB.

16. Using the GPT 3.5 scripts causes a significant decrease in intelligence, and as such generally shouldn't be used for training. Auto-Memory may also lead to some issues, chat - manual is recommended if only using GPT 3.5.

# Contact
email@libraryofcelsus.com
