# Aetherius
Version .042b of Aetherius Personal Assistant/Companion by LibraryofCelsus.com

**What is Aetherius?**  Aetherius is an Ai LLM Retrieval Framework focused on bringing realistic long-term memory and thought formation to a customizable chatbot/companion. I am repulsed by the rampant personal consumer data that is sent to companies without thought, the ability to be manipulated increases evermore with the advent of personalized Ai companions.  My goal is to create a local Ai Companion in which you actually have control over and own. One that cannot be changed by an external force to subtly manipulate.  Eventually Aetherius will be 100% private and ran locally, using given files and web-scrapes for a larger knowledge base. Currently it still uses pinecone.io for its Database, as of now I am still struggling to find a good replacement. 

Note: The current Version of Aetherius should be seen as a tech demo to play around with, while it is usable, I constantly make changes to the architecture and updating the scripts may break whatever bot you are talking to.

I also still need to convert Aetherius to work with Pinecone's new free tier, they have recently removed namespaces.  Old Indexes were grandfathered in so previous users can ignore this.

**Local Llama-2 Update**

**Experimental Folder Changelog**

-Added Experimental Version of the file scrape tool using Llama 2

-Added Experimental Version of the webscrape tool using Llama 2

-Llama 2 Version is now mostly functioning as intended, this is the first local model that I have actually felt is capable of running Aetherius.  I am now working on converting the webscrape and file process tools.

-Added Llama v2 chat version using the Oobabooga API.  Tested with TheBloke/Llama-2-13B-chat-GPTQ.  Still needs more work before it will function well with the 7B version.  I load with ExLlama with a max_seq_len of 4096, leaving the other options at 1.

<a href="https://www.buymeacoffee.com/libraryofcelsus" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>

------

[Skip to installation guide](#installation-guide)

[Skip to Changelog](#changelog)

Photo OCR (jpg, jpeg, png) requires tesseract: https://github.com/UB-Mannheim/tesseract/wiki Once installed, copy the "Tesseract-OCR" folder from Program Files to the "Aetherius_Ai_Assistant" Folder.

More output examples can be found at https://github.com/libraryofcelsus/Aetherius_Ai_Assistant_Outputs

Discord Server: https://discord.gg/pb5zcNa7zE

Join the Discord for help or to get more in-depth information!

Made by: https://github.com/libraryofcelsus

Inspired by https://github.com/daveshap/

## Llama 2 Examples

![alt text](http://www.libraryofcelsus.com/wp-content/uploads/2023/07/Aetherius-Example.png)

## Aether Scrape/Search Example

![alt text](http://www.libraryofcelsus.com/wp-content/uploads/2023/07/Aetherscrape-example.jpg)

## Autonomous Architecture

![alt text](http://www.libraryofcelsus.com/wp-content/uploads/2023/05/Aetherius_Reasoning.png)

# Current Version Information
Welcome to the pre-alpha release of Aetherius, a highly customizable AI assistant designed to adapt to your specific needs.  I prefer a more "anthropomorphized" personal Ai as talking to something like base GPT feels off-putting.  The end goal of Aetherius is to both provide a realistic Ai companion and a cognitive framework that can be added on top of other Ai tools.

Currently, Aetherius's main focus is creating a good architecture for realistic long-term memory storage and thought formation. Currently Aetherius has websearch and document scraping abilities.  More features will come at a later date.

Aetherius aims to provide a modular, personalized AI assistant experience by enabling the addition of task-specific Modules and Sub-Modules. If all goes as planned, Aetherius will support integration with other open-source projects and models.

# Changelog:
0.042b

-Local Llama 2 update, works well, but still needs to be improved.

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

-Re-added Users

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

-Convert to a local DB solution instead of Pinecone

-Improve Aetherius's self reflection

-Provide more personality examples

-Detailed guide on how to initially "train" Aetherius to get a desired personality

-Recreate World Creator with new architecture

-NPC submodule for World Creator

-Text-Rpg submodule for World Creator


# Installation Guide

## Installer bat

Run the Installer Bat, it is located at: https://github.com/libraryofcelsus/Aetherius_AI_Assistant/blob/main/scripts/resources/install.bat

![alt text](http://www.libraryofcelsus.com/wp-content/uploads/2023/05/Capture11111111.png)

Copy your OpenAi and Pinecone API keys to api_key folder inside of the created Aetherius_Ai_Assistant folder

If you get an error, you may need to do steps 5, 8, and 9 from the manual installation.

Launch Aetherius with **run.bat**

At pinecone.io, create an index named "Aetherius" with 768 dimensions and "cosine" as the metric.

Upload heuristics to DB and start chatting with Aetherius. Heuristic examples, and files to modify prompts can be found in the config folder!  Prompts can also be edited through the Config Menu.

To run Aetherius Locally using Oobabooga, first install the web-ui at: https://github.com/oobabooga/text-generation-webui

Then, under the "Interface Mode" tab, enable the api checkbox in both fields. Then click apply and restart the interface.

Next, navigate to the models tab. Uncheck the autoload models box and then input "TheBloke/Llama-2-13B-chat-GPTQ" into the downloads box. Other models may work, but this is the one that is tested.

Once the download is completed, reload the model selection menu and then select the model. Change the model loader to Exllama and set the max_seq_len to "4096".

Click the "load" button and load the model. The Oobabooga API bots should now work!

## Windows Installation

**Guide with Photos can be found at [https://www.libraryofcelsus.com/aetherius-setup-guide/]**

**Guide Out of Date**

1. Install Git: **https://git-scm.com/** (Git can be skipped by downloading the repo as a zip file under the green code button)

2. Install Python 3.10.6, Make sure you add it to PATH: **https://www.python.org/downloads/release/python-3106/**

3. Open the program "Git Bash". 

4. Run git clone: **git clone https://github.com/libraryofcelsus/Aetherius_AI_Assistant.git**

5. Open CMD as Admin (Command Panel)

6. Navigate to Project folder: **cd PATH_TO_AETHERIUS_INSTALL**

7. Create a virtual environment: **python -m venv venv**

8. Activate the environment: **.\venv\scripts\activate**   (This must be done before running Aetherius each time, using an IDE like PyCharm can let you skip this. The run.bat will also automatically do this.)

9. Install the required packages: **pip install -r requirements.txt**

10. Copy your OpenAI api key to key_openai.txt

11. Create a Index on pinecone.io titled: "aetherius" with 768 dimensions and cosine as the metric. I usually do a P1 instance. (Use 1536 dimensions for Open Ai embeddings.)

12. Copy Api key for that Index and paste it in key_pinecone.txt

13. Copy the Pinecone Environment and paste it in key_pinecone_env.txt

14. Copy your Google Api key to key_google.txt  (Google Keys only needed if using AetherSearch's websearch.)

15. Copy your Google CSE ID to key_google_cse.txt

17. Run main.py by typing **python main.py** in cmd or **run.bat** as admin to start Aetherius. (Using run.bat will let you skip opening CMD and activating the enviornment.)

18. Select DB Upload Heuristics from the DB Management menu to upload Heuristics for the bot, this DB can also function as a Personality DB. An example of how to do this can be found in "personality_db_input_examples.txt" in the config folder.

21. Edit the chatbot's prompts with the Config Menu. This will let you change the main, secondary, and greeting prompts.  You can also change things like the font style and size.

22. You can change the botname and the username in the login menu.  Changing either of these will create a new chatbot.

23. Once the chatbot has adopted a desired personality, I recommend creating a backup of the "nexus" folder and then create a collection of the "aetherius" index on pinecone.io.  This will let you revert back to a base state if issues arise later.

24. Once you have made a backup, you can start using the "Auto" mode, this mode has Aetherius decide for itself whether or not it should upload to its memories.

25. To run Aetherius Locally using Oobabooga, first install the web-ui at: https://github.com/oobabooga/text-generation-webui

26. Then, under the "Interface Mode" tab, enable the api checkbox in both fields.  Then click apply and restart the interface.

27. Next, navigate to the models tab. Uncheck the autoload models box and then input "TheBloke/Llama-2-13B-chat-GPTQ" into the downloads box. Other models may work, but this is the one that is tested.

28. Once the download is completed, reload the model selection menu and then select the model. Change the model loader to Exllama and set the max_seq_len to "4096".

29. Click the "load" button and load the model.  The Oobabooga API bots should now work!



# Contact
Discord: libraryofcelsus      -> Old Username Style: Celsus#0262

MEGA Chat: https://mega.nz/C!pmNmEIZQ

Email: libraryofcelsusofficial@gmail.com

