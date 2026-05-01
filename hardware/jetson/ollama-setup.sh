#!/bin/bash
# Ollama Installation — Local LLM Runtime
# Run on Jetson Orin Nano Super (JetPack 6.2.1)

# IMPORTANT: Before installing Ollama, disable the desktop GUI to free ~1.5GB of RAM.
# The Jetson's 8GB is shared between CPU and GPU (unified memory).
# With the desktop running, CUDA can't allocate enough contiguous memory for the model.
#
# Disable desktop (takes effect on reboot):
#   sudo systemctl set-default multi-user.target
#
# Stop desktop immediately (current session):
#   sudo systemctl stop gdm3
#
# To re-enable desktop later:
#   sudo systemctl set-default graphical.target

echo "Installing Ollama..."

# Download and run the Ollama installer.
# -f: fail silently on HTTP errors
# -s: silent mode (no progress bar)
# -S: show errors if something fails
# -L: follow redirects
# The pipe (|) feeds the downloaded script directly into sh to execute it.
# The installer detects ARM64 architecture and downloads the correct build.
# It also detects JetPack and grabs CUDA-optimized libraries automatically.
curl -fsSL https://ollama.com/install.sh | sh

# What the installer does:
# 1. Downloads ollama-linux-arm64.tar.zst (base binary)
# 2. Downloads ollama-linux-arm64-jetpack6.tar.zst (CUDA acceleration for JetPack 6)
# 3. Creates a dedicated 'ollama' system user (security: runs with minimal permissions)
# 4. Adds ollama user to 'render' and 'video' groups (GPU hardware access)
# 5. Creates a systemd service at /etc/systemd/system/ollama.service
# 6. Enables the service to start on every boot
# 7. Starts the Ollama API server on 127.0.0.1:11434

echo ""
echo "Pulling Llama 3.2 3B model..."

# Download the Llama 3.2 3B Instruct model (~2GB).
# This is Meta's open-source LLM with 3.21 billion parameters.
# Q4_K quantization shrinks it from ~6GB to 1.87GB with minimal quality loss.
# Quantization: storing neural network weights as 4-bit integers instead of 16-bit floats.
ollama pull llama3.2:3b

echo ""
echo "Testing model..."

# Quick test — send a prompt and check for a response.
# The Ollama API uses the same HTTP REST pattern as cloud AI APIs,
# but traffic stays on localhost (127.0.0.1) — never leaves the device.
curl -s http://127.0.0.1:11434/api/generate -d '{
  "model": "llama3.2:3b",
  "prompt": "Say hello in one sentence.",
  "stream": false
}' | python3 -c "import sys,json; print(json.load(sys.stdin)['response'])"

echo ""
echo "Ollama setup complete!"
echo "Run: ollama run llama3.2:3b (interactive chat)"
echo "API: http://127.0.0.1:11434"
echo ""
echo "Useful commands:"
echo "  ollama list              — list installed models"
echo "  ollama pull <model>      — download a new model"
echo "  sudo systemctl status ollama  — check service status"
echo "  journalctl -u ollama -n 30    — view recent logs"
echo ""
echo "Memory tips:"
echo "  sudo tegrastats --interval 1000  — monitor RAM/GPU usage"
echo "  sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'  — free cached memory"
