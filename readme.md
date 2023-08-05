# Aetherius
Version .043d of the Aetherius Ai Personal Assistant/Agent/Companion by LibraryofCelsus.com

------

**Experimental Changelog**

-Added Experimental Different Instruct formating for Oobabooga api chatbot.  Barley works for now.

-Added Llama 2 Agent script.  This functions similarly to the websearch/file reading chatbot, but instead chooses if it should search external resources for each task.  It also searches both the webscrape and file reading DB's at once.

-Added Qdrant Version of OpenAi Aethersearch.  Still needs work, I prefer the Llama 2 one as of now.

-Added Experimental Version for instruct models, not optimized for any specific model yet.

-Added Qdrant Version of basic OpenAi Chatbot, updated the scripts and they should now follow the conversation track again.  That being said, most development has now moved to the locally ran version.

------

## Aetherius's Current Modules

All modules upload to the main chatbot's memories, so it's knowledgebase will grow on whatever external data you want!

**Main Chatbot:** A chatbot with realistic long term memory to serve as your personal Ai companion!

**External Resource Modules (Aethersearch, File Processor, Agent):** These modules enable Aetherius to connect with external data. Owing to the constraints of smaller models, it is recommended to scrape the Wikipedia page of your desired subject prior to initiating a conversation. The memories created from these tools are shared across all chatbot versions, allowing Aetherius’s knowledge base to expand over time.

**Aethersearch:** This is a websearch/scrape chatbot.

**File Processor:** This is a chatbot that will let you talk with your own files.  It supports a variety of formats including Image OCR.

**Agent:** This is a chatbot that follows the Autonomous Architecture.  As of now its only tools are DB searches.  It will decide if it needs its memories, external resources, or both.  If it needs external resources it will search the web and file scrape DB's from the Aethersearch and File Processor chatbots.

------

Aetherius's development is self-funded, consider supporting me if you use it frequently :)

<a href='https://ko-fi.com/R6R2NRB0S' target='_blank'><img height='36' style='border:0px;height:36px;' src='https://storage.ko-fi.com/cdn/kofi3.png?v=3' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>

------

[Aetherius Usage Guide](https://www.libraryofcelsus.com/research/aetherius-usage-guide/)

[Skip to Aetherius General Information](#current-version-information)

[Skip to installation guide](#installation-guide)

[Skip to Changelog](#changelog)

More output examples can be found at https://github.com/libraryofcelsus/Aetherius_Ai_Assistant_Outputs

------

Discord Server: https://discord.gg/pb5zcNa7zE

Join the Discord for help or to get more in-depth information!

Made by: https://github.com/libraryofcelsus

Inspired by https://github.com/daveshap/

## Llama 2 Examples

![alt text](http://www.libraryofcelsus.com/wp-content/uploads/2023/07/Aetherius-Example.png)

## Aether Scrape/Search Example

![alt text](http://www.libraryofcelsus.com/wp-content/uploads/2023/07/Aetherscrape-example.jpg)

## Autonomous Architecture

![alt text](http://www.libraryofcelsus.com/wp-content/uploads/2023/07/AetheriusArch.png)

# Current Version Information

**What is Aetherius?**  Aetherius is an Ai LLM Retrieval Framework focused on bringing realistic long-term memory and thought formation to a customizable chatbot/companion. 
My goal is to create a locally ran Ai Assistant that you actually have control over and own. One that cannot be changed by an external force without concent.

Currently, Aetherius's main focus is creating a good architecture for realistic long-term memory storage and thought formation. Currently Aetherius has websearch and file reading abilities.  More features will come at a later date.

Aetherius aims to provide a modular, personalized AI assistant experience by enabling the addition of task-specific Modules and Sub-Modules. If all goes as planned, Aetherius will support integration with other open-source projects and models.

Aetherius can now be ran locally and offline maintaining 100% privacy!


# Changelog:
0.043d

-Cleaned up main Llama 2 chatbot code

0.043c

-Reworked Input Window, now handles larger text strings better.

-Updated OpenAi scripts, they should now follow the conversation track better.

-Various Bug Fixes

0.043b

-Added Delete Button to Edit Conversation in Llama 2 Chatbot

-Added Long Term Memory Upload in Llama 2 Chatbot

-Updated Delete Menu in DB Management in Llama 2 Chatbot


0.043a

-Fixed Bug where only one Implicit and Explicit Memory were uploaded

-Improved Memory Prompts, works alot better with the 7B model of Llama 2 now.  Still wouldn't recommend using the 7B model though.

-Improved Auto Memory Upload.

0.043

-Added Qdrant Version.  Aetherius can now be ran 100% locally!

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


## Future Plans

-Create full documentation on Aetherius's Functions

-Usage and Tip Guides for Aetherius

-Improve Aetherius's self reflection

-Provide more personality examples

-Recreate World Creator with new architecture

-NPC submodule for World Creator

-Text-Rpg submodule for World Creator


# Installation Guide

## Installer bat

Run the Installer Bat, it is located at: https://github.com/libraryofcelsus/Aetherius_AI_Assistant/blob/main/scripts/resources/install.bat

![alt text](http://www.libraryofcelsus.com/wp-content/uploads/2023/05/Capture11111111.png)

Copy your OpenAi and Pinecone API keys to api_key folder inside of the created Aetherius_Ai_Assistant folder

If using Qdrant Cloud copy their Api key and Url instead of Pinecone.  Qdrant Cloud: https://qdrant.to/cloud

To use a local Qdrant server, first install Docker: https://www.docker.com/, then see: https://github.com/qdrant/qdrant/blob/master/QUICK_START.md

Once the local Qdrant server is running, it should be auto detected by Aetherius.

If you get an error, you may need to do steps 5, 8, and 9 from the manual installation.

Launch Aetherius with **run.bat**

At pinecone.io, create an index named "Aetherius" with 768 dimensions and "cosine" as the metric.

Photo OCR (jpg, jpeg, png) requires tesseract: https://github.com/UB-Mannheim/tesseract/wiki   
Once installed, copy the "Tesseract-OCR" folder from Program Files to the "Aetherius_Ai_Assistant" Folder.

Upload heuristics to DB and start chatting with Aetherius. Heuristic examples, and files to modify prompts can be found in the config folder!  Prompts can also be edited through the Config Menu.

To run Aetherius Locally using Oobabooga, first install the web-ui at: https://github.com/oobabooga/text-generation-webui

Then, under the "Interface Mode" tab, enable the api checkbox in both fields. Then click apply and restart the interface.

Next, navigate to the models tab. Uncheck the autoload models box and then input "TheBloke/Llama-2-13B-chat-GPTQ" into the downloads box. Other models may work, but this is the one that is tested.

Once the download is completed, reload the model selection menu and then select the model. Change the model loader to Exllama and set the max_seq_len to "4096".

Click the "load" button and load the model. The Oobabooga API bots should now work!

Photo OCR (jpg, jpeg, png) requires tesseract: https://github.com/UB-Mannheim/tesseract/wiki
Once installed, copy the "Tesseract-OCR" folder from Program Files to the "Aetherius_Ai_Assistant" Folder.

[Aetherius Usage Guide](https://www.libraryofcelsus.com/research/aetherius-usage-guide/)

## Windows Installation

**Guide with Photos can be found at [https://www.libraryofcelsus.com/aetherius-setup-guide/]**

**Photo Guide Out of Date**

1. Install Git: **https://git-scm.com/** (Git can be skipped by downloading the repo as a zip file under the green code button)

2. Install Python 3.10.6, Make sure you add it to PATH: **https://www.python.org/downloads/release/python-3106/**

3. Open the program "Git Bash". 

4. Run git clone: **git clone https://github.com/libraryofcelsus/Aetherius_AI_Assistant.git**

5. Open CMD as Admin (Command Panel)

6. Navigate to Project folder: **cd PATH_TO_AETHERIUS_INSTALL**

7. Create a virtual environment: **python -m venv venv**

8. Activate the environment: **.\venv\scripts\activate**   (This must be done before running Aetherius each time. The run.bat will also automatically do this.)

9. Install the required packages: **pip install -r requirements.txt**

10. Copy your OpenAI api key to key_openai.txt (If using Oobabooga, you may skip this.)

    (If using Qdrant skip to step 14.)

11. Create a Index on pinecone.io titled: "aetherius" with 768 dimensions and cosine as the metric. I usually do a P1 instance. (Use 1536 dimensions for Open Ai 
    embeddings.)

12. Copy Api key for that Index and paste it in key_pinecone.txt 

13. Copy the Pinecone Environment and paste it in key_pinecone_env.txt

14. If using Qdrant Cloud copy their Api key and Url instead of Pinecone.  Qdrant Cloud: https://qdrant.to/cloud

15. To use a local Qdrant server, first install Docker: https://www.docker.com/

16. Now follow the steps in Qdrants Quick Start guide: https://github.com/qdrant/qdrant/blob/master/QUICK_START.md

17. Once the local Qdrant server is running, it should be auto detected by Aetherius.

18. Copy your Google Api key to key_google.txt  (Google Keys only needed if using AetherSearch's websearch.)

19. Copy your Google CSE ID to key_google_cse.txt

20. If you plan on using Photo OCR (jpg, jpeg, png Text Recognition), it requires tesseract: https://github.com/UB-Mannheim/tesseract/wiki
    Once installed, copy the "Tesseract-OCR" folder from Program Files to the "Aetherius_Ai_Assistant" Folder.  Photos must be placed in the ./Upload/SCANS folder.

21. Run main.py by typing **python main.py** in cmd or **run.bat** as admin to start Aetherius. (Using run.bat will let you skip opening CMD and activating the 
    enviornment.)

22. Select DB Upload Heuristics from the DB Management menu to upload Heuristics for the bot, this DB can also function as a Personality DB. An example of how to do 
    this can be found in "personality_db_input_examples.txt" in the config folder.

23. Edit the chatbot's prompts with the Config Menu. This will let you change the main, secondary, and greeting prompts.  You can also change things like the font style 
    and size.

24. You can change the botname and the username in the login menu.  Changing either of these will create a new chatbot.

25. Once the chatbot has adopted a desired personality, I recommend creating a backup of the "nexus" folder and then create a collection of the "aetherius" index on 
    pinecone.io.  This will let you revert back to a base state if issues arise later.

26. Once you have made a backup, you can start using the "Auto" mode, this mode has Aetherius decide for itself whether or not it should upload to its memories.

27. To run Aetherius Locally using Oobabooga, first install the web-ui at: https://github.com/oobabooga/text-generation-webui

28. Then, under the "Interface Mode" tab, enable the api checkbox in both fields.  Then click apply and restart the interface.

29. Next, navigate to the models tab. Uncheck the autoload models box and then input "TheBloke/Llama-2-13B-chat-GPTQ" into the downloads box. Other models may work, but 
    this is the one that is tested.

30. Once the download is completed, reload the model selection menu and then select the model. Change the model loader to Exllama and set the max_seq_len to "4096".

31. Click the "load" button and load the model.  The Oobabooga API bots should now work!

[Aetherius Usage Guide](https://www.libraryofcelsus.com/research/aetherius-usage-guide/)

# Contact
Discord: libraryofcelsus      -> Old Username Style: Celsus#0262

MEGA Chat: https://mega.nz/C!pmNmEIZQ

Email: libraryofcelsusofficial@gmail.com

