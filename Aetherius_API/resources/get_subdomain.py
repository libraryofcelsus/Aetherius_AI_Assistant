# get_subdomain.py
import json

def get_subdomain():
    with open('API_Settings.json', 'r') as file:
        settings = json.load(file)
        print(settings.get('ngrok_reserved_address', '').split('//')[1])

if __name__ == "__main__":
    get_subdomain()
