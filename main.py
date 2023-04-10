import os
import openai
import pinecone
import time
import sys
import importlib.util
sys.path.insert(0, './scripts')

def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()


def main_menu_old():
    print("***********************************")
    print("*Welcome to the Aetherius Chatbot!*")
    print("***********************************")
    print("*Type [Exit] after making a choice*")
    print("*    to return to this screen!    *")
    print("***********************************")
    script_dir = 'Scripts'
    py_files = [f for f in os.listdir(script_dir) if f.endswith('.py')]
    for i, py_file in enumerate(py_files):
        filename = os.path.splitext(py_file)[0].replace('_', ' ')
        print(f"{i+1}. {filename}")
    choice = input("Please enter a number: ")
    if choice.isdigit() and int(choice) in range(1, len(py_files)+1):
        module_name = os.path.splitext(py_files[int(choice)-1])[0]
        module = importlib.import_module(module_name)
        functions = [func for func in dir(module) if callable(getattr(module, func))]
        for function_name in functions:
            getattr(module, function_name)()
    else:
        print("Invalid choice. Please try again.")
        main_menu()


def main_menu():
    print("***********************************")
    print("*Welcome to the Aetherius Main Menu*")
    print("***********************************")
    print("*Type [Exit] after making a choice*")
    print("*    to return to this screen!    *")
    print("***********************************")
    # Get a list of all the files in the folder
    files = os.listdir('scripts')
    # Filter out only the .py files 
    scripts = [file for file in files if file.endswith('.py')]
    # Print the menu options
    for i, script in enumerate(scripts):
        # Replace underscores with spaces
        script_name = script[:-3].replace('_', ' ')
        print(f"{i+1}. {script_name}")
    # Get the user's choice
    choice = int(input("Enter your choice: "))
    # Make sure the choice is valid
    if 1 <= choice <= len(scripts):
        # Get the chosen script
        script = scripts[choice-1]
        # Remove the .py extension to get the module name
        module_name = script[:-3]
        # Import the module
        spec = importlib.util.spec_from_file_location(module_name, f"scripts/{script}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # Call the function with the same name as the module
        function = getattr(module, module_name)
        function()
    else:
        print("Invalid choice")


if __name__ == '__main__':
#    key = input("Enter OpenAi API KEY:")
#   openai.api_key = key
    openai.api_key = open_file('api_keys/key_openai.txt')
    pinecone.init(api_key=open_file('api_keys/key_pinecone.txt'), environment=open_file('api_keys/key_pinecone_env.txt'))
    if not os.path.exists('nexus/inner_loop_nexus'):
        os.makedirs('nexus/inner_loop_nexus')
    if not os.path.exists('nexus/memory_nexus'):
        os.makedirs('nexus/memory_nexus')
    if not os.path.exists('nexus/heuristics_nexus'):
        os.makedirs('nexus/heuristics_nexus')
    if not os.path.exists('logs/complete_chat_logs'):
        os.makedirs('logs/complete_chat_logs')
    if not os.path.exists('logs/final_response_logs'):
        os.makedirs('logs/final_response_logs')
    if not os.path.exists('logs/inner_monologue_logs'):
        os.makedirs('logs/inner_monologue_logs')
    if not os.path.exists('logs/intuition_logs'):
        os.makedirs('logs/intuition_logs')
    while True:
        main_menu()
        continue