#!/bin/bash
# Jetson Orin Nano Super — Initial Setup Script
# JetPack 6.2.1 / Ubuntu 22.04

echo "Setting up Jetson Orin Nano Super..."

# Fix CUDA PATH
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# Install Python pip
sudo apt install python3-pip -y

# Install jetson-stats
sudo pip3 install jetson-stats

# Set MAXN_SUPER power mode
sudo nvpmodel -f /etc/nvpmodel/nvpmodel_p3767_0004_super.conf -m 2

# Create jetson-clocks systemd service
sudo bash -c 'cat > /etc/systemd/system/jetson-clocks.service << SERVICE
[Unit]
Description=Jetson Clocks
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/usr/bin/jetson_clocks
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
SERVICE'

sudo systemctl daemon-reload
sudo systemctl enable jetson-clocks
sudo systemctl start jetson-clocks

echo "Jetson setup complete!"
echo "Run: sudo nvpmodel -q to verify MAXN_SUPER"
echo "Run: jtop to monitor system"
