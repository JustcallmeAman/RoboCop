<div align="center">

# RoboCop

### Wearable Personal AI Companion

[![Built with NVIDIA Jetson](https://img.shields.io/badge/NVIDIA-Jetson_Orin_Nano_Super-76B900?style=for-the-badge&logo=nvidia&logoColor=white)](https://developer.nvidia.com/embedded/jetson-orin-nano-super-developer-kit)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![CUDA](https://img.shields.io/badge/CUDA-12.6-76B900?style=for-the-badge&logo=nvidia&logoColor=white)](https://developer.nvidia.com/cuda-toolkit)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.5.0-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

An always-on wearable AI system that sees, hears, and understands context — responding through bone conduction headphones as a private whisper in your ear.

**Built in public by Z, an artist and developer in Atlanta.**

[Getting Started](#setup-scripts) · [Architecture](#system-architecture) · [Roadmap](#roadmap) · [Concepts](#key-concepts-learned)

</div>

---

> **Project Status:** First end-to-end audio loop working — mic captures speech, Whisper transcribes, LLM reasons, TTS speaks back through bone conduction headphones. All running locally on a Jetson Orin Nano Super.

---

## What It Does

<table>
<tr>
<td width="50%">

**Perception**
- Sees what you see (computer vision via OAK-D Lite)
- Hears what you hear (live audio transcription via Whisper)
- Reads biometrics (heart rate, stress levels via Polar H10)
- Knows where you are (GPS + geofencing)

</td>
<td width="50%">

**Response**
- Responds through a private audio channel (bone conduction)
- Persistent memory of your goals, patterns, and history
- Acts as a buffer — emotionally, socially, and practically
- Maximum 1-3 sentences. Whisper in the ear, not a lecture.

</td>
</tr>
</table>

### Use Cases

| Scenario | How It Works |
|---|---|
| Social situations | Suggests how to respond in conversations based on context |
| Anxiety detection | Detects elevated HR via biometrics, offers grounding techniques |
| Sobriety monitoring | GPS at bar + late hour + elevated HR = check-in and Uber offer |
| Location awareness | "There's a jazz spot 2 blocks from you that fits your taste" |
| Pattern detection | "You've been at this bar 4 times this week" |
| Daily assistance | Real-time task help, emotional processing, routine building |

---

## Hardware Stack

| Device | Purpose | Status |
|---|---|---|
| NVIDIA Jetson Orin Nano Super (8GB) | Main compute brain -- 67 TOPS, 1024 CUDA cores | Installed |
| TN320 NVMe SSD (256GB) | Primary storage -- 21x faster than MicroSD | Installed |
| Luxonis OAK-D Lite (Fixed Focus) | Vision -- RGB + stereo depth + on-device AI (Myriad X, 4 TOPS) | Arriving Jun 3-12 |
| ReSpeaker XVF3800 USB | Microphone array -- far field, beamforming, AEC, noise cancellation | Working |
| Shokz OpenRun Pro 2 | Bone conduction audio output -- private AI voice | Connected |
| Polar H10 Heart Rate Strap | Biometrics -- HR monitoring for anxiety/stress detection | To order |
| Waveshare 3.5" HDMI Touch LCD | Field display -- glanceable dashboard | Arriving May 6-15 |
| GPS Module (USB) | Location awareness -- context, geofencing, logging | To order |
| 256GB MicroSD | Backup OS storage (boot chain) | Installed |
| 140W charger + USB hub + cables | Power and connectivity | Have |

---

<details>
<summary><h2>Software Stack -- What's Installed and Why</h2></summary>

### Operating System

**Ubuntu 22.04.5 LTS (JetPack 6.2.1, L4T R36.4.7)**

JetPack is NVIDIA's SDK for Jetson devices. It bundles the Linux OS (called L4T -- Linux for Tegra) with GPU acceleration libraries. Two version numbers track the same release: L4T R36.4.7 is the OS version, JetPack 6.2.1 is the SDK version.

The Jetson runs headless (no desktop GUI) to save ~1.5GB of RAM for AI workloads. All management happens over SSH. The desktop can be re-enabled anytime with `sudo systemctl set-default graphical.target`.

### GPU Acceleration Stack

| Component | Version | What It Does |
|---|---|---|
| CUDA | 12.6 | NVIDIA's system for running general-purpose code on GPU cores. Lets programs use 1024 GPU cores for parallel math instead of 6 CPU cores |
| cuDNN | 9.3 | Neural network primitives (convolutions, attention, pooling) optimized for CUDA. The building blocks that models like Whisper and YOLO use internally |
| TensorRT | 10.3 | Inference optimizer. Takes a trained model and optimizes it to run faster on NVIDIA hardware -- fusing layers, reducing precision, optimizing memory |

**How they stack:** CUDA (base GPU access) -> cuDNN (neural network math on CUDA) -> TensorRT (makes models run even faster). Together they form the full NVIDIA AI acceleration pipeline.

### Ollama -- Local LLM Runtime

**Version:** 0.22.0
**Model:** Llama 3.2 3B Instruct (Q4_K quantized, 1.87GB)
**API:** http://127.0.0.1:11434

Ollama is a runtime for running large language models locally. Think of it like a media player -- it doesn't contain intelligence, it knows how to *run* AI models. It handles model loading, GPU memory management, tokenization, inference, and serves a local REST API that Python code can talk to.

**Llama 3.2 3B** is Meta's open-source language model with 3.21 billion parameters across 28 layers. "Open-source" means Meta released the weights publicly -- anyone can download and run them on their own hardware. The model is quantized to Q4_K (4-bit precision), shrinking it from ~6GB to 1.87GB with minimal quality loss.

Ollama runs as a systemd service that starts on boot. The API at `127.0.0.1:11434` accepts the same HTTP request/response pattern as cloud AI APIs, but traffic never leaves the device.

**Key insight -- unified memory:** The Jetson shares 8GB RAM between CPU and GPU. The desktop GUI consumed ~1.5GB, leaving insufficient contiguous memory for CUDA to allocate the model. Disabling the desktop freed enough memory for the 1.9GB GPU allocation. This is why the Jetson runs headless.

### PyTorch -- Machine Learning Framework

**Version:** 2.5.0+cu124
**Install source:** https://download.pytorch.org/whl/cu124

PyTorch is the foundation layer that most AI models sit on. When Whisper transcribes speech, it uses PyTorch. When YOLO detects objects, PyTorch. When DeepFace reads emotions, PyTorch. It handles tensor operations (GPU-accelerated multi-dimensional array math), model loading, and inference.

The Jetson requires an ARM64-specific build. The standard pip package is for x86 desktop GPUs. PyTorch 2.5.0 was chosen because it's built against CUDA 12.4, which is compatible with the Jetson's CUDA 12.6 (backward compatible within the same major version). Newer versions (2.11+) require CUDA 13 which the Jetson doesn't have.

**Companion libraries:**
- `torchvision 0.20.0` -- computer vision utilities (image transforms, pre-trained models). Used by the camera pipeline
- `torchaudio 2.5.0` -- audio processing utilities. Used by Whisper

### Faster-Whisper -- Speech to Text

**Model:** small (244MB)
**Runtime:** CTranslate2 (CPU, int8 quantization)

Faster-whisper is a reimplementation of OpenAI's Whisper speech recognition model using CTranslate2 instead of PyTorch for inference. It's 4-6x faster and uses less memory than the original -- critical for a wearable that processes audio continuously.

The `small` model balances accuracy and performance. It handles accents, background noise, and natural conversation well while leaving memory for the LLM and future vision pipeline.

**Why CPU instead of GPU?** The pre-built CTranslate2 pip package for ARM64 doesn't include CUDA support. CPU inference with int8 quantization is still fast enough for real-time transcription on the Jetson's 6-core ARM CPU.

**Whisper model sizes:**

| Model | Disk | RAM | Best For |
|---|---|---|---|
| tiny | 39MB | ~200MB | Quick testing, quiet environments |
| base | 74MB | ~350MB | Basic transcription |
| small | 244MB | ~800MB | Real conversations, background noise (current) |
| medium | 769MB | ~2GB | High accuracy, accents |
| large | 1.5GB | ~3.5GB | Best quality, too heavy alongside Ollama |

### Audio System

**Input: ReSpeaker XVF3800 4-Mic Array**

Connected via USB-C. The XVF3800 chip does beamforming internally -- it combines signals from all 4 microphones to focus on the speaker's direction while canceling background noise. AEC (Acoustic Echo Cancellation) prevents the AI's own voice from being picked up as input. Linux sees it as a standard USB audio device (ALSA card 2), no special drivers needed.

**Output: Shokz OpenRun Pro 2 (Bluetooth)**

Connected via Bluetooth using the HFP (Hands-Free Profile) at 16kHz mono. Paired and trusted for auto-reconnect on boot. Audio routing goes through PulseAudio, which bridges the Bluetooth connection to application audio.

**Text-to-Speech: espeak (temporary)**

Basic robotic TTS for testing. Will be replaced with Piper TTS for natural-sounding speech.

**Audio pipeline:**
```
ReSpeaker mic -> arecord (ALSA capture) -> WAV file -> faster-whisper -> text
text -> espeak -> PulseAudio -> Bluetooth A2DP/HFP -> Shokz headphones
```

### Networking

**Home:** Static IP 192.168.1.100 on WiFi (ATTuq24ywN). SSH via `ssh z@192.168.1.100`.

**Away from home:** Connect Mac and Jetson to the same network (phone hotspot or local WiFi), then SSH via mDNS: `ssh z@z-desktop.local`. mDNS (multicast DNS) lets devices find each other by hostname on any local network without knowing the IP. The `.local` suffix tells the Mac to ask the local network directly instead of a DNS server.

**Adding new WiFi networks headlessly:**
```bash
# Scan for networks
nmcli device wifi list

# Connect (gets saved permanently)
sudo nmcli device wifi connect "NetworkName" password "thepassword"
```

</details>

---

## System Architecture

### Intelligence Layers

```
Layer 1: Deterministic Rules Engine
  Hard-coded safety gates. Critical biomarker thresholds,
  intoxication triggers, emergencies. Never delegates
  life-safety decisions to an LLM.

Layer 2: Perception Pipeline (continuous)
  OAK-D Lite  -> YOLOv8 + CLIP (scene understanding)
              -> DeepFace (emotion recognition)
  ReSpeaker   -> Whisper (speech-to-text)
              -> Speaker diarization
  Polar H10   -> Heart rate -> stress estimation
  GPS Module  -> Coordinates -> geofence check

Layer 3: Context Engine (30-second rolling state)
  Aggregates all sensor data into a unified state object
  that the AI reasoning layer can reference.

Layer 4: AI Reasoning (two-tier)
  Ollama (local)     -> always-on, ambient monitoring, offline
  Claude API (cloud)  -> deep reasoning for complex situations

Layer 5: Response Delivery
  Text -> Piper TTS -> Bluetooth -> Shokz OpenRun Pro 2
  Maximum 1-3 sentences. Whisper in the ear, not a lecture.

Layer 6: Memory System
  ChromaDB vector database storing goals, triggers,
  people, preferences, location history, health data.
```

### Context Engine State Object

```json
{
  "environment": "bar|gym|office|street|home|studio",
  "location": {
    "coordinates": [0.0, 0.0],
    "address": "Ponce City Market, Atlanta",
    "geofence": "bar_zone",
    "time_at_location": "2h 15m"
  },
  "people_present": [],
  "conversation_transcript": "",
  "detected_emotions": {},
  "heart_rate": 0,
  "stress_level": "low|moderate|high",
  "time": "",
  "z_state": "sober|elevated|anxious|tired|focused"
}
```

---

<details>
<summary><h2>Storage Architecture</h2></summary>

The Jetson uses two storage devices:

**NVMe SSD (TN320, 238.5GB) -- Primary**
- Mounted as root filesystem (`/`)
- Read speed: 1,691 MB/s
- Holds OS, all software, models, databases

**MicroSD (256GB) -- Boot chain + backup**
- Holds bootloader partitions (NVIDIA's multi-stage boot chain requires MicroSD)
- Read speed: 80 MB/s (21x slower than NVMe)
- Contains a full backup of the original OS

**Boot flow:** Hardware firmware -> bootloader stages on MicroSD -> reads `extlinux.conf` which points `root=` to the NVMe SSD UUID -> Linux kernel loads -> root filesystem on NVMe takes over.

</details>

---

<details>
<summary><h2>Project Structure</h2></summary>

```
RoboCop/
  src/
    perception/          # OAK-D camera, vision, emotion detection
      camera.py
      emotion.py
      scene.py
    reasoning/           # AI agent, context engine, LLM
      agent.py
      context.py
      rules.py
    audio/               # Mic input, transcription, TTS
      microphone.py
      whisper.py
      tts.py
    memory/              # ChromaDB, history, user profile
      vector_store.py
      profile.py
    location/            # GPS and location features
      gps.py
      geocoder.py
      geofence.py
      history.py
      poi.py
    display/             # Waveshare 3.5" dashboard
      dashboard.py
    integrations/        # External APIs
      uber.py
      weather.py
  hardware/
    jetson/
      setup.sh           # Initial Jetson configuration
      ollama-setup.sh     # Ollama + model installation
      pytorch-setup.sh    # PyTorch installation
      audio-setup.sh      # Audio stack configuration
      nvme-migration.sh   # NVMe SSD migration steps
  docs/
    concepts.md           # Key concepts explained
  scripts/
  tests/
  configs/
  .env.example
  .gitignore
  README.md
```

</details>

---

## Setup Scripts

All setup scripts are in `hardware/jetson/`. They document the exact commands used to configure the Jetson, with explanations of what each command does and why.

| Script | Purpose |
|---|---|
| `setup.sh` | Initial Jetson config: CUDA path, pip, jtop, power mode, clocks |
| `ollama-setup.sh` | Install Ollama, pull Llama 3.2 3B, configure for headless GPU use |
| `pytorch-setup.sh` | Install PyTorch 2.5.0 ARM64 CUDA build + torchvision + torchaudio |
| `audio-setup.sh` | Configure ReSpeaker, Whisper, Bluetooth audio, PulseAudio |
| `nvme-migration.sh` | Partition SSD, clone OS from MicroSD, update boot config |

---

<details>
<summary><h2>Key Concepts Learned</h2></summary>

### CUDA and GPU Computing
A CPU has a few powerful cores (6 on the Jetson). A GPU has thousands of tiny cores (1024 on the Orin) that work in parallel. CUDA lets programs run math on those GPU cores. Neural network inference is massive matrix multiplication -- spreading it across 1024 cores makes it dramatically faster than running on 6 CPU cores.

### Unified Memory (Jetson-specific)
Unlike desktop GPUs with dedicated VRAM, the Jetson's CPU and GPU share one 8GB RAM pool. This means the OS, applications, and GPU workloads all compete for the same memory. Running headless (no desktop GUI) frees ~1.5GB, which is the difference between the LLM fitting on GPU or not.

### Memory Fragmentation
Even with enough total free RAM, CUDA can fail if there isn't a large enough *contiguous* block. `tegrastats` shows `lfb` (largest free block) -- this is more important than total free memory for GPU allocations. Dropping the Linux page cache (`echo 3 > /proc/sys/vm/drop_caches`) can help defragment memory.

### Quantization
Neural network weights are normally stored as 32-bit or 16-bit floating point numbers. Quantization shrinks them to 8-bit or 4-bit integers, dramatically reducing model size and memory usage with minimal quality loss. Llama 3.2 3B uses Q4_K (4-bit) quantization, shrinking from ~6GB to 1.87GB. Whisper uses int8 quantization on CPU.

### Localhost APIs
Services on the Jetson communicate over HTTP on localhost ports, the same pattern as calling cloud APIs but traffic never leaves the device. Ollama on `:11434`, FastAPI context engine on `:8000`, etc. Each service runs independently -- if one crashes, others keep running.

### systemd Services
Linux uses systemd to manage background services (daemons). `systemctl enable` makes a service start on boot. `systemctl start/stop/restart` controls it manually. `journalctl -u servicename` reads its logs. Ollama, Bluetooth, and NetworkManager all run as systemd services.

### PulseAudio and Bluetooth Audio
PulseAudio is the audio server that routes sound between applications and hardware. For Bluetooth audio, it needs the `pulseaudio-module-bluetooth` package to bridge BlueZ (the Bluetooth stack) with audio output. Bluetooth audio uses profiles: A2DP for high-quality stereo playback, HFP for phone-call quality mono.

</details>

---

<details>
<summary><h2>Useful Commands</h2></summary>

### System Monitoring
```bash
# Real-time Jetson stats (RAM, GPU, CPU, temp, power)
sudo tegrastats --interval 1000

# Interactive system monitor
jtop

# Memory usage
free -h

# Storage devices and partitions
lsblk

# Disk speed test
sudo hdparm -t /dev/nvme0n1p1
```

### Ollama
```bash
# Start a chat
ollama run llama3.2:3b

# List installed models
ollama list

# Pull a new model
ollama pull modelname

# Check Ollama service
sudo systemctl status ollama

# View Ollama logs
journalctl -u ollama -n 30 --no-pager
```

### Audio
```bash
# List recording devices
arecord -l

# Record 5 seconds from ReSpeaker
arecord -D plughw:2,0 -f S16_LE -r 16000 -c 1 -d 5 /tmp/test.wav

# List PulseAudio output devices
pactl list sinks short

# Test speaker output
speaker-test -D pulse -c 1 -t sine -f 440 -l 3
```

### Bluetooth
```bash
# Open Bluetooth shell
bluetoothctl

# Inside bluetoothctl:
power on
scan on
pair AA:BB:CC:DD:EE:FF
trust AA:BB:CC:DD:EE:FF
connect AA:BB:CC:DD:EE:FF
```

### Networking
```bash
# Scan WiFi networks
nmcli device wifi list

# Connect to new WiFi
sudo nmcli device wifi connect "SSID" password "pass"

# Show saved connections
nmcli connection show

# SSH from anywhere on same network
ssh z@z-desktop.local
```

</details>

---

## Roadmap

### Phase 0: Foundation (Complete)

- [x] Jetson initial setup (CUDA, power mode, SSH)
- [x] GitHub repository (public)
- [x] Ollama + Llama 3.2 3B running on GPU
- [x] Desktop GUI disabled for memory headroom
- [x] NVMe SSD migration (21x faster storage)
- [x] PyTorch 2.5.0 with CUDA acceleration
- [x] Whisper speech-to-text (faster-whisper, small model)
- [x] ReSpeaker microphone working
- [x] Shokz Bluetooth audio output working
- [x] First end-to-end audio loop (mic -> transcription -> TTS -> headphones)

### Phase 1: Agent Loop (Next)

- [ ] Install Piper TTS (natural-sounding voice)
- [ ] Fix Bluetooth A2DP for better audio quality
- [ ] Build Phase 1 agent loop (speak -> Whisper -> Ollama -> Piper -> Shokz)
- [ ] Scaffold Python project structure

### Phase 2: Perception

- [ ] Set up DepthAI + OAK-D Lite (arriving Jun 3-12)
- [ ] YOLOv8 object detection
- [ ] DeepFace emotion recognition
- [ ] Install and configure GPS module
- [ ] Polar H10 biometric integration

### Phase 3: Intelligence

- [ ] Build context engine (30-second rolling state)
- [ ] Build rules engine (safety gates)
- [ ] Set up ChromaDB memory system
- [ ] Claude API integration for deep reasoning
- [ ] Compound trigger system (GPS + HR + time + context)

### Phase 4: Polish

- [ ] Build wearable enclosure
- [ ] Remote dashboard (Next.js + Waveshare display)
- [ ] Location-aware recommendations (Google Places / Foursquare)
- [ ] Uber API integration

---

## Contributing

This project is built in public. Follow along, open issues, or fork it. If you're building something similar, let's connect.

---

<div align="center">

**Built with patience, curiosity, and Claude Code.**

[![GitHub](https://img.shields.io/badge/Follow_the_build-GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/JustcallmeAman/RoboCop)

</div>

## License

MIT
