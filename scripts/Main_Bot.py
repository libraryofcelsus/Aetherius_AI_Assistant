import os
import openai
import pinecone
import time
import sys
import importlib
sys.path.insert(0, './scripts/Main_Bot')
sys.path.insert(0, './scripts')

def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()


def Main_Bot():
    print("***********************************")
    print("*Welcome to the Aetherius Chatbot!*")
    print("***********************************")
    print("*  Type [Exit] to return to the   *")
    print("*           main menu!            *")
    print("***********************************")
    # Get a list of all the files in the folder
    files = os.listdir('scripts/Main_Bot')
    # Filter out only the .py files 
    scripts = [file for file in files if file.endswith('.py')]
    # Print the menu options
    for i, script in enumerate(scripts):
        # Replace underscores with spaces
        script_name = script[:-3].replace('_', ' ')
        print(f"{i+1}. {script_name}")
    # Get the user's choice
    a = input("Enter your choice: ")
    if a == 'Exit':
        return
    choice = int(a)
    # Make sure the choice is valid
    if 1 <= choice <= len(scripts):
        # Get the chosen script
        script = scripts[choice-1]
        # Remove the .py extension to get the module name
        module_name = script[:-3]
        # Import the module
        spec = importlib.util.spec_from_file_location(module_name, f"scripts/Main_Bot/{script}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # Call the function with the same name as the module
        function = getattr(module, module_name)
        function()
    else:
        print("Invalid choice")