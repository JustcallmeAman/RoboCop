"""
RoboCop Speech-to-Text

Handles mic recording, silence detection, and Whisper transcription.
"""

import subprocess
import struct
import tempfile
import os

from config import (
    SAMPLE_RATE, RECORD_SECONDS, CHANNELS,
    SILENCE_THRESHOLD, WHISPER_MODEL, WHISPER_DEVICE, WHISPER_COMPUTE,
    detect_mic_device,
)

_whisper_model = None
_mic_device = None


def init():
    """Load Whisper model and detect microphone.

    Call this AFTER warming up Ollama — on the Jetson, Ollama needs to
    grab its contiguous GPU memory block before other models load.
    """
    global _whisper_model, _mic_device

    _mic_device = detect_mic_device()

    print('Loading Whisper model...')
    from faster_whisper import WhisperModel
    _whisper_model = WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE)
    print('Whisper ready.')


def record(seconds=RECORD_SECONDS):
    """Record audio from the ReSpeaker and return the file path.

    Caller is responsible for deleting the file when done.
    """
    tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    tmp.close()

    subprocess.run([
        'arecord', '-D', _mic_device,
        '-f', 'S16_LE', '-r', str(SAMPLE_RATE),
        '-c', str(CHANNELS), '-d', str(seconds),
        '-q', tmp.name
    ], check=True)

    return tmp.name


def is_speech(filepath):
    """Check if an audio file contains speech by measuring RMS energy.

    Whisper hallucinates on near-silence — it'll confidently transcribe
    "You" or "Thank you" from pure noise. Checking energy first avoids
    wasting time on empty audio and prevents ghost transcriptions.

    Returns True if the audio is loud enough to be speech.
    """
    with open(filepath, 'rb') as f:
        # Skip the 44-byte WAV header
        f.seek(44)
        raw = f.read()

    if len(raw) < 2:
        return False

    # Unpack 16-bit signed samples and compute RMS
    n_samples = len(raw) // 2
    samples = struct.unpack(f'<{n_samples}h', raw[:n_samples * 2])
    rms = (sum(s * s for s in samples) / n_samples) ** 0.5

    return rms > SILENCE_THRESHOLD


def transcribe(filepath):
    """Transcribe an audio file using Whisper.

    Returns the transcribed text, or empty string if nothing was said.
    """
    segments, _ = _whisper_model.transcribe(filepath)
    return ' '.join(seg.text for seg in segments).strip()


def listen():
    """Record audio, check for speech, and transcribe if present.

    Returns the transcribed text, or None if silence was detected.
    This is the main entry point for the agent loop.
    """
    audio_path = record()
    try:
        if not is_speech(audio_path):
            return None
        return transcribe(audio_path) or None
    finally:
        os.unlink(audio_path)
