import sys
sys.path.insert(0, './scripts')
sys.path.insert(0, './config')
sys.path.insert(0, './config/Chatbot_Prompts')
sys.path.insert(0, './scripts/resources')
import os
import openai
import json
import time
from time import time, sleep
import datetime
from uuid import uuid4
import pinecone


def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()
        
        
def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)
        
        
def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return json.load(infile)
        
        
def save_json(filepath, payload):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        json.dump(payload, outfile, ensure_ascii=False, sort_keys=True, indent=2)
        
        
def timestamp_to_datetime(unix_time):
    return datetime.datetime.fromtimestamp(unix_time).strftime("%A, %B %d, %Y at %I:%M%p %Z")
    
    
def is_integer(value):
    try:
        int(value)
        return True
    except ValueError:
        return False
        

def chatgptselector_completion(messages, model="gpt-3.5-turbo", temp=0.2):
    max_retry = 7
    retry = 0
    m = multiprocessing.Manager()
    lock = m.Lock()
    with lock:
        try:
            response = openai.ChatCompletion.create(model=model, messages=messages, max_tokens=4)
            text = response['choices'][0]['message']['content']
            temperature = temp
            #    filename = '%s_chat.txt' % time()
            #    if not os.path.exists('chat_logs'):
            #        os.makedirs('chat_logs')
            #    save_file('chat_logs/%s' % filename, str(messages) + '\n\n==========\n\n' + text)
            print(text)
            return text
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                print(f"Exiting due to an error in ChatGPT: {oops}")
                exit(1)
            print(f'Error communicating with OpenAI: "{oops}" - Retrying in {2 ** (retry - 1) * 5} seconds...')
            sleep(2 ** (retry - 1) * 5)

        
def search_implicit_db(line_vec):
    m = multiprocessing.Manager()
    lock = m.Lock()
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
    vdb = pinecone.Index("aetherius")
    try:
        with lock:
            print('implicit')
            results = vdb.query(vector=line_vec, filter={"memory_type": "implicit_long_term", "user": username}, top_k=7, namespace=f'{bot_name}')
            memories1 = load_conversation_implicit_long_term_memory(results)
            results = vdb.query(vector=line_vec, filter={"memory_type": "implicit_short_term"}, top_k=5, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}')
            memories2 = load_conversation_implicit_short_term_memory(results)
            memories = f'{memories1}\n{memories2}'
            print(memories)
            return memories
    except Exception as e:
        print(e)
        memories = "Error"
        return memories
        
        
def search_episodic_db(line_vec):
    m = multiprocessing.Manager()
    lock = m.Lock()
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
    vdb = pinecone.Index("aetherius")
    try:
        with lock:
            results = vdb.query(vector=line_vec, filter={
            "memory_type": "episodic", "user": username}, top_k=5, namespace=f'{bot_name}')
            memories = load_conversation_episodic_memory(results)
            return memories
    except Exception as e:
        print(e)
        memories = "Error"
        return memories
                
        
def search_flashbulb_db(line_vec):
    m = multiprocessing.Manager()
    lock = m.Lock()
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
    vdb = pinecone.Index("aetherius")
    try:
        with lock:
            results = vdb.query(vector=line_vec, filter={
            "memory_type": "flashbulb", "user": username}, top_k=5, namespace=f'{bot_name}')
            memories = load_conversation_flashbulb_memory(results)
            return memories
    except Exception as e:
        print(e)
        memories = "Error"
        return memories
        
        
def search_explicit_db(line_vec):
    m = multiprocessing.Manager()
    lock = m.Lock()
    username = open_file('./config/prompt_username.txt')
    bot_name = open_file('./config/prompt_bot_name.txt')
    vdb = pinecone.Index("aetherius")
    try:
        with lock:
            print('explicit')
            results = vdb.query(vector=line_vec, filter={"memory_type": "explicit_long_term", "user": username}, top_k=5, namespace=f'{bot_name}')
            memories1 = load_conversation_explicit_long_term_memory(results)
            results = vdb.query(vector=line_vec, filter={"memory_type": "explicit_short_term"}, top_k=5, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}')
            memories2 = load_conversation_explicit_short_term_memory(results)
            memories = f'{memories1}\n{memories2}'
            print(memories)
            return memories
    except Exception as e:
        print(e)
        memories = "Error"
        return memories
            
            
def google_search(query, my_api_key, my_cse_id, **kwargs):
    params = {
    "key": my_api_key,
    "cx": my_cse_id,
    "q": query,
    "num": 1,
    "snippet": True
    }
    response = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
    if response.status_code == 200:
        data = response.json()
        urls = [item['link'] for item in data.get("items", [])]  # Return a list of URLs
        return urls
    else:
        raise Exception(f"Request failed with status code {response.status_code}")
           
            
def split_into_chunks(text, chunk_size):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]


def chunk_text(text, chunk_size, overlap):
    chunks = []
    start = 0
    end = chunk_size
    while end <= len(text):
        chunks.append(text[start:end])
        start += chunk_size - overlap
        end += chunk_size - overlap
    if end > len(text):
        chunks.append(text[start:])
    return chunks


def chunk_text_from_url(url, chunk_size=1000, overlap=200):
    bot_name = open_file('./config/prompt_bot_name.txt')
    try:
        print("Scraping given URL, please wait...")
        bot_name = open_file('./config/prompt_bot_name.txt')
        username = open_file('./config/prompt_username.txt')
        vdb = pinecone.Index("aetherius")
        html = requests.get(url).text
        soup = BeautifulSoup(html, 'html.parser')
        texttemp = soup.get_text().strip()
        texttemp = texttemp.replace('\n', '').replace('\r', '')
        texttemp = '\n'.join(line for line in texttemp.splitlines() if line.strip())
        chunks = chunk_text(texttemp, chunk_size, overlap)
        weblist = list()
        for chunk in chunks:
            websum = list()
            websum.append({'role': 'system', 'content': "You are a data extractor. Your job is to take the given text from a webscrape, then highlight important or factual information. After useless data has been removed, you will then return all salient information.  Only use given info, do not generalize.  Use the format: [-{Semantic Tag}: {Article/Guide}]. Avoid using linebreaks inside of the article.  Lists should be made into continuous text form to avoid them."})
            websum.append({'role': 'user', 'content': f"ARTICLE CHUNK: {chunk}"})
            text = chatgpt35_completion(websum)
            paragraphs = text.split('\n\n')  # Split into paragraphs
            for paragraph in paragraphs:  # Process each paragraph individually, add a check to see if paragraph contained actual information.
                webcheck = list()
                weblist.append(url + ' ' + paragraph)
                webcheck.append({'role': 'system', 'content': f"You are an agent for an automated webscraping tool. You are one of many agents in a chain. Your task is to decide if the given text from a webscrape was scraped successfully. The scraped text should contain factual data or opinions. If the given data only consists of an error message or advertisements, skip it.  If the article was scraped successfully, print: YES.  If a web-search is not needed, print: NO."})
                webcheck.append({'role': 'user', 'content': f"Is the scraped information useful to an end-user? YES/NO: {paragraph}"})
                webyescheck = chatgptyesno_completion(webcheck)
                if webyescheck == 'YES':
                    print('---------')
                    print(url + ' ' + paragraph)
                    payload = list()
                    vector = gpt3_embedding(url + ' ' + paragraph)
                    timestamp = time()
                    timestring = timestamp_to_datetime(timestamp)
                    unique_id = str(uuid4())
                    metadata = {'bot': bot_name, 'time': timestamp, 'message': url + ' ' + paragraph,
                                'timestring': timestring, 'uuid': unique_id, "memory_type": "web_scrape"}
                    save_json(f'nexus/{bot_name}/{username}/web_scrape_memory_nexus/%s.json' % unique_id, metadata)
                    payload.append((unique_id, vector, {"memory_type": "web_scrape"}))
                    vdb.upsert(payload, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}')
                    payload.clear()
        table = weblist
        return table
    except Exception as e:
        print(e)
        table = "Error"
        return table
            
            
def search_and_chunk(query, my_api_key, my_cse_id, **kwargs):
    try:
        urls = google_search(query, my_api_key, my_cse_id, **kwargs)
        chunks = []
        for url in urls:
            chunks += chunk_text_from_url(url)
        return chunks
    except:
        print('Fail1')
         
            
def load_conversation_web_scrape_memory(results):
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
    try:
        result = list()
        for m in results['matches']:
            info = load_json(f'nexus/{bot_name}/{username}/web_scrape_memory_nexus/%s.json' % m['id'])
            result.append(info)
        ordered = sorted(result, key=lambda d: d['time'], reverse=False)  # sort them all chronologically
        messages = [i['message'] for i in ordered]
        return '\n'.join(messages).strip()
    except Exception as e:
        print(e)
        table = "Error"
        return table
            

def fail():
      #  print('')
    fail = "Not Needed"
    return fail
        
        
def search_webscrape_db(line):
    m = multiprocessing.Manager()
    lock = m.Lock()
    bot_name = open_file('./config/prompt_bot_name.txt')
    username = open_file('./config/prompt_username.txt')
    vdb = pinecone.Index("aetherius")
    try:
        with lock:
            line_vec = gpt3_embedding(line)
            results = vdb.query(vector=line_vec, filter={
        "memory_type": "web_scrape"}, top_k=30, namespace=f'short_term_memory_User_{username}_Bot_{bot_name}')
            table = load_conversation_web_scrape_memory(results)
            return table
    except Exception as e:
        print(e)
        table = "Error"
        return table