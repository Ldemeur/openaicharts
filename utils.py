import hashlib
import os
import pickle
import shelve
import sys
from typing import Dict
from typing import List
import io
import contextlib

import openai

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


@contextlib.contextmanager
def capture_output():
    # create two in-memory io streams to replace stdout and stderr
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()

    # temporarily replace stdout and stderr with the in-memory buffers
    original_stdout, original_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = stdout_buffer, stderr_buffer

    try:
        # yield control back to the calling code, which can now execute
        # while any stdout and stderr output is captured in the in-memory buffers
        yield stdout_buffer, stderr_buffer

    finally:
        # restore the original stdout and stderr
        sys.stdout, sys.stderr = original_stdout, original_stderr


# Load from environment variable
openai.api_key = os.environ.get('OPENAI_API_KEY')


Prompt = List[Dict[str, str]]


@cache_to_disk
def chat_api(messages: Prompt, model: str = 'gpt-4', seed: int = 0, **kwargs):
    print("Waiting for response from OpenAI...")
    # seed is just for caching purposes
    return openai.ChatCompletion.create(
        model=model,
        messages=messages,
        *kwargs
    )
