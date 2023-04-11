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
    print("*          World Generator        *")
    print("***********************************")
    print("*Type [Exit] after making a choice*")
    print("*    to return to this screen!    *")
    print("***********************************")
    script_dir = './scripts/World_Creator'
    py_files = [f for f in os.listdir(script_dir) if f.endswith('.py')]
    for i, py_file in enumerate(py_files):
        filename = os.path.splitext(py_file)[0].replace('_', ' ')
        print(f"{i+1}. {filename}")
    choice = input("Please enter a number: ")
    if choice == 'Exit':
        return
    if choice.isdigit() and int(choice) in range(1, len(py_files)+1):
        module_name = os.path.splitext(py_files[int(choice)-1])[0]
        module = importlib.import_module(module_name)
        functions = [func for func in dir(module) if callable(getattr(module, func))]
        for function_name in functions:
            getattr(module, function_name)()
    else:
        print("Invalid choice. Please try again.")
        Main_Bot()