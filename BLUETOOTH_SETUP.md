# Bluetooth Audio Setup Guide

This guide explains how to use the Bluetooth settings screen to connect your Raspberry Pi to Bluetooth headphones.

## Prerequisites

On your Raspberry Pi, make sure you have the required packages:

```bash
sudo apt-get update
sudo apt-get install bluetooth bluez pulseaudio pulseaudio-module-bluetooth
```

## Using the Bluetooth Settings Screen

1. **Navigate to Settings**
   - From the main menu, select "Settings"
   - The Bluetooth Audio screen will open

2. **Scan for Devices**
   - Press `S` to scan for nearby Bluetooth devices
   - Scanning takes about 5 seconds
   - Your headphones should appear in the list

3. **Connect to Headphones**
   - Use ↑/↓ to navigate to your headphones
   - Press `ENTER` to connect
   - The app will:
     - Pair with the device (if not already paired)
     - Connect to the device
     - Set it as the default audio output
     - Trust the device for auto-reconnect

4. **Check Connection Status**
   - Connected devices show `[CONNECTED]` in green
   - Paired devices show `[PAIRED]` in yellow
   - The current connection is shown at the top

5. **Disconnect**
   - Press `D` to disconnect from the current device

## Keyboard Controls

- **↑/↓**: Navigate device list
- **ENTER**: Connect to selected device
- **S**: Scan for new devices
- **D**: Disconnect current device
- **BACKSPACE**: Return to main menu
- **Q**: Quit application

## Physical Button Controls

If using the hardware buttons:
- **UP/DOWN**: Navigate device list
- **SELECT**: Connect to selected device
- **BACK**: Return to main menu

## Troubleshooting

### Headphones not appearing
1. Make sure your headphones are in pairing mode
2. Press `S` to scan again
3. Make sure Bluetooth is enabled on the Pi: `sudo systemctl status bluetooth`

### Connection fails
1. Remove the device: Use `bluetoothctl` manually to remove
2. Restart Bluetooth service: `sudo systemctl restart bluetooth`
3. Try pairing again

### Audio still plays through Pi's output
The app automatically sets the Bluetooth device as the default audio sink. If this doesn't work:

```bash
# List audio sinks
pactl list short sinks

# Find the bluez sink and set as default
pactl set-default-sink bluez_sink.XX_XX_XX_XX_XX_XX.a2dp_sink
```

### Check audio routing
```bash
# See what's playing
pactl list sink-inputs

# Move audio to Bluetooth
pactl move-sink-input <input-id> bluez_sink.XX_XX_XX_XX_XX_XX.a2dp_sink
```

## Auto-reconnect

Once you've connected to a device, it's automatically trusted for auto-reconnect. Your headphones should reconnect automatically when:
- They're powered on
- They're in range
- Bluetooth is enabled on the Pi

## Technical Details

The Bluetooth manager uses:
- **bluetoothctl**: For device pairing and connection
- **PulseAudio (pactl)**: For audio routing

All audio played through pygame will automatically route to the connected Bluetooth device.

## Removing DAC Code

Since you removed the DAC hardware, the app now uses:
1. **Built-in audio** (if no Bluetooth connected)
2. **Bluetooth audio** (when connected via Settings)

The mock audio player is used if pygame can't initialize audio (like in WSL for development).
