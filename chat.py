import json
import os
import readline
import subprocess
import tempfile
from contextlib import redirect_stderr
from datetime import datetime
from io import StringIO
from pathlib import Path

from jinja2 import Environment
from llama_cpp import Llama


class ChatBot:
    def __init__(self, fp, messages={}, **kwargs):
        self.env = Environment()
        self.env.globals['strftime_now'] = lambda fmt: datetime.now().strftime(fmt)

        data = json.load(open('models.json'))
        for m in data['models']:
            if m['name'] in Path(fp).name:
                self.template = m['chat_template']
                self.stop_tokens = m['stop_tokens']
                break
        else:  # no break
            raise RuntimeError('no matching model ' + Path(fp).name)

        self.settings = {
            'temperature': 0.1,
            'top_p': 0.1,
        } | kwargs

        with redirect_stderr(StringIO()):  # to block llama.cpp output
            self.llm = Llama(model_path=fp, n_ctx=16384)
        self.messages = messages

    def render(self, messages):
        return self.env.from_string(self.template).render(messages=messages)

    def send(self, msg):
        if msg == 'DEBUG':
            breakpoint()
            return

        self.messages.append({'role': 'user', 'content': msg})

        canary = [{'role': 'assistant', 'content': 'APPEND_CANARY'}]
        prompt = self.render(self.messages + canary)
        prompt = prompt[: prompt.index('APPEND_CANARY')]
        # print(prompt)  # for debugging
        try:
            response = ''
            with redirect_stderr(StringIO()):  # to block llama.cpp output
                for result in self.llm(
                    prompt,
                    max_tokens=512,
                    stop=self.stop_tokens,
                    stream=True,
                    **self.settings,
                ):
                    yield (tok := result['choices'][0]['text'])
                    response += tok
            self.messages.append({'role': 'assistant', 'content': response})
        except KeyboardInterrupt:
            pass


# Inspired by https://pogichat.vercel.app/
bot = ChatBot(
    '/home/kjc/Downloads/granite-3.2-2b-instruct-Q4_K_M.gguf',
    [
        {
            'role': 'system',
            'content': 'You are pogi. pogi respond in single sentence and speak funny. pogi no think too much but much like emoji and hooman!!',
        },
        {'role': 'user', 'content': 'hey'},
        {'role': 'assistant', 'content': 'hey 🤩😁 wut u doin? 🤔'},
    ],
)


def read(p):
    if (s := input(p)) == 'E':
        with tempfile.NamedTemporaryFile(suffix='.tmp') as tf:
            subprocess.run([os.environ['EDITOR'], tf.name])
            with open(tf.name, 'r') as f:
                t = f.read()
                print('\033[F' + '\n'.join(p + l for l in t.splitlines()))
                return t
    return s


while True:
    for tok in bot.send(read('> ')):
        print(tok, end='', flush=True)
    print()
