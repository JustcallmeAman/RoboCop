#!/bin/bash
# NVMe SSD Migration — Move OS from MicroSD to NVMe
# Run on Jetson Orin Nano Super (JetPack 6.2.1)
#
# WHY: NVMe is ~21x faster than MicroSD (1,691 MB/s vs 80 MB/s).
# Every file read, model load, database query, and log write benefits.
# A 2GB model loads in ~1.2s from NVMe vs ~25s from MicroSD.
#
# IMPORTANT: The Jetson's boot chain ALWAYS starts from MicroSD.
# The initial bootloader stages must stay on MicroSD regardless.
# Only the root filesystem (/) moves to NVMe. The bootloader
# reads extlinux.conf which tells it where to find root.
#
# PREREQUISITES:
#   1. NVMe SSD physically installed in M.2 Key M slot
#   2. Verify detection: lsblk should show nvme0n1
#
# This script is DOCUMENTATION, not meant to be run automatically.
# Each step should be run manually and verified.

echo "=== NVMe SSD Migration Steps ==="
echo "Run each step manually — do not execute this script directly."
echo ""

cat << 'STEPS'
# ============================================================
# STEP 1: Verify SSD is detected
# ============================================================

lsblk
# Look for: nvme0n1    259:0    0 238.5G  0 disk
# If it doesn't appear, the SSD isn't seated properly in the M.2 slot.


# ============================================================
# STEP 2: Partition the SSD
# ============================================================

# Create a GPT partition table.
# GPT (GUID Partition Table) is the modern standard for disk layouts.
# It replaces the older MBR format from the 1980s.
sudo parted /dev/nvme0n1 mklabel gpt

# Create one partition using the entire disk.
# ext4 is the standard Linux filesystem — rock solid, handles power loss
# gracefully via journaling (logs pending writes for crash recovery).
sudo parted /dev/nvme0n1 mkpart primary ext4 0% 100%

# Format the partition with ext4.
# mkfs = "make filesystem". Writes the ext4 structure onto the partition.
# The UUID generated here is the permanent ID for this partition.
sudo mkfs.ext4 /dev/nvme0n1p1


# ============================================================
# STEP 3: Copy the root filesystem
# ============================================================

# Mount the SSD at /mnt (temporary mount point).
sudo mount /dev/nvme0n1p1 /mnt

# Copy everything from MicroSD to SSD.
# rsync is a smart file copier:
#   -a: archive mode (preserves permissions, ownership, timestamps, symlinks)
#   -x: stay on one filesystem (don't copy /proc, /sys, /dev — virtual filesystems)
#   -HAWXS: preserve Hard links, ACLs, eXtended attributes, handle Sparse files
#   --numeric-ids: preserve user/group IDs as numbers (important for system files)
#   --info=progress2: show overall progress percentage
sudo rsync -axHAWXS --numeric-ids --info=progress2 / /mnt/


# ============================================================
# STEP 4: Update filesystem table on the SSD
# ============================================================

# Get the SSD's UUID.
sudo blkid /dev/nvme0n1p1
# Note the UUID value (e.g., 092f9ead-6fd4-42b1-8c66-bcf631e12cad)

# Edit fstab on the SSD copy to point root (/) to the SSD's UUID.
# fstab (filesystem table) tells Linux what to mount on boot.
# Replace YOUR-UUID with the actual UUID from blkid.
sudo sed -i 's|/dev/root|UUID=YOUR-UUID|' /mnt/etc/fstab

# Verify:
cat /mnt/etc/fstab


# ============================================================
# STEP 5: Update boot config
# ============================================================

# extlinux.conf is the Jetson's bootloader config.
# The APPEND line's root= parameter tells the kernel where to find
# the root filesystem. Change it from MicroSD to the SSD UUID.

# Update the LIVE system's boot config (bootloader reads from MicroSD):
sudo sed -i 's|root=/dev/mmcblk0p1|root=UUID=YOUR-UUID|' /boot/extlinux/extlinux.conf

# Update the SSD copy to stay in sync:
sudo sed -i 's|root=/dev/mmcblk0p1|root=UUID=YOUR-UUID|' /mnt/boot/extlinux/extlinux.conf

# Verify both match:
grep "root=" /boot/extlinux/extlinux.conf
grep "root=" /mnt/boot/extlinux/extlinux.conf


# ============================================================
# STEP 6: Unmount and reboot
# ============================================================

sudo umount /mnt
sudo reboot

# After reboot, verify:
findmnt /
# Should show: /dev/nvme0n1p1 as SOURCE

# Speed comparison:
sudo apt install hdparm -y
sudo hdparm -t /dev/nvme0n1p1   # NVMe: ~1,691 MB/s
sudo hdparm -t /dev/mmcblk0p1   # MicroSD: ~80 MB/s

STEPS
