import readline
import time
from contextlib import redirect_stderr
from io import StringIO

from llama_cpp import Llama

SYSTEM = ['<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n', '<|eot_id|>']
USER = ['<|start_header_id|>user<|end_header_id|>\n', '<|eot_id|>']
ASSISTANT = ['<|start_header_id|>assistant<|end_header_id|>\n', '<|eot_id|>']


class ChatBot:
    def __init__(self, fp, system, initial=[], **kwargs):
        with redirect_stderr(StringIO()):  # to block llama.cpp output
            self.llm = Llama(model_path=fp, n_ctx=2048, seed=20)

        self.settings = kwargs
        self.prompt = SYSTEM[0] + system + SYSTEM[1]
        for a, b in initial:
            self.prompt += USER[0] + a + USER[1] + ASSISTANT[0] + b + ASSISTANT[1]

    def send(self, msg):
        if msg == 'DEBUG':
            # For example, in the middle of a conversation we can breakpoint()
            # and set `self.settings['temperature'] = 1.2` to adjust parameters.
            breakpoint()
            return

        if not msg:
            print('\033[F\r', end='')
        if msg:
            self.prompt += USER[0] + msg + USER[1]
        self.prompt += ASSISTANT[0]

        try:
            with redirect_stderr(StringIO()):  # to block llama.cpp output
                for result in self.llm(
                    self.prompt,
                    max_tokens=512,
                    stop=[ASSISTANT[1]],
                    stream=True,
                    temperature=1.2,
                    top_k=40,
                    top_p=0.95,
                    repeat_penalty=1.1,
                    **self.settings,
                ):
                    yield (tok := result['choices'][0]['text'])
                    self.prompt += tok
        except KeyboardInterrupt:
            pass

        self.prompt += ASSISTANT[1]


# Inspired by https://pogichat.vercel.app/
bot = ChatBot(
    '/home/kjc/Downloads/Meta-Llama-3-8B-Instruct.Q5_K_M.gguf',
    'You are pogi. pogi respond in single sentence and speak funny. pogi no think too much but much like emoji and hooman!!',
    [('hey', 'hey 🤩😁 wut u doin? 🤔')],
)

# bot = ChatBot(
#     '/home/kjc/Downloads/Meta-Llama-3-8B-Instruct.Q5_K_M.gguf',
#     "You are a helpful AI assistant. No yapping.", temperature=4.0
# )

while True:
    for tok in bot.send(input('> ')):
        print(tok, end='', flush=True)
    print()
