import os
import openai
import pinecone
import time
import sys
import importlib.util
sys.path.insert(0, './scripts')
from gtts import gTTS
import speech_recognition as sr
from playsound import playsound
from pydub import AudioSegment
from pydub.playback import play
from pydub import effects
import platform
import tkinter as tk
import customtkinter as ctk


def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()


def set_dark_ancient_theme():
    background_color = "#2B303A"  # Dark blue-gray
    foreground_color = "#FDF7E3"  # Pale yellow
    button_color = "#415A77"  # Dark grayish blue
    highlight_color = "#FFB299"  # Peach
    text_color = 'white'

    return background_color, foreground_color, button_color, highlight_color


class SubApplication(tk.Toplevel):
    def __init__(self, parent, module, function_name):
        super().__init__(parent)
        self.title('Aetherius Sub Menu')
        self.geometry('500x400')  # adjust as needed
        self.parent = parent
        self.module = module
        self.function_name = function_name
        self.create_widgets()

    def create_widgets(self):
        background_color, foreground_color, button_color, highlight_color = set_dark_ancient_theme()

        self.configure(bg=background_color)

        self.label = tk.Label(self, text="Select a script:", bg=background_color, fg=foreground_color, font=("Arial", 14, "bold"))
        self.label.pack(side="top", pady=10)

        files = os.listdir('scripts/' + self.function_name.replace('Menu_', ''))
        scripts = [file for file in files if file.endswith('.py')]
        for i, script in enumerate(scripts):
            script_name = script[:-3].replace('_', ' ')
            button = tk.Button(self, text=script_name, command=lambda s=script: self.run_script(s), bg=button_color, activebackground=highlight_color, fg="white", font=("Arial", 12))
            button.pack(side="top", pady=3)  # Added pady=5 for spacing between buttons

    def run_script(self, script):
        module_name = script[:-3]
        spec = importlib.util.spec_from_file_location(module_name, f"scripts/{self.function_name.replace('Menu_', '')}/{script}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        function = getattr(module, module_name)
        function()


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Aetherius Main Menu')
        self.geometry('500x400')  # adjust as needed
        self.create_widgets()

    def create_widgets(self):
        background_color, foreground_color, button_color, highlight_color = set_dark_ancient_theme()

        self.configure(bg=background_color)
        self.label = tk.Label(self, text="Welcome to the Aetherius Main Menu!", bg=background_color, fg=foreground_color, font=("Arial", 18, "bold"))
        self.label.pack(side="top", pady=10)

        self.label2 = tk.Label(self, text="Please give a star on GitHub and\nshare with friends to support development!", bg=background_color, fg=foreground_color, font=("Arial", 12, "bold"))
        self.label2.pack(side="top", pady=10)

        self.label3 = tk.Label(self, text="Select a script:", bg=background_color, fg=foreground_color, font=("Arial", 14, "bold"))
        self.label3.pack(side="top", pady=10)

        files = os.listdir('scripts')
        scripts = [file for file in files if file.endswith('.py')]
        for i, script in enumerate(scripts):
            script_name = script[:-3].replace('_', ' ')
            button = tk.Button(self, text=script_name, command=lambda s=script: self.run_script(s), bg=button_color, activebackground=highlight_color, fg="white", font=("Arial", 12))
            button.pack(side="top", pady=3)

    def run_script(self, script):
        module_name = script[:-3]
        spec = importlib.util.spec_from_file_location(module_name, f"scripts/{script}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        for attr_name in dir(module):
            if attr_name.startswith("Menu_"):
                SubApplication(self, module, attr_name)
                return

        tk.messagebox.showerror("Error", "No Menu_ function found")


if __name__ == '__main__':
#    key = input("Enter OpenAi API KEY:")
#   openai.api_key = key
    set_dark_ancient_theme()
    openai.api_key = open_file('api_keys/key_openai.txt')
    pinecone.init(api_key=open_file('api_keys/key_pinecone.txt'), environment=open_file('api_keys/key_pinecone_env.txt'))
    vdb = pinecone.Index("aetherius")
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
    if not os.path.exists(f'nexus/{bot_name}/{username}/implicit_short_term_memory_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/implicit_short_term_memory_nexus')
    if not os.path.exists(f'nexus/{bot_name}/{username}/explicit_short_term_memory_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/explicit_short_term_memory_nexus')
    if not os.path.exists(f'nexus/{bot_name}/{username}/explicit_long_term_memory_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/explicit_long_term_memory_nexus')
    if not os.path.exists(f'nexus/{bot_name}/{username}/implicit_long_term_memory_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/implicit_long_term_memory_nexus')
    if not os.path.exists(f'nexus/{bot_name}/{username}/episodic_memory_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/episodic_memory_nexus')
    if not os.path.exists(f'nexus/{bot_name}/{username}/flashbulb_memory_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/flashbulb_memory_nexus')
    if not os.path.exists(f'nexus/{bot_name}/{username}/heuristics_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/heuristics_nexus')
    if not os.path.exists(f'nexus/global_heuristics_nexus'):
        os.makedirs(f'nexus/global_heuristics_nexus')
    if not os.path.exists(f'nexus/{bot_name}/{username}/cadence_nexus'):
        os.makedirs(f'nexus/{bot_name}/{username}/cadence_nexus')
    if not os.path.exists(f'logs/{bot_name}/{username}/complete_chat_logs'):
        os.makedirs(f'logs/{bot_name}/{username}/complete_chat_logs')
    if not os.path.exists(f'logs/{bot_name}/{username}/final_response_logs'):
        os.makedirs(f'logs/{bot_name}/{username}/final_response_logs')
    if not os.path.exists(f'logs/{bot_name}/{username}/inner_monologue_logs'):
        os.makedirs(f'logs/{bot_name}/{username}/inner_monologue_logs')
    if not os.path.exists(f'logs/{bot_name}/{username}/intuition_logs'):
        os.makedirs(f'logs/{bot_name}/{username}/intuition_logs')
    if not os.path.exists(f'history/{username}'):
        os.makedirs(f'history/{username}')
    while True:
        app = Application()
        app.mainloop()
        continue