# Key Concepts — RoboCop Learning Notes

A reference of concepts learned while building the RoboCop wearable AI system.

---

## Hardware Concepts

### CUDA (Compute Unified Device Architecture)
NVIDIA's system for running general-purpose code on GPU cores. A CPU has a few powerful cores (6 on the Jetson) that handle tasks sequentially. A GPU has thousands of tiny cores (1024 on the Orin) that work in parallel. CUDA lets programs use those GPU cores for math-heavy workloads like neural network inference, which is fundamentally massive matrix multiplication.

### Unified Memory (Jetson-specific)
Desktop GPUs have dedicated VRAM (Video RAM) separate from system RAM. The Jetson is different — its CPU and GPU share one pool of 8GB RAM. This means the OS, applications, and GPU workloads compete for the same memory. Running headless (no desktop GUI) is critical because the desktop consumes ~1.5GB that the GPU needs.

### Memory Fragmentation
Even with enough total free RAM, CUDA can fail if there isn't a large enough *contiguous* block. Think of it like a theater: you might have 50 empty seats, but not 10 seats in a row. The `tegrastats` tool shows `lfb` (largest free block) — this number matters more than total free memory for GPU allocations.

### TOPS (Trillion Operations Per Second)
A measure of AI compute performance. The Jetson Orin Nano Super is rated at 67 TOPS. This measures how many simple math operations (multiply-add) the hardware can do per second. Higher TOPS = faster model inference.

### M.2 Key M
A physical connector standard for NVMe SSDs. The "Key M" refers to the notch pattern on the connector edge — it ensures you can only insert the drive in the correct orientation. The SSD slides in at a 30-degree angle, pivots flat, and is secured with a small screw.

### Beamforming (ReSpeaker)
The ReSpeaker has 4 microphones arranged in a pattern. Beamforming combines signals from all 4 mics to focus on sound from a specific direction while canceling noise from other directions. The XVF3800 chip does this processing internally — the output is a single focused audio stream, not 4 separate channels.

---

## Linux Concepts

### systemd
The system and service manager for Linux. It controls what runs on boot and manages background services (daemons). Key commands:
- `systemctl enable <service>` — start on every boot
- `systemctl start/stop/restart <service>` — control now
- `systemctl status <service>` — check if running
- `journalctl -u <service>` — read its logs

### Block Devices
Any storage hardware that reads/writes data in fixed-size chunks (blocks). SSDs, hard drives, SD cards are all block devices. Listed with `lsblk`. As opposed to "character devices" like keyboards that send data one byte at a time.

### Partitions
Logical divisions of a physical drive — like splitting one closet into shelves. A single SSD might have one partition for the OS and another for data. The Jetson's MicroSD has ~15 partitions because NVIDIA's boot chain is complex (multiple bootloader stages, redundant backups, kernel images).

### ext4
The standard Linux filesystem (like APFS on Mac or NTFS on Windows). Features journaling — a log of pending writes that enables crash recovery. If power cuts mid-write, ext4 replays the journal on next boot to fix inconsistencies.

### fstab (/etc/fstab)
The filesystem table. Tells Linux "when you boot, mount these drives at these locations." Each line maps a device (identified by UUID) to a mount point (directory path).

### UUID (Universally Unique Identifier)
A permanent ID burned into a filesystem when formatted. More reliable than device names like `/dev/nvme0n1p1` which could theoretically change between boots. Used in fstab and boot configs to identify specific drives.

### extlinux.conf
The Jetson's bootloader configuration file. Tells the bootloader which kernel to load and which partition is the root filesystem (via the `root=` parameter in the APPEND line). Lives on MicroSD because the initial boot stages always start there.

### sudo
"Superuser do" — run a command as the system administrator (root). Required for system-level operations like installing packages, modifying system files, or accessing hardware directly.

### Pipes (|)
Take the output of one command and feed it as input to another. Example: `curl -s URL | sh` downloads a script and immediately executes it. Commands are chained left to right.

### /dev/null
A "black hole" file — anything written to it disappears. Used when you want to run a command but discard its output. Example: `dd if=/dev/sda of=/dev/null` reads a drive but throws away the data (for speed testing).

### /proc and /sys
Virtual filesystems that expose kernel information as files. `/proc/sys/vm/drop_caches` isn't a real file on disk — writing to it tells the kernel to drop its memory caches. This is how Linux lets you configure the running kernel through familiar file operations.

---

## Networking Concepts

### SSH (Secure Shell)
Encrypted remote terminal access. Connect to the Jetson from your Mac: `ssh z@192.168.1.100`. All commands you type are executed on the Jetson, not your Mac.

### Static IP
A fixed IP address that doesn't change between reboots. The Jetson is set to `192.168.1.100` on the home network via NetworkManager. Without a static IP, the router assigns a random IP via DHCP each time.

### mDNS (Multicast DNS) / .local
Lets devices find each other on a local network by hostname without a DNS server. When your Mac connects to `z-desktop.local`, it broadcasts "who is z-desktop?" on the local network. The Jetson responds with its IP. Works on any network — no static IP needed. macOS calls it Bonjour, Linux uses Avahi.

### NetworkManager / nmcli
NetworkManager manages all network connections on Linux (WiFi, ethernet, VPN). `nmcli` is its command-line interface. Saved WiFi connections persist in `/etc/NetworkManager/system-connections/` and auto-connect when detected.

### 127.0.0.1 (localhost)
The loopback address. Traffic sent here never touches a network cable — it loops back to the same device. Used for services talking to each other on the same machine. Ollama's API at `127.0.0.1:11434` follows the same HTTP pattern as cloud APIs but data never leaves the Jetson.

### Ports
A number that identifies a specific service on a machine. Like apartment numbers in a building — the IP address gets you to the building, the port gets you to the right door. Ollama uses 11434, SSH uses 22, HTTP uses 80. Only one program can listen on a port at a time.

---

## AI/ML Concepts

### Parameters
The learned numbers (weights) inside a neural network. Llama 3.2 has 3.21 billion of them. During training, these numbers were tuned across trillions of tokens of text. More parameters generally = smarter model but more memory and compute needed.

### Layers
A neural network is a stack of identical processing layers — data flows through layer 1, then 2, then 3, etc. Each layer transforms the data slightly. Llama 3.2 3B has 28 layers. When GPU memory is tight, some layers can run on CPU while others stay on GPU (partial offloading).

### Tokens
The units that language models think in. Not exactly words — "tokenization" splits text into subword pieces. "understanding" might become ["under", "standing"]. Llama 3.2's vocabulary has 128,256 possible tokens. Context length (4096 tokens) determines how much conversation the model can "see" at once (~3000 words).

### Quantization
Shrinking neural network weights from high-precision numbers to lower-precision ones. The original Llama 3.2 uses 16-bit floats. Q4_K quantization shrinks to 4-bit integers, cutting size from ~6GB to 1.87GB with minimal quality loss. Like compressing FLAC to high-quality MP3 — technically lossy but hard to notice. Types:
- **Q4_K** — 4-bit, used by Llama on Ollama
- **int8** — 8-bit, used by Whisper on CPU
- **float16** — half precision, standard for GPU inference

### Inference
Running input data through a trained model to get predictions. As opposed to training (adjusting the model's weights to learn). All on-device AI in RoboCop is inference — the models are pre-trained, we just run them.

### Transformer Architecture
The neural network design used by virtually all modern language and speech models (GPT, Llama, Whisper, CLIP). Key innovation: the "attention mechanism" which lets the model decide which parts of the input are most relevant to the current output. Whisper uses transformers to convert audio spectrograms to text. Llama uses them to generate text from prompts.

### GGUF (GPT-Generated Unified Format)
A file format for storing quantized language models. Designed for efficient loading and inference on consumer hardware. When Ollama downloads a model, it gets a GGUF file. It contains the model weights, tokenizer, and metadata in one package.

### Wheels (.whl files)
Pre-compiled Python packages ready to install. As opposed to installing from source code (which requires compilation). NVIDIA and PyTorch provide ARM64-specific wheels for the Jetson since the standard packages are compiled for x86 desktop CPUs.

---

## Audio Concepts

### Sample Rate
How many audio samples are captured per second. 16,000 Hz (16kHz) means 16,000 measurements per second — standard for speech recognition. Music uses 44,100 Hz (CD quality). Higher = more detail but larger files.

### PCM (Pulse Code Modulation)
Raw, uncompressed digital audio. Each sample is a number representing the sound wave's amplitude at that instant. S16_LE = Signed 16-bit Little Endian — each sample is a 16-bit integer (range -32768 to 32767), stored least-significant-byte first (how ARM processors order data in memory).

### ALSA (Advanced Linux Sound Architecture)
The Linux kernel's audio subsystem. Talks directly to audio hardware and provides a standard interface for programs. `arecord` and `aplay` are ALSA tools. Higher-level audio servers (PulseAudio) sit on top of ALSA.

### PulseAudio
An audio server that sits between applications and ALSA. Handles mixing multiple audio streams, volume control, and routing audio between devices. Critical for Bluetooth audio — it bridges the BlueZ Bluetooth stack with ALSA audio output.

### Bluetooth Audio Profiles
- **A2DP** (Advanced Audio Distribution Profile) — high-quality stereo audio streaming (music/podcast quality)
- **HFP** (Hands-Free Profile) — phone-call quality, mono, 16kHz. Lower quality but supports microphone input
- The Shokz currently connects via HFP due to a BlueZ/PulseAudio version mismatch

### CTranslate2
A C++ inference engine optimized for transformer models. faster-whisper uses it instead of PyTorch for running Whisper. Benefits: 4-6x faster inference, lower memory usage, int8 quantization support. The tradeoff: the ARM64 pip package doesn't include CUDA support, so it runs on CPU only.

### Beamforming
Combining signals from multiple microphones to focus on sound from a specific direction. The ReSpeaker's 4 mics are arranged so the XVF3800 chip can calculate where sound is coming from (based on tiny timing differences between mics) and amplify that direction while suppressing others.

### AEC (Acoustic Echo Cancellation)
The ReSpeaker's ability to filter out the device's own audio output from its microphone input. Without AEC, when the AI speaks through nearby speakers, the mic would pick up that audio and create a feedback loop. The XVF3800 handles this in hardware.
