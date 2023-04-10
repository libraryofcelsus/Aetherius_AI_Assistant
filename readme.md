# Aetherius
Version 0.021 of the Aetherius Personal Assistant by LibraryofCelsus.com
https://github.com/libraryofcelsus

Inspired by https://github.com/daveshap/

# Current Version Information
Welcome to the first pre-alpha release of Aetherius, a highly customizable AI assistant designed to adapt to your specific needs. 

Aetherius aims to provide a modular, personalized AI assistant experience by enabling the addition of task-specific Modules and Sub-Modules. If all goes as planned, Aetherius will support integration with other open-source projects.

In future releases, Aetherius will feature a core long-term memory chatbot alongside a prototype world information generator. The current version of the generator can create small-scale enviornments such as towns, but my ultimate vision is to develop a comprehensive system that allows users to create entire worlds and explore them in a text-RPG format. If successful, Aetherius will also generate real-time storyboards, offering users a seamless platform for creative writing and idea generation.

## Windows Installation

1. Install Git: **https://git-scm.com/**

2. Install Python 3.10.6, Make sure you add it to PATH: **https://www.python.org/downloads/release/python-3106/**

3. Run git clone: **git clone https://github.com/libraryofcelsus/Aetherius_AI_Assistant.git**

4. Navigate to Project folder: **cd PATH**

5. Open CMD as Admin

6. Create a virtual environment: **python3 -m venv venv**

7. Activate the environment: **.\venv\Scripts\activate**

8. Install the required packages: **pip install -r requirements.txt**

9. Copy your OpenAI api key to key_openai

10. Create a Index on pinecone.io titled: "aetherius" with 1536 dimensions and cosine as the metric. I usually do a P1 instance.

11. Copy Api key for that Index and paste it in key_pinecone.txt

12. Edit the prompt_.txt files to customize the bot.

13. Run db_upload_personality.py and upload a personality for the bot. An example of how to do this can be found in "personality_db_inputs.txt", located in the scripts folder.

14. Run chat_training.py with Python 3.10.6 (Using the Auto Memory Version at the beginning can lead to an undesired personality.)

15. Run chat_auto.py when the Chatbot's memories have been established.  This script has the bot decide for itself whether it should upload to the DB.

16. Using the GPT 3.5 scripts causes a significant decrease in intelligence, and as such generally shouldn't be used for training. Auto-Memory may also lead to some issues, chat - manual is recommended if only using GPT 3.5.
