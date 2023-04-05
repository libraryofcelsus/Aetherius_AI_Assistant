# Aetherius
Version 0.2 of the Aetherius Personal Assistant by LibraryofCelsus.com
https://github.com/libraryofcelsus

Inspired by https://github.com/daveshap/

## Windows Installation

1. Install Git: **https://git-scm.com/**

2. Install Python 3.10.6, Make sure you add it to PATH: **https://www.python.org/downloads/release/python-3106/**

3. Run git clone: **git clone https://github.com/libraryofcelsus/Aetherius-Personal-Assistant**

4. Navigate to Project folder: **cd PATH**

5. Open CMD as Admin

6. Create a virtual environment: **python3 -m venv venv**

7. Activate the environment: **.\venv\Scripts\activate**

8. Install the required packages: **pip -r requirements.txt**

9. Copy your OpenAI api key to key_openai

10. Create a Index on pinecone.io titled: "aetherius" with 1536 dimensions and cosine as the metric. I usually do a P1 instance.

11. Copy Api key for that Index and paste it in key_pinecone.txt

12. Copy Index Enviornment/Region to key_pinecone_env.txt

13. Run Aetherius_Ai.py

14. Input "5" to upload Aetherius's Secondary Heuristics or a custom Personality.  An example of how to do this can be found in "personality_db_inputs.txt"

13. Type "Exit" to return to main menu.

14. Input "1" or "3" to enter Manual Chat mode, this also functions as a training mode.  You want to begin talking to Aetherius in this mode so you can guide its initial development.

14. Exit out and choose an "Auto" mode after the Chatbot's memories have been established.  This mode has the bot decide for itself whether it should upload to its memories.

15. Using the GPT 3.5 mode causes a significant decrease in intelligence, and as such generally shouldn't be used for training. Auto-Memory may also lead to some issues, Manual Chat is recommended if only using GPT 3.5.

