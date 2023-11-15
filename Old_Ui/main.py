import os
import time
import sys
import importlib.util
sys.path.insert(0, './scripts')
import platform
import tkinter as tk
import customtkinter
import json
from tkinter import PhotoImage
import webbrowser



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
        self.geometry('720x500')  # adjust as needed
        customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
        self.parent = parent
        self.module = module
        self.function_name = function_name
        self.create_widgets()
        dark_bg_color = "#2b2b2b"  # Dark background color. You can adjust this value.
        self.configure(bg=dark_bg_color)  # Set the Toplevel's background color


    def create_widgets(self):
        with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)

        # Extract the font and font_size settings from the dictionary
        font_config = settings.get('font', 'Arial')  # Provide a default value if the key doesn't exist
        font_size = settings.get('font_size', '12')  # Provide a default value if the key doesn't exist

        self.label = customtkinter.CTkLabel(self, text="Select a script:", font=(font_config, 16, "bold"))
        self.label.pack(side="top", pady=10)

        files = os.listdir('scripts/' + self.function_name.replace('Menu_', ''))
        scripts = [file for file in files if file.endswith('.py')]
        for i, script in enumerate(scripts):
            script_name = script[:-3].replace('_', ' ')
            button = customtkinter.CTkButton(self, text=script_name, command=lambda s=script: self.run_script(s), font=(font_config, 14))
            button.pack(side="top", pady=3)  # Added pady=5 for spacing between buttons
            
        exit_button = customtkinter.CTkButton(self, text="Exit", command=self.destroy)
        exit_button.pack(side="bottom")


    def run_script(self, script):
        module_name = script[:-3]
        spec = importlib.util.spec_from_file_location(module_name, f"scripts/{self.function_name.replace('Menu_', '')}/{script}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        function = getattr(module, module_name)
        function()
        



class Application(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title('Aetherius Main Menu')
        self.geometry(f"{500}x{400}")  # adjust as needed
        self.create_widgets()
        customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"

    def create_widgets(self):
        with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)

        # Extract the font and font_size settings from the dictionary
        font_config = settings.get('font', '')  # Provide a default value if the key doesn't exist
        font_size = settings.get('font_size', '')  # Provide a default value if the key doesn't exist
        try:
            font_size_config = int(font_size)
        except:
            font_size_config = 10
        font_style = (f"{font_config}", font_size_config)
        font_style_bold = (f"{font_config}", font_size_config, "bold")
        
        


     #   self.configure(bg=background_color)
        self.label = customtkinter.CTkLabel(self, text="Welcome to the Aetherius Main Menu!", font=(font_config, 20, "bold"))
        self.label.pack(side="top", pady=10)

        self.label2 = customtkinter.CTkLabel(self, text="Please give a star on GitHub and\nshare with friends to support development!", font=(font_config, 14, "bold"))
        self.label2.pack(side="top", pady=10)

        self.label3 = customtkinter.CTkLabel(self, text="Select an Option:", font=("Arial", 14, "bold"))
        self.label3.pack(side="top", pady=10)

        files = os.listdir('scripts')
        scripts = [file for file in files if file.endswith('.py')]
        for i, script in enumerate(scripts):
            script_name = script[:-3].replace('Menu_', '').replace('_', ' ')
            button = customtkinter.CTkButton(self, text=script_name, command=lambda s=script: self.run_script(s), font=("Arial", 14))
            button.pack(side="top", pady=3)
            
        # Create the Ko-fi button at the bottom left
        kofi_img_path = './scripts/resources/Image/kofi3.png'
        kofi_img = PhotoImage(file=kofi_img_path)

        kofi_label = tk.Label(self, image=kofi_img, cursor="hand2", bg="#242424")
        kofi_label.image = kofi_img  # Keep a reference to avoid garbage collection
        kofi_label.bind("<Button-1>", self.open_kofi_link)

        # Anchor the label to the west (left) and pack it to the bottom
        kofi_label.pack(side="bottom", anchor="w", pady=10)
            
    def open_kofi_link(self, event):
        webbrowser.open('https://ko-fi.com/libraryofcelsus')

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
  #  set_dark_ancient_theme()
    with open('./config/chatbot_settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
            
    bot_name = settings.get('prompt_bot_name', '')
    username = settings.get('prompt_username', '')
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