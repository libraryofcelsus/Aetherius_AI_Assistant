import os
import importlib.util
import tkinter as tk
from tkinter import ttk
import customtkinter

class OpenAiMenu(tk.Toplevel):
    def __init__(self):
        super().__init__()
        customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
        self.title('Aetherius Pinecone/OpenAi Menu')
        self.geometry('720x500')  # adjust as needed
        dark_bg_color = "#2b2b2b"  # Dark background color. You can adjust this value.
        self.configure(bg=dark_bg_color)  # Set the Toplevel's background color


        # Get a list of all the files in the folder
        files = os.listdir('scripts/Old_Scripts/Old_Pinecone_Scripts/OpenAi')
        # Filter out only the .py files 
        scripts = [file for file in files if file.endswith('.py')]
        # Create a button for each script
        for i, script in enumerate(scripts):
            # Replace underscores with spaces
            script_name = script[:-3].replace('_', ' ')
            button = customtkinter.CTkButton(self, text=script_name, command=lambda s=script: self.run_script(s))
            button.pack(side="top")

        exit_button = customtkinter.CTkButton(self, text="Exit", command=self.destroy)
        exit_button.pack(side="bottom")

    def run_script(self, script):
        # Remove the .py extension to get the module name
        module_name = script[:-3]
        # Import the module
        spec = importlib.util.spec_from_file_location(module_name, f"scripts/Old_Scripts/Old_Pinecone_Scripts/OpenAi/{script}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # Call the function with the same name as the module
        function = getattr(module, module_name)
        function()

def Menu_OpenAi():
    OpenAiMenu()