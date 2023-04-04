import datetime
import hashlib
import json
import os
from typing import List

from utils import Prompt, chat_api, capture_output

MAX_OUTPUT_LENGTH = 600

PROMPT = "You are a creative rockstar data scientist. Your task is to analyse a data source, this is a file " \
    "called FILENAME you can execute python commands only. " \
    "Each of your outputs should be in strictly in json format. Your json must have two keys: " \
    "'comment': should be a pretty short comment about what you are doing or what you are finding out " \
    " (remember to keep it short even feel free to leave it empty if you are nothing interesting to say), " \
    "'python': should be a string containing a valid python code including imports if needed, " \
    " while keeping it short do use newlines in between statements and use 2 spaces for indentation. " \
    f"max {MAX_OUTPUT_LENGTH} characters of the results will be returned to you, " \
    f"might be an error in which case you should correct " \
    "yourself by writing better code. Don't do too much after each request. If something does not work feel free " \
    "to try something totally different instead. Be clever and creative in your analysis. Remember to only " \
    "write json. Start with { ... etc. Use print statements, as we do not print your last commands like in notebooks" \
    "If you are finished, just write 'exit', nothing else, and we will stop."

PROMPT_SUMMARY = "Now please write a summary of the analysis above. Including the most interesting insights." \
                 " Do not write your output in json anymore, instead write in markdown."


def next_step(full_prompt_history: Prompt, exec_variables: dict):
    new_prompt_messages = []

    valid_message = False
    while not valid_message:
        res = chat_api(full_prompt_history + new_prompt_messages, seed=0)
        res_str = res.choices[0]["message"]["content"]
        new_prompt_messages.append({'role': 'assistant', 'content': str(res_str)})

        if res_str == 'exit':
            return None

        try:
            res_data = json.loads(res_str)
            if 'exit' in res_data.values():
                print(res_data)
                return None
            valid_message = True
        except Exception as ex:
            print(res_str)
            msg = f'Please respond with a valid json or exit (error while parsing json: ${str(ex)})'
            print("# Invalid json:")
            print(msg)
            new_prompt_messages.append(
                {'role': 'system', 'content': f'Please always only respond with a valid json (${str(ex)})'}
            )

    # noinspection PyUnboundLocalVariable
    report_item = res_data.copy()

    if 'comment' in res_data:
        print("## Extracting comment:")
        print(res_data['comment'])
    if 'python' in res_data:
        print("## Extracting python code:")
        print('----------------------------------------')
        print(res_data['python'])
        print('----------------------------------------')
        print('## Do you want to execute this code? (y/N)')
        if input() in ['y', 'Y']:
            try:
                with capture_output() as (stdout_buf, stderr_buf):
                    exec(res_data['python'], exec_variables)
                out = ''
            except Exception as ex:
                out = f"Got exception: ${ex}"
            finally:
                stderr = stderr_buf.getvalue()
                stdout = stdout_buf.getvalue()
                if stderr:
                    # noinspection PyUnboundLocalVariable
                    out += f'error:\n{stderr[:round(MAX_OUTPUT_LENGTH/3)]}\n'
            if stdout:
                out += f'output:\n{stdout}'

            out = out[:MAX_OUTPUT_LENGTH]
            print("## Output:")
            print(out)
            new_prompt_messages.append({'role': 'user', 'content': out})
            report_item['output'] = out
    return new_prompt_messages, report_item


def main():
    print("What file do you want to analyse? (press enter for default: food-enforcement.json)\n > ", end='')
    file_name = input().strip()
    if not file_name:
        file_name = 'food-enforcement.json'
    messages = [{'role': 'system', 'content': PROMPT.replace('FILENAME', file_name)}]
    exec_variables = {}
    report_items = []
    try:
        while True:
            res = next_step(messages, exec_variables)
            if res is None:
                break
            new_messages, report_item = res
            messages.extend(new_messages)
            report_items.append(report_item)
    finally:
        messages.append({'role': 'system', 'content': PROMPT_SUMMARY})
        res = chat_api(messages, seed=0)
        summary = res.choices[0]["message"]["content"]
        save_report(report_items, summary, file_name)


REPORT_DIR = os.path.dirname(os.path.abspath(__file__)) + '/reports'


def save_report(history: List[dict], summary, analyzed_file_name):
    # generate a short random file name starting with current date time
    file_name = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name += hashlib.sha1(os.urandom(32)).hexdigest()[:8]
    os.makedirs(REPORT_DIR, exist_ok=True)
    # save report as markdown file
    with open(REPORT_DIR+'/'+file_name+'.md', 'w') as file:
        file.write('# Report\n')
        file.write(f'File: *{analyzed_file_name}*\n\n')
        for item in history:
            if 'comment' in item:
                file.write(item['comment'])
                file.write('\n\n')
            if 'python' in item:
                file.write('```python\n')
                file.write(item['python'].strip())
                file.write('\n```\n\n')
            if 'output' in item:
                file.write('```json\n')
                file.write(item['output'])
                file.write('\n```\n\n')
        file.write('# Summary\n')
        file.write(summary)
    print(f'Report saved to {REPORT_DIR}/{file_name}.md')


if __name__ == '__main__':
    main()
