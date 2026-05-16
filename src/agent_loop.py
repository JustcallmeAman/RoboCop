#!/usr/bin/env python3
"""
RoboCop Phase 1 Agent Loop

The core conversation loop for your wearable AI companion.

Flow: You speak -> ReSpeaker captures -> Whisper transcribes ->
      Ollama thinks -> Piper speaks -> Shokz plays in your ear

Press Ctrl+C to exit.
"""

import sys
import os
import time

# Allow imports from src/ when running as a script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import llm
import stt
import tts

# ============================================================
# Initialize — ORDER MATTERS for GPU memory
# ============================================================
# On the Jetson, CPU and GPU share 8GB of unified memory.
# Ollama needs a large contiguous block for CUDA allocation.
# If Whisper/Piper load first, they fragment the memory pool.
# Solution: Ollama first, then Whisper, then Piper.

llm.init()      # 1. Reserve GPU memory for Qwen 2.5 3B
stt.init()      # 2. Load Whisper (CPU, won't fragment GPU)
tts.init()      # 3. Load Piper voice (CPU)

print()
print('=' * 50)
print('  RoboCop Phase 1 — Agent Loop')
print('  Speak and I will respond in your ear.')
print('  Press Ctrl+C to exit.')
print('=' * 50)
print()

# ============================================================
# Main loop
# ============================================================

try:
    while True:
        print('Listening... (speak now)')

        user_text = stt.listen()

        if not user_text:
            print('(silence)')
            print()
            continue

        print(f'You: {user_text}')

        print('Thinking...')
        start = time.time()
        response_text = llm.ask(user_text)
        elapsed = time.time() - start
        print(f'RoboCop: {response_text}')
        print(f'({elapsed:.1f}s)')

        tts.speak(response_text)
        print()

except KeyboardInterrupt:
    print()
    print('RoboCop signing off. Take care, Z.')
