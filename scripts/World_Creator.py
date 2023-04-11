import os
import openai
import pinecone
import time
import sys
import importlib
sys.path.insert(0, './scripts/World_Creator')


def World_Creator():
    print("***********************************")
    print("*    Welcome to  the Aetherius    *")
    print("*         World Generator         *")
    print("***********************************")
    print("*  Type [Exit] to return to the   *")
    print("*           main menu!            *")
    print("***********************************")
    # Get a list of all the files in the folder
    files = os.listdir('scripts/World_Creator')
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
        print('\n\nSYSTEM: Are you sure you want to exit?')
        while True:
            print('        Press Y for yes, N for no.')
            user_input = input("'Y' or 'N': ")
            if user_input == 'y':
                return
            elif user_input == 'n':
                pass
            else:
                pass
    choice = int(a)
    # Make sure the choice is valid
    if 1 <= choice <= len(scripts):
        # Get the chosen script
        script = scripts[choice-1]
        # Remove the .py extension to get the module name
        module_name = script[:-3]
        # Import the module
        spec = importlib.util.spec_from_file_location(module_name, f"scripts/World_Creator/{script}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # Call the function with the same name as the module
        function = getattr(module, module_name)
        function()
    else:
        print("Invalid choice")