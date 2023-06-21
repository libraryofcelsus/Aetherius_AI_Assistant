import os
import tkinter as tk
import importlib.util
from tkinter import ttk


class OobaboogaChatbotMenu(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title('Aetherius Oobabooga General Chatbot Menu')
        self.geometry('500x400')  # adjust as needed

        label = ttk.Label(self, text="***********************************\n"
                                       "*Welcome to the Aetherius Chatbot!*\n"
                                       "***********************************\n"
                                       "*  Press [Exit] to return to the  *\n"
                                       "*           main menu!            *\n"
                                       "***********************************")
        label.pack(side="top")

        # Get a list of all the files in the folder
        files = os.listdir('scripts/Oobabooga_General_Chatbot')
        # Filter out only the .py files 
        scripts = [file for file in files if file.endswith('.py')]
        # Create a button for each script
        for i, script in enumerate(scripts):
            # Replace underscores with spaces
            script_name = script[:-3].replace('_', ' ')
            button = ttk.Button(self, text=script_name, command=lambda s=script: self.run_script(s))
            button.pack(side="top")

        exit_button = ttk.Button(self, text="Exit", command=self.destroy)
        exit_button.pack(side="bottom")

    def run_script(self, script):
        # Remove the .py extension to get the module name
        module_name = script[:-3]
        # Import the module
        spec = importlib.util.spec_from_file_location(module_name, f"scripts/Oobabooga_General_Chatbot/{script}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # Call the function with the same name as the module
        function = getattr(module, module_name)
        function()

def Menu_Oobabooga_General_Chatbot(parent):
    OobaboogaChatbotMenu(parent)