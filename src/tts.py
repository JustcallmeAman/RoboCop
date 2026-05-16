"""
RoboCop Text-to-Speech

Handles Piper voice synthesis and Bluetooth audio playback.
"""

import subprocess
import wave
import tempfile
import os

from config import PIPER_VOICE, AUDIO_SINK, TTS_PADDING_SECONDS

_piper_voice = None


def init():
    """Load the Piper voice model.

    Call this AFTER Ollama and Whisper are loaded. Piper runs on CPU
    so it doesn't need contiguous GPU memory, but loading it still
    allocates memory that could fragment the pool if done too early.
    """
    global _piper_voice

    print('Loading Piper voice...')
    from piper import PiperVoice
    _piper_voice = PiperVoice.load(PIPER_VOICE)
    print('Piper ready.')


def speak(text):
    """Convert text to speech and play through the Shokz headphones.

    Adds silence padding before and after the audio. Bluetooth has a
    codec startup delay — the first ~300ms get swallowed while the
    link activates. The stream also closes before the last chunk
    finishes playing. Padding with silence on both ends ensures no
    speech gets trimmed.
    """
    raw_path = tempfile.mktemp(suffix='.wav')
    padded_path = raw_path + '.padded.wav'

    try:
        # Generate speech
        with wave.open(raw_path, 'wb') as f:
            _piper_voice.synthesize_wav(text, f)

        # Read back and add silence padding
        with wave.open(raw_path, 'rb') as src:
            params = src.getparams()
            frames = src.readframes(src.getnframes())

        pad_samples = int(params.framerate * TTS_PADDING_SECONDS)
        silence = b'\x00\x00' * pad_samples * params.nchannels

        with wave.open(padded_path, 'wb') as dst:
            dst.setparams(params)
            dst.writeframes(silence + frames + silence)

        # Play through Bluetooth
        subprocess.run(
            ['paplay', '--device=' + AUDIO_SINK, padded_path],
            check=True
        )
    finally:
        if os.path.exists(raw_path):
            os.unlink(raw_path)
        if os.path.exists(padded_path):
            os.unlink(padded_path)
