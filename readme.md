# Aetherius
Version .042a of Aetherius Personal Assistant by LibraryofCelsus.com

**GUI Update!**

**Experimental Folder Changelog**

N/A

------

[Skip to installation guide](#installation-guide)

[Skip to Changelog](#changelog)

Photo OCR (jpg, jpeg, png) requires tesseract: https://github.com/UB-Mannheim/tesseract/wiki Once installed, copy the "Tesseract-OCR" folder from Program Files to the "Aetherius_Ai_Assistant" Folder.

More output examples can be found at https://github.com/libraryofcelsus/Aetherius_Ai_Assistant_Outputs

Latest Untested Version/Best Script for Code Viewing can be found at /scripts/resources/Base_Aetherius_Script_For_Analysis.py (This version has undergone very little testing and will most likely have bugs. Copy the script to the OpenAi_General_Chatbot folder to use.)

Discord Server: https://discord.gg/pb5zcNa7zE

Join the Discord for help or to get more in-depth information!

Made by: https://github.com/libraryofcelsus

Inspired by https://github.com/daveshap/

![alt text](http://www.libraryofcelsus.com/wp-content/uploads/2023/06/Aetherius-Example-1.png)

## Aether Scrape/Search

![alt text](http://www.libraryofcelsus.com/wp-content/uploads/2023/06/Aetherius-Example-2.png)

![alt text](http://www.libraryofcelsus.com/wp-content/uploads/2023/06/Aetherius-Example-3.png)

## Autonomous Architecture

![alt text](http://www.libraryofcelsus.com/wp-content/uploads/2023/05/Aetherius_Reasoning.png)

# Current Version Information
Welcome to the pre-alpha release of Aetherius, a highly customizable AI assistant designed to adapt to your specific needs.  I prefer a more "anthropomorphized" personal Ai as talking to something like base GPT feels off-putting.  The end goal of Aetherius is to both provide a realistic Ai companion and a cognitive framework that can be added on top of other Ai tools.

Currently, Aetherius's main focus is creating a good architecture for realistic long-term memory storage and thought formation. Currently Aetherius has websearch and document scraping abilities.  More features will come at a later date.

Aetherius aims to provide a modular, personalized AI assistant experience by enabling the addition of task-specific Modules and Sub-Modules. If all goes as planned, Aetherius will support integration with other open-source projects and models.

# Changelog:
0.042a

-Added Webscrape Delete Button

-Small Webscrape prompt rework

-Various Bug Fixes


0.042

-Added GUI for Aetherius.  Very basic for now.

-Added Edit Conversation

-Added Model Selection

-Added GPT 3.5 Turbo 16k

0.041

-Reworked Conversation History, it will now persist past shutdown.

-Added .TXT, .PDF, and .EPUB text extractors. For now it just functions similarly to the webscrape. Place file in the "Upload" folder in its extension's respective folder.  Then run "GPT_4_Text_Extractor.py" to extract all of the files, they will be moved to the "Finished" folder once done.

-Added Photo OCR to the Text Extractor.  To use, place the desired photo in the /Upload/SCANS folder.  Using this feature requires tesseract: https://github.com/UB-Mannheim/tesseract/wiki    Once installed, copy the "Tesseract-OCR" folder from Program Files to the "Aetherius_Ai_Assistant" Folder.  This will allow you to take Screenshots with the windows snipping tool and upload them to Aetherius for processing.

0.04b

-Readded Users

-Various Bug Fixes

-Intuition Prompt Rework

0.04a

-Switched to Username based DB to Bot Name based DB, will add user's again later.

-Various Bug Fixes

0.04

-New User System Implemented.  Change the username prompt in the config folder to change users.  This will allow you to have multiple versions of Aetherius on the same index.

-First iteration of Aether Search/Scrape implemented. This will be the eventual websearch system.  As of now it requires a Google CSE key and Google API key, other options coming soon.

-Autonomous Tasklist Generation

-Aetherius now decides for itself whether or not each task in its generated tasklist requires a websearch, memory search, or both.

0.039

-Added Cadence DB check, will no longer use Cadence prompt if Cadence DB is empty.

-Fixed GPT 3.5 Context Length Bug

-Worked on improving Auto-Memory

-Implemented Auto Explicit Memory Association/Pruning

-Reworked Auto-Memory code

-Various Bug Fixes

0.038

-Worked on Intuition

-Reworded internal prompts to hopefully fix wrong username bug when using gpt 3.5

-Added loop to skip uploading empty lines in memory upsert.

-Added Flashbulb Memory

-Improved summary prompts

-Implemented Implicit Short-Term Memory

-Implemented Implicit Memory Consolidation

-Implemented Implicit Memory Association/Pruning

0.037

-Added Reset_Pinecone_Index.py to DB Management. This will allow you to reset Aetherius without having to log into pinecone.io

-Added "Clear Memory" command to main chatbot. This will clear the saved short-term memory.

-Worked on Improving Memory Auto Upload|

-Cleaned up Code and added an Analysis file in the resources folder

-Fixed TTS Bug

-Added Manual Long-Term memory Consolidation script in DB Management

0.036

-Implemented Memory Consolidation

-Added Retry loop for Auto Memory

-Fixed Intuition Loop context length bug

-Various Bug Fixes

0.035

-Separated General Memory DB into Implicit and Explicit Memories.

-Various Bug Fixes

0.034

-Added Voice Assistant Script, only on keypress for now. Always listening will come later.

-Auto Memory Upload bug fix

## Future Plans
-Give Aetherius tools like web-search

-Improve Aetherius's self reflection

-Provide more personality examples

-Detailed guide on how to initially "train" Aetherius to get a desired personality

-Recreate World Creator with new architecture

-NPC submodule for World Creator

-Text-Rpg submodule for World Creator

-Generative Q/A Module from own Dataset

# Installation Guide

## Installer bat

https://github.com/libraryofcelsus/Aetherius_AI_Assistant/blob/main/scripts/resources/install.bat

![alt text](http://www.libraryofcelsus.com/wp-content/uploads/2023/05/Capture11111111.png)

Copy your OpenAi and Pinecone API keys to api_key folder inside of the created Aetherius_Ai_Assistant folder

Launch Aetherius with **run.bat**

Select DB Management and select Reset Pinecone Index to create an index.

Upload heuristics to DB and start chatting with Aetheius, bot name, heuristic examples, and files to modify prompts can be found in the config folder!

## Windows Installation

**Guide with Photos can be found at [https://www.libraryofcelsus.com/aetherius-setup-guide/]**

**Guide Out of Date**

1. Install Git: **https://git-scm.com/** (Git can be skipped by downloading the repo as a zip file under the green code button)

2. Install Python 3.10.6, Make sure you add it to PATH: **https://www.python.org/downloads/release/python-3106/**

3. Open the program "Git Bash". 

4. Run git clone: **git clone https://github.com/libraryofcelsus/Aetherius_AI_Assistant.git**

5. Open CMD as Admin

6. Navigate to Project folder: **cd PATH_TO_AETHERIUS_INSTALL**

7. Create a virtual environment: **python -m venv venv**

8. Activate the environment: **.\venv\scripts\activate**   (This must be done before running Aetherius each time, using an IDE like PyCharm can let you skip this.)

9. Install the required packages: **pip install -r requirements.txt**

10. Copy your OpenAI api key to key_openai.txt

11. Create a Index on pinecone.io titled: "aetherius" with 1536 dimensions and cosine as the metric. I usually do a P1 instance.

12. Copy Api key for that Index and paste it in key_pinecone.txt

13. Copy the Pinecone Enviornment and paste it in key_pinecone_env.txt

14. Copy your Google Api key to key_google.txt

15. Copy your Google CSE ID to key_google_cse.txt

16. Edit the .txt files in the "config" folder to customize the bot.

17. Run main.py with **python main.py** to start Aetherius, Select DB Management.

18. Select DB Upload Heuristics to upload secondary Heuristics for the bot, this DB can also function as a Personality DB. An example of how to do this can be found in "personality_db_input_examples.txt" in the config folder.

19. Upload your desired Cadence to "DB Upload Cadence" in DB Management. This should be a direct example of the speech style, not a description. I suggest asking Aetherius to use the diction of a "____" to generate an example, then copy paste the response to the Cadence Upload.

20. Type "Exit" to return to the main menu. Now select "OpenAi_General_Chatbot"

21. Select one of the "Training" chatbot modes, this will enable you to choose what gets uploaded to the chatbots memories.  It also functions as a "Manual" mode. (Previous Manual mode has been removed)

22. Once the chatbot has adopted a desired personality, I recommend creating a backup of the "nexus" folder and then create a collection of the "aetherius" index on pinecone.io.  This will let you revert back to a base state if issues arise later.

23. Once you have made a backup, you can start using the "Auto" mode, this mode has Aetherius decide for itself whether or not it should upload to its memories.

24. Type "Clear Memories" to clear short term memory. Type "Exit" to exit without saving the current conversation to episodic memory. Type "Save and Exit" to summarize the current conversation and upload it to episodic memories.

25. To reset Aetherius completely, enter DB Management and select "Reset Pinecone Index". Type "Reset Index" to delete and remake the index.  This takes a little bit so wait at least 1 minuite before attempting to access it.

26. Using the GPT 3.5 scripts causes a significant decrease in intelligence, and as such generally shouldn't be used for initial training.

# Contact
Discord: libraryofcelsus      -> Old Username Style: Celsus#0262

MEGA Chat: https://mega.nz/C!pmNmEIZQ

Email: libraryofcelsusofficial@gmail.com

