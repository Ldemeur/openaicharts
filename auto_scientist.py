import io
import json
import sys
from typing import List, Dict

import os
import hashlib
import shelve
import pickle

import openai

PROMPT = "You are a creative rockstar data scientist. Your task is to analyse a data source, this is a file" \
    "Called food-enforcement.json you can execute python commands only. For example start by printing" \
    "A few lines of the file, then read them, and start running code as you choose.\n" \
    "Each of your outputs should be in strictly in json format. Your json should have two keys: " \
    "'comment': Should be a pretty short comment about what you are doing or what you are finding out. " \
    "Remember to keep it short even feel free to leave it empty if you are nothing interesting to say." \
    "'python' or 'shell': Should be a string containing a valid python or shell code including imports if needed" \
    "max 1000 characters of the results will be returned to you, might be an error in which case you should correct" \
    "Yourself by writing better code, when that happens. Don't do too much after each request. Remember to only write" \
    " json. S start with { ... etc. Do use print statements, as we do not print your last commands like in notebooks"


openai.api_key = 'sk-...'


Prompt = List[Dict[str, str]]


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
        res = chat_api(messages, seed=0)
        res_str = res.choices[0]["message"]["content"]
        messages.append({'role': 'assistant', 'content': str(res_str)})
        print("# Assistant:")
        print(res_str)
        try:
            res_data = json.loads(res_str)
        except Exception as ex:
            msg = f'Please always only respond with a valid json (${str(ex)})'
            print("# System:")
            print(msg)
            messages.append({'role': 'system', 'content': f'Please always only respond with a valid json (${str(ex)})'})
            continue

        if 'comment' in res_data:
            print("## Extracting comment:")
            print(res_data['comment'])
        if 'python' in res_data:
            print("## Extracting python code:")
            print(res_data['python'])
            # ask user if he wants to execute
            print('## Do you want to execute this code? (y/n)')
            if input() == 'y':
                # execute and save std out result in out
                try:
                    # Save the current stdout and stderr
                    original_stdout = sys.stdout
                    original_stderr = sys.stderr

                    # Create a StringIO buffer to store the output and error
                    captured_stdout = io.StringIO()
                    captured_stderr = io.StringIO()

                    # Redirect stdout and stderr to the buffer
                    sys.stdout = captured_stdout
                    sys.stderr = captured_stderr
                    exec(res_data['python'])
                    out = ''
                except Exception as ex:
                    out = f"Got exception: ${ex}"
                finally:
                    # Restore the original stdout and stderr
                    sys.stdout = original_stdout
                    sys.stderr = original_stderr

                    # Get the output and error as strings
                    output = captured_stdout.getvalue()
                    error = captured_stderr.getvalue()

                    # Close the StringIO buffer
                    stdout = captured_stdout.getvalue()
                    stderr = captured_stderr.getvalue()
                    captured_stdout.close()
                    captured_stderr.close()
                if stdout:
                    out += f'\n\noutput:\n{stdout}'
                if stderr:
                    out += f'\n\nerror:\n{stderr}'
                print("# User:")
                print(out)
                messages.append({'role': 'user', 'content': out})

if __name__ == '__main__':
   main()
