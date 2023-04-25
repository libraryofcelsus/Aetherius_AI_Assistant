# Aetherius
Version 0.035 of the Aetherius Personal Assistant by LibraryofCelsus.com

https://github.com/libraryofcelsus

Inspired by https://github.com/daveshap/

![](http://www.libraryofcelsus.com/wp-content/uploads/2023/04/Aetherius-Example-gif.gif)

# Current Version Information
Welcome to the pre-alpha release of Aetherius, a highly customizable AI assistant designed to adapt to your specific needs.  I prefer a more "anthropomorphized" personal Ai as talking to something like base GPT feels off-putting.  The end goal of Aetherius is to both provide a realistic Ai companion and a cognitive framework that can be added on top of other Ai tools.

Aetherius aims to provide a modular, personalized AI assistant experience by enabling the addition of task-specific Modules and Sub-Modules. If all goes as planned, Aetherius will support integration with other open-source projects.

## Changelog:
0.035

-Separated General Memory DB into Implicit and Explicit Memories.

-Various Bug Fixes

0.034

-Added Voice Assistant Script, only on keypress for now. Always listening will come later.

-Auto Memory Upload bug fix

0.033

-Improved Auto Memory Upload

-Various Bug Fixes

0.032

-Implemented new system for memory recall

-Added Debug output scripts, these print all of the internal loops that are hidden in the other scripts.

0.031

-Reworked some internal prompts, internal monologue consistancy issue should be fixed.

-Various Bug Fixes

0.03

-Improved Episodic Memory Implementation

-Summary length bug fixed

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

**Guide with Photos can be found at [https://www.libraryofcelsus.com/aetherius-setup-guide/]**

1. Install Git: **https://git-scm.com/** (Git can be skipped by downloading the repo as a zip file under the green code button)

2. Install Python 3.10.6, Make sure you add it to PATH: **https://www.python.org/downloads/release/python-3106/**

3. Open the program "Git Bash". 

4. Run git clone: **git clone https://github.com/libraryofcelsus/Aetherius_AI_Assistant.git**

5. Open CMD as Admin

6. Navigate to Project folder: **cd PATH**

7. Create a virtual environment: **python -m venv venv**

8. Activate the environment: **.\venv\scripts\activate**

9. Install the required packages: **pip install -r requirements.txt**

10. Copy your OpenAI api key to key_openai.txt

11. Create a Index on pinecone.io titled: "aetherius" with 1536 dimensions and cosine as the metric. I usually do a P1 instance.

12. Copy Api key for that Index and paste it in key_pinecone.txt

13. Copy the Pinecone Enviornment and paste it in key_pinecone_env.txt

14. Edit the .txt files in the "config" folder to customize the bot.

15. Run main.py with **python main.py** to start Aetherius, Select DB Management.

16. Select DB Upload Heuristics to upload secondary Heuristics for the bot, this DB can also function as a Personality DB. An example of how to do this can be found in "personality_db_input_examples.txt" in the config folder.

17. Upload your desired Cadence to "DB Upload Cadence" in DB Management. This should be a direct example of the speech style, not a description. I suggest asking Aetherius to use the diction of a "____" to generate an example, then copy paste the response to the Cadence Upload.

18. Type "Exit" twice to return to the main menu. Now select "Main Bot"

19. Select one of the "Training" chatbot modes, this will enable you to choose what gets uploaded to the chatbots memories.  It also enables a summary of Aetherius's inner loop, avoid uploading irrelivant information to the inner loop DB as they tend to take priority over other memories. 

20. Once the chatbots memories have been established, type "Exit" and then select one of the "Manual" chatbots, this mode is similar to the training mode, but disables the inner-loop summary and upload sequence.

21. Once the chatbot has adopted a desired personality, I recommend creating a backup of the "nexus" folder and then create a collection from the "aetherius" index on pinecone.io.  This will let you revert back to a base state if issues arise later.

22. Once you have made a backup, you can start using the "Auto mode, this mode has Aetherius decide for itself whether or not it should upload to its memories.

23. Using the GPT 3.5 scripts causes a significant decrease in intelligence, and as such generally shouldn't be used for training. Auto-Memory may also lead to some issues, chat - manual is recommended if only using GPT 3.5.

# Contact
Discord: Kutkh#7805

Email: email@libraryofcelsus.com
