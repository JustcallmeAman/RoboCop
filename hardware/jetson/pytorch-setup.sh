#!/bin/bash
# PyTorch Installation — Machine Learning Framework
# Run on Jetson Orin Nano Super (JetPack 6.2.1, CUDA 12.6)

# PyTorch is the foundation layer that most AI models sit on.
# Whisper, YOLO, DeepFace, and most neural networks use PyTorch
# for tensor operations (GPU-accelerated multi-dimensional array math),
# model loading, and inference.
#
# The Jetson requires a specific PyTorch build:
# - ARM64 architecture (not x86 like desktop PCs)
# - CUDA 12.x compatible (the Jetson has CUDA 12.6)
#
# IMPORTANT: PyTorch version must match CUDA version.
# PyTorch 2.5.0+cu124 is built for CUDA 12.4, which is backward
# compatible with CUDA 12.6 (same major version).
# PyTorch 2.11+ requires CUDA 13 which the Jetson doesn't have.
#
# NVIDIA's Jetson-specific indexes (jp/v60, jp/v61, jp/v62) did not
# have packages for our setup. The generic ARM64 CUDA 12.4 wheels
# from PyTorch's official repository work correctly.

echo "Upgrading pip..."
pip3 install --upgrade pip

echo ""
echo "Installing PyTorch 2.5.0 (CUDA 12.4 build)..."

# --index-url points to PyTorch's official wheel repository organized by CUDA version.
# cu124 = CUDA 12.4 compatible builds.
# Wheels (.whl files) are pre-compiled packages — no build step needed.
# --no-cache-dir prevents caching the ~2.4GB download.
pip3 install --no-cache-dir torch==2.5.0 --index-url https://download.pytorch.org/whl/cu124

echo ""
echo "Installing torchvision and torchaudio..."

# These version numbers must match PyTorch 2.5.0:
# - torchvision 0.20.0 — computer vision utilities (image transforms, pretrained models)
# - torchaudio 2.5.0 — audio processing utilities (used by Whisper)
# If versions are mismatched, things break silently.
pip3 install --no-cache-dir torchvision==0.20.0 torchaudio==2.5.0 --index-url https://download.pytorch.org/whl/cu124

echo ""
echo "Verifying installation..."

# Test that PyTorch can see the GPU.
# "Error in cpuinfo: prctl(PR_SVE_GET_VL) failed" is harmless —
# it checks for ARM SVE extensions which the Orin's Cortex-A78AE cores don't have.
# PyTorch falls back to NEON instructions (which ARE supported) and works fine.
python3 -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA device: {torch.cuda.get_device_name(0)}')
    print(f'CUDA version: {torch.version.cuda}')
else:
    print('WARNING: CUDA not available! Check driver compatibility.')
"

echo ""
echo "PyTorch setup complete!"
