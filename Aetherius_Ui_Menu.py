import warnings
warnings.filterwarnings("ignore", message=".*torch.utils._pytree._register_pytree_node is deprecated.*")
import os
import time
import sys
import importlib.util
import platform
import tkinter as tk
import customtkinter
import json
from tkinter import PhotoImage, messagebox
import webbrowser
from Aetherius_API.Main import *




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


        



class Application(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title('Aetherius Main Menu')
        self.geometry(f"{500}x{400}")  # adjust as needed
        self.create_widgets()
        customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"

    def create_widgets(self):
        with open('./Aetherius_API/chatbot_settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)

        font_config = settings.get('font', 'Arial')  # Provide a default value if the key doesn't exist
        font_size = settings.get('font_size', 10)  # Provide a default value if the key doesn't exist

        self.label = customtkinter.CTkLabel(self, text="Welcome to the Aetherius Main Menu!", font=(font_config, 20, "bold"))
        self.label.pack(side="top", pady=10)

        self.label2 = customtkinter.CTkLabel(self, text="Please give a star on GitHub and\nshare with friends to support development!", font=(font_config, 14, "bold"))
        self.label2.pack(side="top", pady=10)

        self.label3 = customtkinter.CTkLabel(self, text="Select an Option:", font=("Arial", 14, "bold"))
        self.label3.pack(side="top", pady=10)

        scripts = [file for file in os.listdir('Aetherius_GUI') if file.endswith('.py')]
        for script in scripts:
            script_name = script[:-3].replace('Menu_', '').replace('_', ' ')
            button = customtkinter.CTkButton(self, text=script_name, command=lambda s=script: self.run_script(s), font=("Arial", 14))
            button.pack(side="top", pady=3)

        kofi_img_path = './Aetherius_GUI/Images/kofi3.png'
        kofi_img = PhotoImage(file=kofi_img_path)
        kofi_label = tk.Label(self, image=kofi_img, cursor="hand2", bg="#242424")
        kofi_label.image = kofi_img
        kofi_label.bind("<Button-1>", self.open_kofi_link)
        kofi_label.pack(side="bottom", anchor="w", pady=10)

    def open_kofi_link(self, event):
        webbrowser.open('https://ko-fi.com/libraryofcelsus')

    def run_script(self, script):
        module_name = script[:-3]
        spec = importlib.util.spec_from_file_location(module_name, f"./Aetherius_GUI/{script}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        function_name = module_name
        if hasattr(module, function_name):
            func = getattr(module, function_name)
            if callable(func):
                if "self" in func.__code__.co_varnames:
                    func(self)  # Call with self if the function expects it
                else:
                    func()  # Call without self if the function does not expect it
        else:
            messagebox.showerror("Error", f"No {function_name} function found in the script")




if __name__ == '__main__':
    app = Application()
    app.mainloop()