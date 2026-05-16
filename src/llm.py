"""
RoboCop LLM

Handles conversation with the local Ollama model.
"""

import requests
from config import OLLAMA_URL, OLLAMA_MODEL, SYSTEM_PROMPT

# Rolling conversation history: list of (role, message) tuples.
# Kept to 20 exchanges so the prompt doesn't exceed the model's
# context window (~4096 tokens for Qwen 2.5 3B).
_history = []
MAX_HISTORY = 20


def init():
    """Warm up Ollama by loading the model into GPU memory.

    This MUST be called before loading Whisper or Piper. On the Jetson,
    CPU and GPU share 8GB of unified memory. Ollama needs a large
    contiguous block for CUDA allocation (~2GB). If Whisper/Piper load
    first, they fragment the memory pool and Ollama can't find a big
    enough block — resulting in a 500 error.
    """
    print('Warming up Ollama (reserving GPU memory)...')
    try:
        r = requests.post(OLLAMA_URL, json={
            'model': OLLAMA_MODEL,
            'prompt': 'Hi',
            'stream': False,
            'options': {'num_predict': 1}
        }, timeout=60)
        r.raise_for_status()
        print(f'Ollama ready ({OLLAMA_MODEL} loaded).')
    except Exception as e:
        print(f'WARNING: Ollama warmup failed: {e}')
        print('LLM responses may fail. Is Ollama running?')


def _build_prompt(user_message):
    """Build a prompt string from system prompt, history, and new message."""
    prompt = f'System: {SYSTEM_PROMPT}\n\n'
    for role, msg in _history:
        if role == 'user':
            prompt += f'Z: {msg}\n'
        else:
            prompt += f'RoboCop: {msg}\n'
    prompt += f'Z: {user_message}\nRoboCop:'
    return prompt


def ask(user_message):
    """Send a message to Ollama and return the response.

    Automatically manages conversation history.
    """
    prompt = _build_prompt(user_message)

    try:
        response = requests.post(OLLAMA_URL, json={
            'model': OLLAMA_MODEL,
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': 0.7,
                'num_predict': 100,
            }
        }, timeout=30)
        response.raise_for_status()
        reply = response.json()['response'].strip()
    except requests.exceptions.RequestException as e:
        reply = f'Sorry, I could not think of a response. Error: {e}'

    # Update history
    _history.append(('user', user_message))
    _history.append(('assistant', reply))
    if len(_history) > MAX_HISTORY:
        _history[:] = _history[-MAX_HISTORY:]

    return reply
