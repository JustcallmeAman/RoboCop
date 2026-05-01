#!/bin/bash
# Audio Stack Setup — Microphone, Whisper, Bluetooth, TTS
# Run on Jetson Orin Nano Super (JetPack 6.2.1)

# This script sets up the full audio pipeline:
#   ReSpeaker mic -> Whisper transcription -> LLM -> TTS -> Bluetooth headphones
#
# Hardware:
#   Input:  ReSpeaker XVF3800 USB 4-Mic Array (USB-C connection)
#   Output: Shokz OpenRun Pro 2 (Bluetooth bone conduction)

# ============================================================
# STEP 1: Verify ReSpeaker microphone
# ============================================================

echo "=== Step 1: Checking microphone ==="

# arecord -l lists all ALSA capture (recording) devices.
# ALSA = Advanced Linux Sound Architecture, the Linux kernel's audio subsystem.
# The ReSpeaker should appear as a USB Audio device.
# It uses the standard USB audio class protocol — no special drivers needed.
echo "Looking for ReSpeaker..."
arecord -l | grep -i "respeaker\|USB Audio"

if [ $? -ne 0 ]; then
    echo "ERROR: ReSpeaker not found. Make sure it's plugged in via USB-C."
    exit 1
fi

echo "ReSpeaker detected!"
echo ""

# ============================================================
# STEP 2: Install faster-whisper (speech to text)
# ============================================================

echo "=== Step 2: Installing faster-whisper ==="

# faster-whisper is a reimplementation of OpenAI's Whisper using CTranslate2
# instead of PyTorch for inference. 4-6x faster, less memory.
# CTranslate2 is a C++ inference engine optimized for transformer models.
#
# On the Jetson, it runs on CPU with int8 quantization because the
# ARM64 CTranslate2 pip package doesn't include CUDA support.
# CPU inference is still fast enough for real-time transcription.
pip3 install faster-whisper

echo ""
echo "Downloading Whisper 'small' model (244MB)..."

# Pre-download the model so first use isn't slow.
# The 'small' model balances accuracy and performance:
#   tiny (39MB)  — fast but misses words in noise
#   small (244MB) — good for real conversations (our choice)
#   medium (769MB) — very good but uses ~2GB RAM
#   large (1.5GB)  — best but too heavy alongside Ollama
python3 -c "
from faster_whisper import WhisperModel
model = WhisperModel('small', device='cpu', compute_type='int8')
print('Whisper small model downloaded and loaded successfully!')
"

echo ""

# ============================================================
# STEP 3: Test recording and transcription
# ============================================================

echo "=== Step 3: Testing audio pipeline ==="
echo "Recording 5 seconds from ReSpeaker... SPEAK NOW!"

# arecord captures audio from the ReSpeaker:
#   -D plughw:2,0  — device card 2, subdevice 0 (ReSpeaker)
#                    'plughw' adds automatic format conversion if needed
#   -f S16_LE      — Signed 16-bit, Little Endian (standard PCM audio)
#   -r 16000       — 16kHz sample rate (what Whisper expects)
#                    Speech AI uses 16kHz; music uses 44.1kHz
#   -c 1           — mono (the XVF3800 beamforms 4 mics into 1 focused stream)
#   -d 5           — record for 5 seconds
arecord -D plughw:2,0 -f S16_LE -r 16000 -c 1 -d 5 /tmp/audio_test.wav

echo "Transcribing..."
python3 -c "
from faster_whisper import WhisperModel
model = WhisperModel('small', device='cpu', compute_type='int8')
segments, info = model.transcribe('/tmp/audio_test.wav')
print(f'Language: {info.language} ({info.language_probability:.2f})')
for seg in segments:
    print(f'[{seg.start:.1f}s - {seg.end:.1f}s] {seg.text}')
"

echo ""

# ============================================================
# STEP 4: Bluetooth audio output (Shokz)
# ============================================================

echo "=== Step 4: Setting up Bluetooth audio ==="

# Install PulseAudio Bluetooth module.
# PulseAudio is the audio server that routes sound between apps and hardware.
# Without this module, PulseAudio can't handle Bluetooth audio streams.
# BlueZ (the Bluetooth stack) handles the connection, PulseAudio handles the audio.
sudo apt install pulseaudio-module-bluetooth -y

# Restart Bluetooth and PulseAudio to load the new module.
sudo systemctl restart bluetooth
pulseaudio --kill
pulseaudio --start

echo ""
echo "To pair Shokz headphones:"
echo "  1. Put Shokz in pairing mode (hold power 5-7 seconds)"
echo "  2. Run: bluetoothctl"
echo "  3. In bluetoothctl shell:"
echo "     power on"
echo "     scan on"
echo "     (wait for Shokz to appear)"
echo "     pair AA:BB:CC:DD:EE:FF"
echo "     trust AA:BB:CC:DD:EE:FF"
echo "     connect AA:BB:CC:DD:EE:FF"
echo "     exit"
echo ""
echo "To test audio output:"
echo "  pactl list sinks short                           — list output devices"
echo "  speaker-test -D pulse -c 1 -t sine -f 440 -l 3  — play test tone"

# ============================================================
# STEP 5: Install basic TTS
# ============================================================

echo ""
echo "=== Step 5: Installing text-to-speech ==="

# espeak is a basic TTS engine — robotic but instant and tiny.
# Used for testing the audio pipeline. Will be replaced with Piper TTS
# for natural-sounding speech in production.
sudo apt install espeak -y

echo ""
echo "Audio setup complete!"
echo ""
echo "Full pipeline test (record -> transcribe -> speak -> headphones):"
echo '  arecord -D plughw:2,0 -f S16_LE -r 16000 -c 1 -d 5 /tmp/test.wav && \'
echo '  python3 -c "from faster_whisper import WhisperModel; m=WhisperModel('"'"'small'"'"',device='"'"'cpu'"'"',compute_type='"'"'int8'"'"'); s,i=m.transcribe('"'"'/tmp/test.wav'"'"'); [print(x.text) for x in s]" && \'
echo '  espeak "I heard you" --stdout | paplay'
