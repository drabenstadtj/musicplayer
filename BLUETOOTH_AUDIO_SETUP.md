# Bluetooth-Only Audio Setup for Raspberry Pi

This guide configures your Raspberry Pi to use Bluetooth headphones as the only audio output (no sound card required).

## Prerequisites

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade

# Install required packages
sudo apt-get install -y bluetooth bluez pulseaudio pulseaudio-module-bluetooth

# Install Python requirements
pip3 install -r requirements.txt
```

## PulseAudio Configuration

### 1. Enable PulseAudio for your user

```bash
# Start PulseAudio
pulseaudio --start

# Make it start automatically
systemctl --user enable pulseaudio
```

### 2. Configure PulseAudio for Bluetooth

Edit `/etc/pulse/default.pa` and ensure these lines are present:

```
# Bluetooth support
load-module module-bluetooth-policy
load-module module-bluetooth-discover
```

### 3. Restart PulseAudio

```bash
pulseaudio -k
pulseaudio --start
```

## Bluetooth Setup

### 1. Enable Bluetooth service

```bash
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
```

### 2. Check Bluetooth is working

```bash
bluetoothctl
# Inside bluetoothctl:
power on
agent on
default-agent
scan on
# Wait for your headphones to appear, then:
scan off
exit
```

## Troubleshooting

### No audio output / ALSA errors

If you see ALSA errors like:
```
ALSA lib confmisc.c:855:(parse_card) cannot find card '0'
ALSA lib pcm.c:2722:(snd_pcm_open_noupdate) Unknown PCM default
```

This is normal when you don't have a sound card. The app now uses PulseAudio instead.

To verify PulseAudio is working:

```bash
# Check PulseAudio status
pulseaudio --check
echo $?  # Should return 0 if running

# List audio sinks (should show Bluetooth when connected)
pactl list short sinks

# Test audio (should work after connecting Bluetooth)
paplay /usr/share/sounds/alsa/Front_Center.wav
```

### Bluetooth scan finds 0 devices

1. **Make sure Bluetooth is enabled:**
   ```bash
   sudo systemctl status bluetooth
   # Should show "active (running)"
   ```

2. **Put your headphones in pairing mode:**
   - Most headphones require holding the power button for 5-10 seconds
   - Look for a flashing LED (usually blue/red alternating)

3. **Check permissions:**
   ```bash
   # Your user should be in the bluetooth group
   sudo usermod -a -G bluetooth $USER
   # Log out and back in for group change to take effect
   ```

4. **Manual scan test:**
   ```bash
   bluetoothctl
   power on
   scan on
   # Wait 10 seconds - you should see devices appear
   ```

5. **Check Bluetooth hardware:**
   ```bash
   hciconfig
   # Should show hci0 UP RUNNING

   # If not UP:
   sudo hciconfig hci0 up
   ```

### Connected but no audio

1. **Ensure Bluetooth is set as default sink:**
   ```bash
   # List sinks
   pactl list short sinks

   # Look for bluez_sink.XX_XX_XX_XX_XX_XX
   # Set as default (replace with your actual sink name):
   pactl set-default-sink bluez_sink.XX_XX_XX_XX_XX_XX.a2dp_sink
   ```

2. **Check audio routing:**
   ```bash
   # See active audio streams
   pactl list sink-inputs

   # Move to Bluetooth (replace IDs with actual values):
   pactl move-sink-input <INPUT_ID> bluez_sink.XX_XX_XX_XX_XX_XX.a2dp_sink
   ```

3. **Verify codec:**
   ```bash
   # Check Bluetooth audio profile
   pactl list cards
   # Look for "Active Profile: a2dp_sink" (high quality)
   # If showing "headset_head_unit" (low quality), change it:
   pactl set-card-profile bluez_card.XX_XX_XX_XX_XX_XX a2dp_sink
   ```

### App still shows "No audio available"

This means pygame couldn't initialize with PulseAudio. Check:

```bash
# Make sure PulseAudio is running
pulseaudio --check && echo "Running" || echo "Not running"

# Check if SDL can see PulseAudio
SDL_AUDIODRIVER=pulseaudio python3 -c "import pygame; pygame.mixer.init(); print('OK')"
```

If this fails, try:

```bash
# Restart PulseAudio
pulseaudio -k
pulseaudio --start

# Try the app again
python3 main.py
```

## Using the Music Player

Once Bluetooth is set up:

1. **Start the app:**
   ```bash
   cd ~/musicplayer  # or wherever you installed it
   python3 main.py
   ```

2. **Connect headphones:**
   - Navigate to Settings → Bluetooth Audio
   - Press SELECT on "Scan for devices"
   - Wait for scan to complete
   - Navigate to your headphones
   - Press SELECT to connect

3. **The app will automatically:**
   - Pair with the device (if needed)
   - Connect to it
   - Set it as the default audio sink
   - Route all music to your headphones

4. **Auto-reconnect:**
   - Once connected, the device is trusted
   - It will auto-reconnect when powered on in range

## PulseAudio + Bluetooth Architecture

```
┌─────────────────┐
│  Music Player   │
│   (pygame)      │
└────────┬────────┘
         │
         │ SDL_AUDIODRIVER=pulseaudio
         ▼
┌─────────────────┐
│  PulseAudio     │
│   (sound server)│
└────────┬────────┘
         │
         │ module-bluetooth-discover
         ▼
┌─────────────────┐
│  BlueZ          │
│   (Bluetooth)   │
└────────┬────────┘
         │
         │ A2DP profile
         ▼
┌─────────────────┐
│  Headphones     │
└─────────────────┘
```

The app bypasses ALSA entirely by:
1. Setting `SDL_AUDIODRIVER=pulseaudio` in [player/audio.py](player/audio.py:10)
2. PulseAudio handles all audio routing
3. When Bluetooth device connects, PulseAudio creates a `bluez_sink`
4. The app's BluetoothManager sets this as the default sink
5. All pygame audio automatically routes to Bluetooth

## Performance Tips

For best audio quality on Bluetooth:

1. **Disable WiFi power saving (can interfere with Bluetooth):**
   ```bash
   sudo iwconfig wlan0 power off
   ```

2. **Increase Bluetooth priority:**
   ```bash
   sudo nice -n -10 bluetoothd
   ```

3. **Use A2DP profile (not HSP/HFP):**
   - A2DP = high quality stereo
   - HSP/HFP = phone headset (mono, low quality)
   - The app automatically uses A2DP

## Common Issues

| Problem | Solution |
|---------|----------|
| Choppy audio | Increase pygame buffer: `pygame.mixer.init(buffer=8192)` in [player/audio.py](player/audio.py:14) |
| Connection drops | Move Pi closer to headphones, reduce WiFi interference |
| Scan finds 0 devices | Headphones in pairing mode? Bluetooth service running? |
| No audio | Check PulseAudio running, Bluetooth connected, default sink set |
| ALSA errors | Normal - app uses PulseAudio not ALSA |
