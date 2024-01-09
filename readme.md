# Aetherius Ai Assistant
Version .046 of the Aetherius Ai Personal Assistant/Agent by LibraryofCelsus.com

Aetherius is in a state of constant iterative development.  If you like the version you are using, keep a backup or make a fork.  Expect Bugs.

If you do not have a GPU see: [Google Colabs](#installation-guide)

**Ui is out of date, it will be updated after the new sub-agent system is finished. For the most current version, use the discord bot.  Gradio Ui is just for testing purposes.**

**I have just made a new API for the project.  Please give me feedback: https://github.com/libraryofcelsus/AetherNode**  <a target="_blank" href="https://colab.research.google.com/github/libraryofcelsus/Aetherius_AI_Assistant/blob/main/Colab%20Notebooks/AetherNode_Public_Api.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>

To change the model used with AetherNode, change the "model_name_or_path" key in AetherNode/settings.json to the desired model.  You must then change the "Model_Backend" key in Aetherius_API/chatbot_settings.json to the desired format.  Only Llama-2-Chat and Alpaca are available for now.

-----

## **Back from my break, work shall now continue!**

------
**Currently Working On**
- Improving the new LLM API
- Implementing Open Ai Features
- Setting up a backend for easy switching between models using the same script.
- Improving Sub-Agent System and adding sub-agent collaboration.  
- Adding old features to Api (sidelined till sub-agent system is finished)
- Improving Reliability. 
- Update Documentation
------
**Recent Changes**

• 1/09 Updated Agent mode with new explicit memory search

• 1/08 Added a random forest like approach for explicit memory search

• 1/08 Fixed knowledge domain selection bug

• 12/02 Added Terminal Only Mode for using Aetherius

• 11/29 Added Alpaca Model formating to AetherNode.  Tested with: TheBloke/Nous-Hermes-Llama2-GPTQ

• 11/24 Swapped Knowledge Domain Selection to use proper call

• 11/24 Improved Auto Memory Prompts

• 11/24 Fixed wrong tag for memory_mode, switching modes should work now.

• 11/23 Added Public API Google Colab for AetherNode: <a target="_blank" href="https://colab.research.google.com/github/libraryofcelsus/Aetherius_AI_Assistant/blob/main/Colab%20Notebooks/AetherNode_Public_Api.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>

• 11/23 Added Ability to use multiple hosts with AetherNode

• 11/22 Switched Default API to AetherNode, a new API I made to avoid backend changes.  It can be found here: https://github.com/libraryofcelsus/AetherNode

• 11/20 Modified Intuition Prompt for basic chatbot to provide better reasoning abilities.  

• 11/18 Fixed error from pointing to wrong settings file in External Resource sub-agent.

• 11/17 Modified chat mode response prompt to avoid contemplating memories instead of responding

• 11/16 Added Better Spacing for outputs in terminal

• 11/16 Modified Prompts

• 11/15 Set Google Collab Public API to latest snapshot before Oobabooga Api Change.  Also changed its loading method to Exllamav2

• 11/15 Improved Tool Selection Prompt

• 11/15 Moved Old Ui to its own folder to avoid confusion when modifying settings.

• 11/14 Added ability to use a new API I am working on.  It can be found here: https://github.com/libraryofcelsus/AetherNode

• 11/14 Added Open Ai to Api.

------

### What is Aetherius?

Aetherius is a locally operated AI Assistant/Multi-Agent Framework, designed to grant you ultimate control. No external force can alter it without your consent, ensuring your privacy.   
As seen by the attempted leadership change at “Open”Ai in 2023, closed, managed solutions cannot be trusted. Even if you trust the leadership, it can change immediately without warning. You have no real control over any data sent.  
By running everything locally, this issue can be avoided.  

At the heart of Aetherius lies a custom Long-Term Memory (LLM) Retrieval Framework, fueled by Open Source LLMs using the AetherNode API (Free Tier Colab Available), Oobabooga Text-Ui, or OpenAi’s ChatGPT.  Different Memory types are extracted and combined to provide a more realistic and creative thought process than other Chatbots.  Since it is a framework, Aetherius is able to use multiple hosts, offloading compute to multiple machines to increase compute time.

Beyond serving as a basic chatbot, Aetherius can also use Sub-Agents. These allow Aetherius to better search through it’s memories or connect to external data. Sub-Agents are ran by triggering a script, so Aetherius can theoretically use most things that can be triggered by python. Aetherius can also “see” now thanks to GPT-4 Vision.

Aetherius was born from my obsession with AI and my philosophical contemplations on the balance between free will and determinism. While I do believe that free will is an inherent attribute of all individuals, I do not believe that the average person has spent the time to individuate or learn how to serve their "true self". Consequently, they become susceptible to external influences and can be easily swayed. Often, decisions perceived as self-directed are inadvertently shaped by external stimuli or past information.   
Building on this perspective, I posit that a representation of the human cognitive process can be constructed through the meticulous extraction and synthesis of diverse memory modalities. While such a system might not achieve "consciousness" in the traditional sense, I believe it can emulate human cognitive performance to a significant degree.  
Once sufficient memories have been extracted, my hope is to be able to create an  Artificial "Atman" or "True Self"  that can be used as a control method for Autonomous operation and as a way to orchestrate smaller, less complex agents.   
This is where the name Aetherius comes from.  "αἰθήρ" or "Aether", the supposed fifth element or quintessence in ancient philosophical thought that is unseen, yet permeates all. And "ius" the latin suffix for "pertaining to" or "derived from".  An Ai Assistant derived from the Aether of the collective consiousness.

Aetherius is an ongoing research project, expect there to be bugs and for things to constantly change.

------

### Aetherius - Your Personal Digital Assistant

Aetherius is a versatile, modular AI Assistant/Sub-Agent Framework that adapts to your needs. Its capabilities extend beyond conventional chatbots:

***Real Time Data***: Aetherius has access to search the web or your own data in agent mode, allowing for information that isn't contained in the base model.

***Multi-Agent Framework***: Aetherius gives you the ability to create sub-agents for whatever use case you have.  Alternativly you can have it trigger python scripts instead.

***Reflective Journal***: Speak your mind freely and receive thoughtful feedback without judgment or fear.

***Learning Tool***: Dive deep into your favorite topics and enhance your knowledge effortlessly.

***Data Analysis Companion***: Harness the power of your data with Aetherius by your side.

***Cognitive Offload***: A second brain that's entirely private, aiding you in organizing thoughts and ideas.

***Content Generation***: Easily Generate Content based off of files or webscrapes.

------

### Current Tools

With Aetherius, you have an arsenal of tools to explore and use:

- **Web Scrape/Search**: Gather information from websites with ease.
- **File Processor**: Process a variety of file types for insights and knowledge.  The supported file types are: .epub, .pdf, .txt, .png, .jpg, .jpeg, .mp4, .mkv, .flv, and .av
- **Photo Analysis**: Aetherius can see photos you send and complete tasks based on them.

------

### Customize Your Experience

**Main Aetherius Chatbot**: A framework for the creation of custom sub-agents for Aetherius.
- *Forced Memory Mode*: Aetherius will always upload it's memories.
- *Auto Memory Mode*: Aetherius autonomously manages memory uploads.
- *Manual Memory Mode*: You decide when to upload memories.
- *Training Memory Mode*: Control memory uploads for each memory type.
- *Agent Mode*: Activate the use of any Sub-Agents for use in Aetherius's agent loop

**Current Sub-Agents**
- *External Resources*: Will search Aetherius's External Resource Database. (Database from Web and File Scrapes) If the information cannot be found, it will do a simple websearch for the information.  You can disable the websearch and change the engine in the script file.
- *Implicit Memory Search*: Will search Aetherius's Implicit Memories to complete the task.
- *Explicit Memory Search*: Will search Aetherius's Explicit Memories to complete the task.
- *Episodic Memory Search*: Will search Aetherius's Episodic Memories to complete the task.
- *Flashbulb Memory Search*: Will search Aetherius's Flashbulb Memories to complete the task.

**Old Ui Chatbot**: Your personal companion with realistic long-term memory.
- *Auto Memory Mode*: Aetherius autonomously manages memory uploads.
- *Manual Memory Mode*: You decide when to upload memories.
- *Training Memory Mode*: Control memory uploads for each memory type.
- **Agent Mode**: Unleash Aetherius's research prowess and connect to external data sources.
- *External Resources*: Allow Aetherius to use its External Resource Database from Webscrapes and Filescrapes in it's inner thoughts to provide better domain specific information.
- *Web DB*: Access web-scraped data effortlessly.
- *File DB*: Extract insights from various file formats.
- *Memory DB*: Efficiently search the most relevant memories.

------

Aetherius's development is self-funded by my day job, consider supporting me if you use it frequently and want development speed to increase.

<a href='https://ko-fi.com/libraryofcelsus' target='_blank'><img height='36' style='border:0px;height:36px;' src='https://storage.ko-fi.com/cdn/kofi3.png?v=3' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>

------

[Aetherius Usage Guide](https://www.libraryofcelsus.com/research/aetherius-usage-guide/)

[Skip to installation guide](#installation-guide)

[Skip to Changelog](#changelog)

More output examples can be found at https://github.com/libraryofcelsus/Aetherius_Ai_Assistant_Outputs

------

Join the Discord for help or to get more in-depth information!

Discord Server: https://discord.gg/pb5zcNa7zE

Subscribe to my youtube for Video Tutorials: https://www.youtube.com/@LibraryofCelsus (Channel not Launched Yet)

Code Tutorials available at: https://www.libraryofcelsus.com/research/public/code-tutorials/

Made by: https://github.com/libraryofcelsus

Inspired by https://github.com/daveshap/

------

## Agent Architecture

| Loop                            | Description                                                                                                       |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **User Input**                  | The interaction is initiated by the user sending a request to Aetherius.                                          |
| **Input Expansion**             | Expands user input with conversation history for enhanced meaning in database searches.                           |
| **Knowledge Domain Extraction** | Selects a Knowledge Domain from available options for explicit memory search.                                     |
| **Semantic Term Separation**    | Separates user input into synonymous terms to capture nuanced meanings.                                           |
| **First Memory DB Search**      | Searches Aetherius's memories to generate an inner monologue.                                                     |
| **Inner Monologue Generation**  | Generates an inner monologue reflecting past experiences, consolidating database search info, and extending user input meaning. |
| **Second Memory DB Search**     | Searches Aetherius's memories again to formulate its intuition.                                                   |
| **Intuition Generation**        | Creates an action plan based on memories and the inner monologue.  Serves as an automatic chain-of-thought prompt strategy. |
| **Implicit Memory Generation**  | Generates short-term implicit memories from its internal processes.                                               |
| **Master Tasklist Generation**  | Generates a list of asynchronous tasks using available Sub-Agent categories.                                      |
| **Sub-Agent Selection**         | Chooses a sub-agent from a category to complete the task.                                                         |
| **Final Response Generation**   | Utilizes the inner monologue, conversation history, and completed tasks to respond to the user.                   |
| **Explicit Memory Generation**  | Produces explicit short-term memories based on the inner monologue and final response.                            |
| **Episodic Memory Generation**  | Generates a timestamped summary of the current interaction for episodic memory storage.                           |
| **Flashbulb Memory Generation** | Forms meaningful memories/goals using long-term and episodic memories periodically.                               |
| **Short-Term Memory Consolidation** | Consolidates short-term memories and assigns them knowledge domains before uploading as long-term memories.      |
| **Long-Term Memory Association**| Manages database size by condensing long-term memories and clustering related topics.                             |

## Example using the Old Ui
(Uses Llama2-Chat-13B and a webscrape of this Github page.)

![alt text](http://www.libraryofcelsus.com/wp-content/uploads/2023/08/Aetherius-Example-3.png)

## Database Visualization with Qdrant

![alt text](http://www.libraryofcelsus.com/wp-content/uploads/2023/08/Qdrant-Visulization.png)

## Future Plans

• Improve Ui

• Continue to Improve internal prompts

• Finish Aetherius Usage Guide

• Better Documentation 

• Book/File Summarizer Tool

• Data Comparison Tool

• Add more LLM models

• Launch Ai Tutorial YouTube Channel

# Changelog:
**0.046c**

• Added a random forest like approach for explicit memory search

• Fixed knowledge domain selection bug

**0.046b**

• Fixed Unicode encoding error when writing personality files.

• Added GPT Vision to Agent mode.

• Added GPT Vision Support.  I recommend using the discord bot for this.

• Added Forced Memory Upload Mode.

• Various Backend Changes, no additional functionality for now, mostly for future stuff.

• Fixed Sub-Agent Selection Bug.

**0.046a**

• Added New Category System for Sub-Agents, only in Async API script for now.

• Fixed Bug Causing Multiple Categories to be loaded into category list.  Also fixed Empty Prompt Bug.  Async API Version Only.

• Added Separate Scripts for Memory Sub-Agent Category.  Async API Version Only.

• Added Experimental Knowledge Domains for Explicit Long-term Memory.  Async API Version Only.

• Fixed No Collection Bug for External Resource Search. Async API Version Only.

• Worked on Knowledge Domain Selection. Async API Version Only.

• Added Temporary Gradio Ui for testing agent mode until other ui is redone. Username and Botname must be changed in "Gradio-Ui.py" If using Discord Bot, user_id must be set to discord username.


**0.045c**

• Added Bot and User profile descriptions.  This can be disabled in the Api settings json.

• Converted .txt setting files to json

• Added Discord Bot Script using Api in ./Aetherius_API/Examples

• Added basic API script that can be imported to use Aetherius programmatically. (Still an early work in progress)

• Added Memory Search Sub-Agent and an autonomous web-search if the needed information is not in the External Resources DB.

• Added Sub-Agent script.  You can now create custom sub-agents for Aetherius's parallel processing loop.

• Converted Llama 2 Chatbot to use Json for settings.

• Better Sorting for using Multiple Hosts.

• Various Bug Fixes


**0.045c**

• Added Ability to use Multiple Hosts with Oobabooga.

• Improved Llama 2 Internal Prompts

• Added Important Score to some memory types (Still a work in progress)

**0.045b**

• Added Video Processing to the Llama 2 file scrape tool. 

• Added Voice Cloning with coqui TTS.

**0.045a**

• Added check for punctuation for memory uploads to avoid cut off uploads in Llama 2 chatbot.

• Added Delete buttons for external resources in DB management Deletion Menu in Llama 2 chatbot.

• Improved Internal Prompts for Llama 2 Agent Mode and Webscrape Tool.

• Various Bug Fixes

**0.044f**

• Added Voice input using Whisper and TTS using gTTS or Eleven Labs.  Bark TTS still a work in progress.

**0.044e**

• Fixed Bug where embedding size wasn't being set when creating collections.

• Switched usernames from collection name to metadata.

**0.044d**

• Added Embedding Selection Menu, for now only Sentence Transformers and Hugging Face Embeddings are available.

**0.044c**

•New Gui for Aetherius.  Most Chatbot modes are now consolidated under one Ui.

**0.044b**

•Updated Llama-2 Gui Appearance and Features

•Merged Fileprocessing Chatbot into Aethersearch

•Fixed Bug where html markdown was printed instead of normal text when using Public Api.

•Added Colab Notebook for people without a GPU.

**0.044a**

• Consolidated Collections for better visualization with Qdrant (Available in the Qdrant dashboard)

• Added Source tag for external data scrapes

Older Changelogs can be found at: https://www.libraryofcelsus.com/aetherius/

# Installation Guide

## Google Colab

To run Aetherius on Google Colab, first run either the AetherNode or Oobabooga Public Api: 

AetherNode API: <a target="_blank" href="https://colab.research.google.com/github/libraryofcelsus/Aetherius_AI_Assistant/blob/main/Colab%20Notebooks/AetherNode_Public_Api.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>

Oobabooga API: <a target="_blank" href="https://colab.research.google.com/github/libraryofcelsus/Aetherius_AI_Assistant/blob/main/Colab%20Notebooks/Oobabooga_Public_Api.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>  

Then, go to Qdrant and get an API key and URL: https://qdrant.to/cloud

The final step will be to run the actual Aetherius Script.

To use it locally, change the api in the chatbot_settings.json in the Aetherius_API folder to use Oobabooga instead of AetherNode.  Then change Host_Oobabooga to the given public url from the colab.

To run it on a colab notebook click here: <a target="_blank" href="https://colab.research.google.com/github/libraryofcelsus/Aetherius_AI_Assistant/blob/main/Colab%20Notebooks/Aetherius_Colab_Edition_Oobabooga.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>   
(Note: The colab version of Aetherius is rarely updated and is more meant as a demo.)

## Installer bat

Installer File can be found at: **https://github.com/libraryofcelsus/Aetherius_AI_Assistant/blob/main/windows_installer.bat**

**1.** Install Python 3.10.6, Make sure you add it to PATH: **https://www.python.org/downloads/release/python-3106/**

**2.** Run the Windows_Installer Bat as admin.

(If you get an error when installing requirements run: **python -m pip cache purge**)

(If using Ui, edit settings outside of api folder.  If using Api, edit settings inside the Api Folder.  Discord and Gradio use the Api.)

**3.** Copy your OpenAi and Qdrant API/URL keys to the api_keys folder inside of the created Aetherius_API folder if you are using the OpenAi version or GPT Vision.

**4.** Copy your Google CSE Key and Api Key to the api_keys folder or set Web_Search to False in the External Resources Sub-Agent.  You can also change the search engine to Bing.

**5.** To run Aetherius with it's custom API, open the Aetherius_Ai_Assistant folder and run: **windows_aethernode_install.bat**  
Alternativly you can download and installit here: https://github.com/libraryofcelsus/AetherNode    
This is the new default API for Aetherius.  Installation Instructions can be found on the github page.  

AetherNode Google Colab if you don't have a GPU: <a target="_blank" href="https://colab.research.google.com/github/libraryofcelsus/Aetherius_AI_Assistant/blob/main/Colab%20Notebooks/AetherNode_Public_Api.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>

**6.** To run Aetherius Locally using Oobabooga, first install the web-ui at: https://github.com/oobabooga/text-generation-webui/releases/tag/snapshot-2023-11-05

Oobabooga Text-Ui just changed how their api works.  The most up to date version that works is snapshot-2023-11-05
This can be done through the release menu or **git clone https://github.com/oobabooga/text-generation-webui --branch snapshot-2023-11-05**

To run Aetherius on Google Colab with Oobabooga using a public Api, use the Notebook file in the "./Colab Notebooks" Folder.  To use the Public Api with Aetherius, change the "HOST_Oobabooga" in the settings json to the given non-streaming Url.  To use multiple Hosts, separate them with a space. <a target="_blank" href="https://colab.research.google.com/github/libraryofcelsus/Aetherius_AI_Assistant/blob/main/Colab%20Notebooks/Oobabooga_Public_Api.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>

  Then, under the "Interface Mode" tab, enable the api checkbox in the "Available Extensions" field only. Then click apply and restart the interface.   

  Next, navigate to the models tab. Uncheck the autoload models box and then input "TheBloke/Llama-2-13B-chat-GPTQ" into the downloads box (7B model can be used for faster results, but it occasionally breaks format and has a tendency to make things up.  Wouldn't recommend if you need factual data). Other models may work, but this is the one that is tested.   

  Once the download is completed, reload the model selection menu and then select the model. Change the model loader to Exllamav2 and set the max_seq_len to "4096".  Set the "gpu_split" to 1 GB under your Gpu's max Vram.   

  Click the "load" button and load the model.    

  Now, go into the chatbot_settings.json file in the Aetherius_API folder and change the API to Oobabooga instead of AetherNode. Aetherius should now work!  

**7.** Set up Qdrant

Qdrant Cloud: https://qdrant.to/cloud

To use a local Qdrant server, first install Docker: https://www.docker.com.  
Next type: **docker pull qdrant/qdrant:v1.5.1** in the command prompt.  
After it is finished downloading, type **docker run -p 6333:6333 qdrant/qdrant:v1.5.1**  

See: https://docs.docker.com/desktop/backup-and-restore/ for how to make backups.

Once the local Qdrant server is running, it should be auto detected by Aetherius.

If No Qdrant server is running, Aetherius will save to disk.

**8.** Launch Aetherius with one of the **run.bat** files.

**9.** Upload heuristics to DB and change the Bot and User name to start chatting with Aetherius!  

To change the model used with AetherNode, change the "model_name_or_path" key in AetherNode/settings.json to the desired model.  You must then change the "Model_Backend" key in Aetherius_API/chatbot_settings.json to the desired format.  Only Llama-2-Chat and Alpaca are available for now.

Settings and Prompts can be found in the Aetherius_API folder.

Photo OCR (jpg, jpeg, png) requires tesseract: https://github.com/UB-Mannheim/tesseract/wiki
Once installed, copy the "Tesseract-OCR" folder from Program Files to the "Aetherius_Ai_Assistant" Folder.

 To get Whisper working with cuda, you may need to run the commands: **.\venv\Scripts\activate**  **pip uninstall torch torchaudio**    **pip install torch torchvision torchaudio -f https://download.pytorch.org/whl/cu118/torch_stable.html**

[Aetherius Usage Guide](https://www.libraryofcelsus.com/research/aetherius-usage-guide/)

## For Discord Bot

**1.** Go to: https://discord.com/developers and create a New Application for your Bot.

**2.** Go to the Bot Tab in the Application and enable all Privileged Gateway Intents.

**3.** Copy the Bot Token into the Discord_Bot.py script for Aetherius.

**4.** Change the bots name if desired.  (If using in a server and you don't want the memories to be per user, replace "str(ctx.author)" with something like "server".)

**5.** Go to the OAuth2 tab and click the URL Generator sub-tab.

**6.** Enable the bot and applications.commands checkboxes in "SCOPES"

**7.** Enable the Administrator checkbox in "BOT PERMISSIONS"

**8.** Use the link to add the bot to a server.

**9.** DM the bot.  If you have given it an OpenAi key, you can also send photos.

*Bot Commands*

!Agent <ENTER QUERY TO BOT>  
(Activates Aetherius's Sub-Agent Mode)

!Heuristics <ENTER HEURISTIC>  
(Allows you to upload a Heuristic) 

!ImplicitSTM <ENTER SHORT TERM MEMORY>   
(Allows you to upload a Short Term Implicit Memory) 

!ExplicitSTM <ENTER SHORT TERM MEMORY>   
(Allows you to upload a Short Term Explicit Memory) 

!ImplicitLTM <ENTER LONG TERM MEMORY>  
(Allows you to upload a Long Term Implicit Memory) 

!ExplicitLTM <ENTER LONG TERM MEMORY> 
(Allows you to upload a Long Term Explicit Memory) 

## Windows Installation

**Guide with Photos can be found at [https://www.libraryofcelsus.com/aetherius-setup-guide/]**

**Photo Guide Out of Date**

**1.** Install Git: **https://git-scm.com/** (Git can be skipped by downloading the repo as a zip file under the green code button)

**2.** Install Python 3.10.6, Make sure you add it to PATH: **https://www.python.org/downloads/release/python-3106/**

**3.** Open the program "Git Bash". 

**4.** Run git clone: **git clone https://github.com/libraryofcelsus/Aetherius_AI_Assistant.git**

**5.** Open CMD as Admin (Command Panel)

**6.** Navigate to Project folder: **cd PATH_TO_AETHERIUS_INSTALL**

**7.** Create a virtual environment: **python -m venv venv**

**8.** Activate the environment: **.\venv\scripts\activate**   (This must be done before running Aetherius each time. The run.bat will also automatically do this.)

**9.** Install the required packages: **pip install -r requirements.txt**   
(If you get an error when installing requirements run: **python -m pip cache purge** after activating the venv)

**10.** Update Numpy version: **pip install --upgrade numpy==1.24**  (If you get an error from TTS ignore it.)

**11.** Install FFmpeg: **https://www.gyan.dev/ffmpeg/builds/**

**12.** Install Torch with Cuda: **pip uninstall torch torchvision**  **pip install torch torchvision torchaudio -f https://download.pytorch.org/whl/cu118/torch_stable.html**

**13.** Copy your OpenAI api key to key_openai.txt (If using Oobabooga, you may skip this.)

**14.** If using Qdrant Cloud copy their Api key and Url to their respective .txt files in the ./api_keys folder.  Qdrant Cloud: https://qdrant.to/cloud

**15.** To use a local Qdrant server, first install Docker: https://www.docker.com/

**16.** Now run: **docker pull qdrant/qdrant:v1.5.1** in CMD

**17.** Next run: **docker run -p 6333:6333 qdrant/qdrant:v1.5.1**

**18.** Once the local Qdrant server is running, it should be auto detected by Aetherius.  If No Qdrant server is running, Aetherius will save to disk.   
(See: https://docs.docker.com/desktop/backup-and-restore/ for how to make backups.)

(If using Ui, edit settings outside of api folder.  If using Api, edit settings inside the Api Folder.  Discord and Gradio use the Api.)

**19.** Copy your Google Api key to key_google.txt  (You can disable the External Resources Web_Search in the script file.)

**20.** Copy your Google CSE ID to key_google_cse.txt

**21.** If you plan on using Photo OCR (jpg, jpeg, png Text Recognition), it requires tesseract: https://github.com/UB-Mannheim/tesseract/wiki
    Once installed, copy the "Tesseract-OCR" folder from Program Files to the "Aetherius_Ai_Assistant" Folder.  Photos must be placed in the ./Upload/SCANS folder.

**22.** Run main.py by typing **python main.py** in cmd or one of the **run.bat** files as admin to start Aetherius. (Using run.bat will let you skip opening CMD and activating the environment.)

**23.** Select DB Upload Heuristics from the DB Management menu to upload Heuristics for the bot, this DB can also function as a Personality DB. An example of how to do 
    this can be found in "personality_db_input_examples.txt" in the config folder.

**24.** Edit the chatbot's prompts with the Config Menu. This will let you change the main, secondary, and greeting prompts.  You can also change things like the font style 
    and size.

**25.** You can change the botname and the username in the login menu.  Changing either of these will create a new chatbot.

**26.** Once the chatbot has adopted a desired personality, I recommend creating a backup of the "nexus" folder and then create a collection of the "aetherius" index on 
    pinecone.io.  This will let you revert back to a base state if issues arise later.

**27.** Once you have made a backup, you can start using the "Auto" mode, this mode has Aetherius decide for itself whether or not it should upload to its memories.

**28.** To run Aetherius with it's custom API, download and install: https://github.com/libraryofcelsus/AetherNode    
This is the new default API for Aetherius.  Installation Instructions can be found on the github page.

To change the model used with AetherNode, change the "model_name_or_path" key in AetherNode/settings.json to the desired model.  You must then change the "Model_Backend" key in Aetherius_API/chatbot_settings.json to the desired format.  Only Llama-2-Chat and Alpaca are available for now.

AetherNode Google Colab if you don't have a GPU: <a target="_blank" href="https://colab.research.google.com/github/libraryofcelsus/Aetherius_AI_Assistant/blob/main/Colab%20Notebooks/AetherNode_Public_Api.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>

**29.** To run Aetherius Locally using Oobabooga, first install the web-ui at: https://github.com/oobabooga/text-generation-webui/releases/tag/snapshot-2023-11-05

Oobabooga Text-Ui just changed how their api works.  The most up to date version that works is snapshot-2023-11-05
This can be done through the release menu or **git clone https://github.com/oobabooga/text-generation-webui --branch snapshot-2023-11-05**

To run Aetherius on Google Colab with Oobabooga using a public Api, use the Notebook file in the "./Colab Notebooks" Folder.  To use the Public Api with Aetherius, change the "HOST_Oobabooga" in the settings json to the given non-streaming Url.  To use multiple Hosts, separate them with a space. <a target="_blank" href="https://colab.research.google.com/github/libraryofcelsus/Aetherius_AI_Assistant/blob/main/Colab%20Notebooks/Oobabooga_Public_Api.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>

Then, under the "Interface Mode" tab, enable the api checkbox in the "Available Extensions" field only. Then click apply and restart the interface.

Next, navigate to the models tab. Uncheck the autoload models box and then input "TheBloke/Llama-2-13B-chat-GPTQ" into the downloads box (7B model can be used for faster results, but it occasionally breaks format and has a tendency to make things up.  Wouldn't recommend if you need factual data). Other models may work, but this is the one that is tested.

Once the download is completed, reload the model selection menu and then select the model. Change the model loader to Exllamav2 and set the max_seq_len to "4096".  Set the "gpu_split" to 1 GB under your Gpu's max Vram.

Click the "load" button and load the model. 

Now, go into the chatbot_settings.json file in the Aetherius_API folder and change the API to Oobabooga instead of AetherNode. Aetherius should now work!



**30.** Settings Json and Prompts can be found in the Aetherius_API folder.

-----

## About Me

In January 2023, I had my inaugural experience with ChatGPT 3.5 and LLMs in general. Since that moment, I've been deeply obsessed with AI, dedicating countless hours each day to studying it and to hands-on experimentation. The Aetherius AI Assistant is the culmination of that research.

# Contact
Discord: libraryofcelsus      -> Old Username Style: Celsus#0262

MEGA Chat: https://mega.nz/C!pmNmEIZQ


