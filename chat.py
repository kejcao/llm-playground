import os
import re
import readline
import subprocess
import tempfile
from contextlib import redirect_stderr
from io import StringIO

from llama_cpp import Llama

# # Gemma
# template = """\
# <start_of_turn>user
# {{ if .System }}{{ .System }} {{ end }}{{ .Prompt }}<end_of_turn>
# <start_of_turn>model
# {{ .Response }}<end_of_turn>
# """
# stopwords = ['<end_of_turn>']

# # Llama 3
# template = '''\
# {{ if .System }}<|begin_of_text|><|start_header_id|>system<|end_header_id|>
# {{ .System }}<|eot_id|>{{ end }}{{ if .Prompt }}<|start_header_id|>user<|end_header_id|>
# {{ .Prompt }}<|eot_id|>{{ end }}<|start_header_id|>assistant<|end_header_id|>
# {{ .Response }}<|eot_id|>
# '''
# stopwords = ['<|end_header_id|>', '<|eot_id|>']

# Qwen
template = """\
{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>{{ end }}<|im_start|>user
{{ .Prompt }}<|im_end|>
<|im_start|>assistant
"""
stopwords = ['<|im_end|>', '<|im_start|>']


class ChatBot:
    def __init__(self, fp, system, initial=[], **kwargs):
        with redirect_stderr(StringIO()):  # to block llama.cpp output
            self.llm = Llama(model_path=fp, n_ctx=4096)

        self.settings = {
            'temperature': 1.2,
            'top_k': 40,
            'top_p': 0.95,
            'repeat_penalty': 1.1,
        } | kwargs

        self.system_prompt = system
        self.prompt = ''

    def send(self, msg):
        if msg == 'DEBUG':
            # For example, in the middle of a conversation we can breakpoint()
            # and set `self.settings['temperature'] = 1.2` to adjust parameters.
            breakpoint()
            return

        if msg.startswith('https://www.youtube.com/watch?v='):
            import subtitles

            subs = subtitles.get_subtitles(msg)
            msg = (
                'Summarize this transcription of a YouTube video. Retain most important information only.\n\n'
                + subs.replace('\n', ' ')
            )
            print('\nsubtitles:\n\n' + subs + '\n')

        def f(text, keyword, replacement):
            tmp = re.sub(
                f'{{{{ if .{keyword} }}}}(.*?)({{{{ .{keyword} }}}})(.*?){{{{ end }}}}',
                lambda m: m.group(1) + replacement + m.group(3),
                text,
                flags=re.S,
            )
            return re.sub(f'{{{{ .{keyword} }}}}', replacement, tmp)

        self.prompt += template
        self.prompt = f(self.prompt, 'System', self.system_prompt)
        self.system_prompt = ''

        self.prompt = f(self.prompt, 'Prompt', msg)
        feed = self.prompt[: self.prompt.find('{{')]

        try:
            response = ''
            with redirect_stderr(StringIO()):  # to block llama.cpp output
                for result in self.llm(
                    feed,
                    max_tokens=512,
                    stop=stopwords,
                    stream=True,
                    **self.settings,
                ):
                    yield (tok := result['choices'][0]['text'])
                    response += tok
        except KeyboardInterrupt:
            pass

        self.prompt = f(self.prompt, 'Response', response)


# # Inspired by https://pogichat.vercel.app/
# bot = ChatBot(
#     '/home/kjc/closet/llm/Llama-3-8B-Instruct-abliterated-v2_q5.gguf',
#     'You are pogi. pogi respond in single sentence and speak funny. pogi no think too much but much like emoji and hooman!!',
#     [('hey', 'hey 🤩😁 wut u doin? 🤔')],
# )

bot = ChatBot(
    '/home/kjc/closet/llm/qwen2-1_5b-instruct-q4_k_m.gguf',
    'You are a helpful AI assistant.',
)


def read(p):
    if (s := input(p)) == 'E':
        with tempfile.NamedTemporaryFile(suffix='.tmp') as tf:
            try:
                editor = os.environ['EDITOR']
            except KeyError:
                editor = 'vim'
            subprocess.run([editor, tf.name])

            with open(tf.name, 'r') as f:
                t = f.read()
                print('\033[F' + '\n'.join(p + l for l in t.splitlines()))
                return t
    return s


while True:
    for tok in bot.send(read('> ')):
        print(tok, end='', flush=True)
    print()
