"""
RoboCop Configuration

All settings in one place. Auto-detects hardware where possible.
"""

import subprocess
import re

# ============================================================
# Audio Input
# ============================================================

SAMPLE_RATE = 16000
RECORD_SECONDS = 5
CHANNELS = 1

# Minimum RMS energy to consider audio as speech (not silence).
# Below this threshold, we skip Whisper entirely to avoid
# hallucinated transcriptions like "You" or "Thank you".
# 500 is conservative — normal speech is typically 2000-10000.
SILENCE_THRESHOLD = 500


def detect_mic_device():
    """Auto-detect the ReSpeaker mic card number.

    The ReSpeaker's ALSA card number shifts between boots depending
    on USB enumeration order. Instead of hardcoding plughw:2,0, we
    parse `arecord -l` to find the card with 'xvf3800' or 'ReSpeaker'
    in the name.

    Returns 'plughw:N,0' where N is the detected card number,
    or 'plughw:2,0' as a fallback.
    """
    try:
        result = subprocess.run(
            ['arecord', '-l'], capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.lower().split('\n'):
            if 'xvf3800' in line or 'respeaker' in line:
                match = re.search(r'card (\d+)', line)
                if match:
                    card = match.group(1)
                    print(f'Auto-detected ReSpeaker on card {card}')
                    return f'plughw:{card},0'
    except Exception:
        pass

    print('WARNING: Could not auto-detect ReSpeaker, using plughw:2,0')
    return 'plughw:2,0'


# ============================================================
# Speech-to-Text (Whisper)
# ============================================================

WHISPER_MODEL = 'small'
WHISPER_DEVICE = 'cpu'
WHISPER_COMPUTE = 'int8'

# ============================================================
# LLM (Ollama)
# ============================================================

OLLAMA_URL = 'http://127.0.0.1:11434/api/generate'
OLLAMA_MODEL = 'qwen2.5:3b'

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
# Text-to-Speech (Piper)
# ============================================================

PIPER_VOICE = '/home/z/.local/share/piper_voices/en_GB-alba-medium.onnx'

# Silence padding (seconds) added before and after speech.
# Bluetooth codecs have a startup delay that swallows the first ~300ms.
# The stream also closes before the last chunk finishes playing.
TTS_PADDING_SECONDS = 0.4

# ============================================================
# Audio Output (Bluetooth)
# ============================================================

AUDIO_SINK = 'bluez_output.A0_0C_E2_D5_CE_ED.headset-head-unit'

# ============================================================
# Vision (OAK-D Lite)
# ============================================================

DETECTION_MODEL = 'mobilenet-ssd'
DETECTION_PLATFORM = 'RVC2'
DETECTION_CONFIDENCE = 0.5
CAMERA_PREVIEW_SIZE = (300, 300)
CAMERA_FPS = 10

DETECTION_LABELS = [
    'background', 'aeroplane', 'bicycle', 'bird', 'boat', 'bottle', 'bus',
    'car', 'cat', 'chair', 'cow', 'diningtable', 'dog', 'horse',
    'motorbike', 'person', 'pottedplant', 'sheep', 'sofa', 'train', 'tvmonitor'
]
