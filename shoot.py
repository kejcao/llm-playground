import readline
import time

from llama_cpp import Llama

llm = Llama(
    model_path='/home/kjc/closet/llm/tinyllama-1.1b-intermediate-step-1431k-3t.Q8_0.gguf',
    seed=69,
    verbose=False,
)


def c(s, **kwargs):
    print(s, end='')
    for result in llm(s, max_tokens=512, stop=[], stream=True, **kwargs):
        print(result['choices'][0]['text'], end='', flush=True)
    print()


c(
    'A list of reasons never to go outside:\n\n1.',
    top_k=40,
    top_p=0.1,
    temperature=10,
)
