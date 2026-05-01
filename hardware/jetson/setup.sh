#!/bin/bash
# Jetson Orin Nano Super — Initial Setup Script
# JetPack 6.2.1 / Ubuntu 22.04 / L4T R36.4.7
#
# This is the first script to run on a fresh Jetson.
# It configures CUDA paths, installs monitoring tools,
# and sets the power mode for maximum AI performance.

echo "Setting up Jetson Orin Nano Super..."

# ============================================================
# CUDA PATH
# ============================================================

# Add CUDA binaries and libraries to the system path.
# Without this, running CUDA tools (nvcc compiler, etc.) requires typing
# the full path every time. These lines append to .bashrc so the paths
# persist across terminal sessions and reboots.
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# ============================================================
# PYTHON PIP
# ============================================================

# Install pip (Python package installer).
# Most AI libraries are installed via pip. The -y flag auto-confirms
# the installation prompt so you don't have to type 'yes'.
sudo apt install python3-pip -y

# ============================================================
# JETSON MONITORING (jtop)
# ============================================================

# jtop is an interactive system monitor built specifically for Jetson.
# Like htop but shows GPU usage, power draw, temperature, and NVIDIA-specific stats.
# Run it anytime with: jtop
sudo pip3 install jetson-stats

# ============================================================
# POWER MODE: MAXN_SUPER
# ============================================================

# The Jetson Orin Nano Super has multiple power modes that trade performance
# for power consumption. MAXN_SUPER (mode 2) unlocks all 6 CPU cores at max
# frequency and the full 67 TOPS of GPU compute.
#
# nvpmodel manages these power profiles. The config file is specific to
# the Orin Nano Super hardware variant (p3767_0004_super).
sudo nvpmodel -f /etc/nvpmodel/nvpmodel_p3767_0004_super.conf -m 2

# ============================================================
# JETSON CLOCKS (lock max frequencies)
# ============================================================

# jetson_clocks locks CPU, GPU, and memory clocks at their maximum frequencies.
# Without it, the hardware dynamically scales frequencies based on load,
# which can cause inconsistent AI inference latency.
#
# We create a systemd service so clocks are locked automatically on every boot.
# systemd is Linux's service manager — it controls what runs at startup.
sudo bash -c 'cat > /etc/systemd/system/jetson-clocks.service << SERVICE
[Unit]
Description=Jetson Clocks — Lock CPU/GPU/Memory at Max Frequency
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/usr/bin/jetson_clocks
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
SERVICE'

# Reload systemd so it sees the new service file
sudo systemctl daemon-reload

# Enable: start on every boot
sudo systemctl enable jetson-clocks

# Start: run right now
sudo systemctl start jetson-clocks

# ============================================================
# DISABLE DESKTOP GUI (headless mode)
# ============================================================

# The Jetson's 8GB RAM is shared between CPU and GPU (unified memory).
# The desktop GUI (GNOME + GDM3) consumes ~1.5GB that the GPU needs
# for loading AI models. Disabling it frees that memory.
#
# multi-user.target = boot to terminal only (services + SSH still work)
# graphical.target = boot with desktop (to re-enable later if needed)
#
# This takes effect on next reboot. The Jetson is fully manageable
# over SSH — no desktop needed for a wearable device.
sudo systemctl set-default multi-user.target

echo ""
echo "Jetson setup complete!"
echo ""
echo "Verify:"
echo "  sudo nvpmodel -q          — check power mode (should be MAXN_SUPER)"
echo "  jtop                      — interactive system monitor"
echo "  sudo tegrastats           — raw system stats (RAM, GPU, temp, power)"
echo ""
echo "The desktop GUI is disabled. The Jetson will boot headless."
echo "Connect via SSH: ssh z@192.168.1.100 (or ssh z@z-desktop.local)"
echo ""
echo "Next step: Run ollama-setup.sh to install the local LLM"
