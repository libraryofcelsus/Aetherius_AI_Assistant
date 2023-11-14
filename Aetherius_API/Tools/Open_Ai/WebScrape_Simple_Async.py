import os
import sys
sys.path.insert(0, './Aetherius_API/resources')
from Open_Ai_GPT_35 import *
import asyncio
import aiofiles
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup
from uuid import uuid4


def timestamp_to_datetime(unix_time):
    datetime_obj = datetime.datetime.fromtimestamp(unix_time)
    datetime_str = datetime_obj.strftime("%A, %B %d, %Y at %I:%M%p %Z")
    return datetime_str


async def fetch_html(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

async def read_json(filepath):
    async with aiofiles.open(filepath, mode='r', encoding='utf-8') as f:
        return json.loads(await f.read())
        
async def chunk_text(text, chunk_size, overlap):
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
        
        
async def async_chunk_text_from_url(url, username, bot_name, chunk_size=380, overlap=40):
    try:
        print("Scraping given URL, please wait...")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                html = await response.text()

        soup = BeautifulSoup(html, 'html.parser')
        texttemp = soup.get_text().strip()
        texttemp = texttemp.replace('\n', '').replace('\r', '')
        texttemp = '\n'.join(line for line in texttemp.splitlines() if line.strip())
        chunks = await chunk_text(texttemp, chunk_size, overlap)
        weblist = list()

        try:
            with open('config/chatbot_settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
            host_data = settings.get('HOST_Oobabooga', '').strip()
            hosts = host_data.split(' ')
            num_hosts = len(hosts)
        except Exception as e:
            print(f"An error occurred while reading the host file: {e}")
        
        # Assuming host_queue is now an async queue
        host_queue = asyncio.Queue()
        for host in hosts:
            await host_queue.put(host)
            
        # Define the collection name
        collection_name = f"Bot_{bot_name}_External_Knowledgebase"
        try:
            collection_info = client.get_collection(collection_name=collection_name)
            print(collection_info)
        except:
            client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=embed_size, distance=Distance.COSINE),
        )
        
        
        async def process_chunk(chunk):
            # If wrapped_chunk_from_url is not asynchronous, you will need to modify it as well
            result = await wrapped_chunk_from_url(
                host_queue, chunk, collection_name, bot_name, username, embeddings, client, url
            )
            weblist.append(result['url'] + ' ' + result['processed_text'])
            print(result['url'] + '\n' + result['semantic_db_term'] + '\n' + result['processed_text'])
            return result
        
        # Use asyncio.gather to run all the coroutines concurrently
        await asyncio.gather(*(process_chunk(chunk) for chunk in chunks))
        
        table = weblist
        return
    except Exception as e:
        print(e)
        table = "Error"
        return


async def wrapped_chunk_from_url(host_queue, chunk, collection_name, bot_name, username, embeddings, client, url):
    try:
        # get a host
        host = await host_queue.get()
        
        # Assuming summarized_chunk_from_url is also async function
        result = await summarized_chunk_from_url(host, chunk, collection_name, bot_name, username, embeddings, client, url)
        
        # release the host
        await host_queue.put(host)
        return result
    except Exception as e:
        print(e)


async def summarized_chunk_from_url(host, chunk, collection_name, bot_name, username, embeddings, client, url):
    try:
        weblist = list()
        websum = list()
        chunk = text

        webyescheck = 'yes'
        if 'no webscrape' in text.lower():
            text = chunk
            print('---------')
            print('Summarization Failed')
            pass
        if 'no article' in text.lower():
            text = chunk
            print('---------')
            print('Summarization Failed')
            pass
        if 'you are a text' in text.lower():
            text = chunk
            print('---------')
            print('Summarization Failed')
            pass
        if 'no summary' in text.lower():
            text = chunk
            print('---------')
            print('Summarization Failed')
            pass  
        if 'i am an ai' in text.lower():
            text = chunk
            print('---------')
            print('Summarization Failed')
            pass                
        else:
            if 'yes' in webyescheck.lower():
                semanticterm = list()
                semanticterm.append({'role': 'system', 'content': f"MAIN SYSTEM PROMPT: You are a bot responsible for taging articles with a title for database queries.  Your job is to read the given text, then create a title in question form representative of what the article is about, focusing on its main subject.  The title should be semantically identical to the overview of the article and not include extraneous info.  The article is from the URL: {url}. Use the format: [<TITLE IN QUESTION FORM>].\n\n"})
                semanticterm.append({'role': 'user', 'content': f"ARTICLE: {text}\n\n"})
                semanticterm.append({'role': 'user', 'content': f"SYSTEM: Create a short, single question that encapsulates the semantic meaning of the Article.  Use the format: [<QUESTION TITLE>].  Please only print the title, it will be directly input in front of the article.[/INST]\n\nASSISTANT: Sure! Here's the summary of the webscrape: "})
                prompt = ''.join([message_dict['content'] for message_dict in semanticterm])
                semantic_db_term = Webscrape_Call(prompt, username, bot_name)
                if 'cannot provide a summary of' in semantic_db_term.lower():
                    semantic_db_term = 'Tag Censored by Model'
                print('---------')
                weblist.append(url + ' ' + text)
                print(url + '\n' + semantic_db_term + '\n' + text)
                payload = list()
                timestamp = time()
                timestring = timestamp_to_datetime(timestamp)
                    # Create the collection only if it doesn't exist

                vector1 = embeddings(semantic_db_term + ' ' + text)
                #    embedding = model.encode(query)
                unique_id = str(uuid4())
                point_id = unique_id + str(int(timestamp))
                metadata = {
                    'bot': bot_name,
                    'user': username,
                    'time': timestamp,
                    'source': url,
                    'tag': semantic_db_term,
                    'message': text,
                    'timestring': timestring,
                    'uuid': unique_id,
                    'memory_type': 'Web_Scrape',
                }
                client.upsert(collection_name=collection_name,
                                     points=[PointStruct(id=unique_id, vector=vector1, payload=metadata)]) 
                payload.clear()           
            else:
                print('---------')
                print(f"\n\n\nFAILED ARTICLE: {text}")
                print(f'\nERROR MESSAGE FROM BOT: {webyescheck}\n\n\n')  
        table = weblist
        return table                
    except Exception as e:
        print(e)
        table = "Error"
        return table  