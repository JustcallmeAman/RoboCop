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
import vision

# ============================================================
# Initialize — ORDER MATTERS for GPU memory
# ============================================================
# On the Jetson, CPU and GPU share 8GB of unified memory.
# Ollama needs a large contiguous block for CUDA allocation.
# If Whisper/Piper load first, they fragment the memory pool.
# Solution: Ollama first, then Whisper, then Piper.
# Vision runs on the OAK-D Lite's MyriadX — no Jetson cost.

llm.init()      # 1. Reserve GPU memory for Qwen 2.5 3B
stt.init()      # 2. Load Whisper (CPU, won't fragment GPU)
tts.init()      # 3. Load Piper voice (CPU)
vision.init()   # 4. Start OAK-D Lite (runs on-camera, no Jetson cost)

print()
print('=' * 50)
print('  RoboCop Phase 2 — Agent Loop + Vision')
print('  Speak and I will respond in your ear.')
print('  I can also see through the OAK-D Lite.')
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

        # Snapshot what the camera sees while we think
        scene = vision.describe_scene(duration=0.5)
        if scene:
            print(f'[Camera: {scene}]')

        print('Thinking...')
        start = time.time()
        context = user_text
        if scene:
            context = f'[You can currently see: {scene}] {user_text}'
        response_text = llm.ask(context)
        elapsed = time.time() - start
        print(f'RoboCop: {response_text}')
        print(f'({elapsed:.1f}s)')

        tts.speak(response_text)
        print()

except KeyboardInterrupt:
    print()
    vision.stop()
    print('RoboCop signing off. Take care, Z.')
