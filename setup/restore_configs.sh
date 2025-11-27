#!/bin/bash
# Restore hardware configuration for music player

echo "Restoring hardware configuration..."

# Backup originals
sudo cp /boot/firmware/config.txt /boot/firmware/config.txt.backup
sudo cp /etc/asound.conf /etc/asound.conf.backup 2>/dev/null

# Restore configs
echo "Copying config.txt..."
sudo cp setup/config_backups/config.txt /boot/firmware/config.txt

echo "Copying asound.conf..."
sudo cp setup/config_backups/asound.conf /etc/asound.conf

echo ""
echo "Configuration restored!"
echo "You must reboot for changes to take effect."
echo ""
echo "Run: sudo reboot"
