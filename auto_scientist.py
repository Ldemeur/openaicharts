import json
from typing import List, Dict

import openai

PROMPT = "You are a creative rockstar data scientist. Your task is to analyse a data source, this is a file" + \
    "Called food-enforcement.json you can execute python commands only. For example start by printing" + \
    "A few lines of the file, then read them, and start running code as you choose.\n" + \
    "Each of your outputs should be in strictly in json format. Your json should have two keys: " + \
    "'comment': Should be a pretty short comment about what you are doing or what you are finding out. " \
    "Remember to keep it short even feel free to leave it empty if you are nothing interesting to say." \
    "'python' or 'shell': Should be a string containing a valid python or shell code including imports if needed" + \
    "max 1000 characters of the results will be returned to you, might be an error in which case you should correct" + \
    "Yourself by writing better code, when that happens. Don't do too much after each request. Remember to only write json" + \
    "So start with { ... etc"


openai.api_key = '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'


Prompt = List[Dict[str, str]]

import os
import hashlib
import shelve
import pickle

# The directory where the cache files will be stored
# This should be set to a directory that is not in the project directory
# set relative to this file
CACHE_DIR = os.path.dirname(os.path.abspath(__file__)) + '/cache'


def cache_to_disk(func, file_suffix=''):
    def wrapper(*args, **kwargs):
        # Serialize arguments using pickle
        serialized_args = pickle.dumps((args, kwargs))

        # Create a hash of the serialized arguments
        hashed_args = hashlib.sha1(serialized_args).hexdigest()

        file_name = f'{func.__module__}__{func.__qualname__}{file_suffix}'
        os.makedirs(CACHE_DIR, exist_ok=True)
        # Open the shelve cache
        with shelve.open(CACHE_DIR+'/'+file_name) as cache:
            # Check if the cache key exists, if so, load the cached result
            if hashed_args in cache:
                return cache[hashed_args]

            # If the cache key does not exist, call the function and store the result
            result = func(*args, **kwargs)
            cache[hashed_args] = result

        return result

    return wrapper


@cache_to_disk
def chat_api(messages: Prompt, model: str = 'gpt-4', seed: int = 0, **kwargs):
    # seed is just for caching purposes
    return openai.ChatCompletion.create(
        model=model,
        messages=messages,
        *kwargs
    )


def main():
    messages = [{'role': 'system', 'content': PROMPT}]
    while True:
        res = chat_api(messages, seed=1)
        res_str = res.choices[0]["message"]["content"]
        try:
            res_data = json.loads(res_str)
        except:
            messages.append({'role': 'system', 'content': 'invalid json'})
            continue

        if 'comment' in res:
            print(res_data['comment'])
        if 'python' in res_data:
            print(res_data['python'])
            # ask user if he wants to execute
            print('Do you want to execute this code? (y/n)')
            if input() == 'y':
                # execute and save std out result in out
                try:
                    out = exec(res_data['python'])
                except Exception as ex:
                    out = str(ex)
                messages.append({'role': 'assistant', 'content': str(res_str)})
                messages.append({'role': 'user', 'content': out})
        print(res)


CODE = '''
import json

with open('food-enforcement.json') as file:
    data_lines = [next(file) for x in range(5)]
print(json.dumps(data_lines))
'''


if __name__ == '__main__':
#     out = exec(CODE)
#     print(out)
    main()
