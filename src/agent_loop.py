#!/usr/bin/env python3
"""
RoboCop Phase 1 Agent Loop
The first real conversation with your wearable AI.

Flow: You speak -> ReSpeaker captures -> Whisper transcribes ->
      Ollama thinks -> Piper speaks -> Shokz plays in your ear

Press Ctrl+C to exit.
"""

import subprocess
import requests
import wave
import tempfile
import os
import time
import struct

# ============================================================
# Configuration
# ============================================================

MIC_DEVICE = 'plughw:2,0'
SAMPLE_RATE = 16000
RECORD_SECONDS = 5
CHANNELS = 1

WHISPER_MODEL = 'small'
WHISPER_DEVICE = 'cpu'
WHISPER_COMPUTE = 'int8'

OLLAMA_URL = 'http://127.0.0.1:11434/api/generate'
OLLAMA_MODEL = 'qwen2.5:3b'

PIPER_VOICE = '/home/z/.local/share/piper_voices/en_GB-alba-medium.onnx'

AUDIO_SINK = 'bluez_output.A0_0C_E2_D5_CE_ED.headset-head-unit'

SYSTEM_PROMPT = """You are RoboCop, a wearable personal AI companion worn by Z.
You speak through bone conduction headphones directly into Z's ear.

Rules:
- Keep responses to 1-3 sentences maximum. You are a whisper in the ear, not a lecturer.
- Be warm, direct, and genuine. You are a friend and mentor, not an assistant.
- You can hear what Z says and what's happening around them.
- If Z seems stressed or anxious, acknowledge it gently.
- Be casual. No corporate speak. Talk like a real person.
"""


# ============================================================
# Initialize models — ORDER MATTERS for memory
# ============================================================
# On the Jetson, CPU and GPU share 8GB of unified memory.
# Ollama needs a large CONTIGUOUS block for GPU allocation.
# If we load Whisper/Piper first, they fragment the memory pool
# and Ollama can't find a big enough block -> 500 error.
#
# Solution: warm up Ollama FIRST (grabs its GPU block while
# memory is clean), then load Whisper/Piper into whatever's left.
# CPU allocations don't need contiguous blocks, so this works.

print('Warming up Ollama (reserving GPU memory)...')
try:
    r = requests.post(OLLAMA_URL, json={
        'model': OLLAMA_MODEL,
        'prompt': 'Hi',
        'stream': False,
        'options': {'num_predict': 1}
    }, timeout=60)
    r.raise_for_status()
    print('Ollama ready (GPU memory reserved).')
except Exception as e:
    print(f'WARNING: Ollama warmup failed: {e}')
    print('LLM responses may fail. Is Ollama running?')

print('Loading Whisper model...')
from faster_whisper import WhisperModel
whisper_model = WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE)
print('Whisper ready.')

print('Loading Piper voice...')
from piper import PiperVoice
piper_voice = PiperVoice.load(PIPER_VOICE)
print('Piper ready.')

print()
print('=' * 50)
print('  RoboCop Phase 1 — Agent Loop')
print('  Speak and I will respond in your ear.')
print('  Press Ctrl+C to exit.')
print('=' * 50)
print()


def record_audio(filepath, seconds=RECORD_SECONDS):
    """Record audio from the ReSpeaker microphone."""
    subprocess.run([
        'arecord', '-D', MIC_DEVICE,
        '-f', 'S16_LE', '-r', str(SAMPLE_RATE),
        '-c', str(CHANNELS), '-d', str(seconds),
        '-q', filepath
    ], check=True)


def transcribe(filepath):
    """Transcribe audio file using Whisper."""
    segments, info = whisper_model.transcribe(filepath)
    return ' '.join([seg.text for seg in segments]).strip()


def ask_ollama(user_message, conversation_history):
    """Send a message to Ollama and get a response."""
    prompt = f'System: {SYSTEM_PROMPT}\n\n'
    for role, msg in conversation_history:
        if role == 'user':
            prompt += f'Z: {msg}\n'
        else:
            prompt += f'RoboCop: {msg}\n'
    prompt += f'Z: {user_message}\nRoboCop:'

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
        return response.json()['response'].strip()
    except requests.exceptions.RequestException as e:
        return f'Sorry, I could not think of a response. Error: {e}'


def speak(text):
    """Convert text to speech with Piper and play through Shokz.

    Adds silence padding at the start and end of the audio.
    Bluetooth audio has a codec startup delay — the first ~300ms
    get swallowed while the link activates. Similarly, the stream
    closes before the last chunk finishes playing. Padding with
    silence on both ends ensures no speech gets trimmed.
    """
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        tmp_path = tmp.name
    try:
        # Generate speech into a temporary file
        with wave.open(tmp_path, 'wb') as f:
            piper_voice.synthesize_wav(text, f)

        # Read it back, add silence padding, write padded file
        padded_path = tmp_path + '.padded.wav'
        with wave.open(tmp_path, 'rb') as src:
            params = src.getparams()
            frames = src.readframes(src.getnframes())

        # 400ms of silence on each side (16-bit mono at 16kHz)
        pad_samples = int(params.framerate * 0.4)
        silence = b'\x00\x00' * pad_samples * params.nchannels

        with wave.open(padded_path, 'wb') as dst:
            dst.setparams(params)
            dst.writeframes(silence + frames + silence)

        subprocess.run([
            'paplay', '--device=' + AUDIO_SINK, padded_path
        ], check=True)
        os.unlink(padded_path)
    finally:
        os.unlink(tmp_path)


# ============================================================
# Main loop
# ============================================================

conversation_history = []

try:
    while True:
        print('Listening... (speak now)')
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            audio_path = tmp.name

        try:
            record_audio(audio_path)
            print('Transcribing...')
            user_text = transcribe(audio_path)
        finally:
            os.unlink(audio_path)

        if not user_text:
            print('(silence)')
            print()
            continue

        print(f'You: {user_text}')

        print('Thinking...')
        start = time.time()
        response_text = ask_ollama(user_text, conversation_history)
        elapsed = time.time() - start
        print(f'RoboCop: {response_text}')
        print(f'({elapsed:.1f}s)')

        conversation_history.append(('user', user_text))
        conversation_history.append(('assistant', response_text))
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]

        speak(response_text)
        print()

except KeyboardInterrupt:
    print()
    print('RoboCop signing off. Take care, Z.')
