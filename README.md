# Raspberry Pi Portable Music Player

A portable music player built with Raspberry Pi Zero 2W that streams from Navidrome server with a 2.2" TFT display and I2S audio output.

## Hardware Components

- **Raspberry Pi Zero 2W** - Main computer
- **Adafruit PiTFT 2.2" HAT (320x240, no touch)** [ID:2315] - Display
- **Adafruit I2S Stereo Decoder - UDA1334A** [ID:3678] - DAC for audio output
- **PowerBoost 1000 Charger** [ID:2465] - Battery management and 5V boost
- **Lithium Ion Polymer Battery 3.7v 2500mAh** [ID:328] - Power source
- **Stacking Header 2x20 Extra Tall** [ID:1979] - For connecting HAT and components
- **Brass M2.5 Standoffs** [ID:2336] - Mounting hardware
- **4 tactile buttons** - User input (GPIO 17, 22, 23, 27)

## Hardware Connections

### I2S DAC (UDA1334A)
```
VIN  → 3.3V (pin 1)
GND  → Ground (pin 6)
WSEL → GPIO 19 (pin 35, I2S Frame Sync)
DIN  → GPIO 21 (pin 40, I2S Data)
BCLK → GPIO 18 (pin 12, I2S Bit Clock)
```

### PiTFT 2.2" Display
- Mounts directly on stacking header
- Uses SPI interface (automatically configured)

### PowerBoost 1000C
- Battery → JST connector on PowerBoost
- USB input → Micro USB on PowerBoost (for charging)
- 5V output → Pi GPIO pins 2 or 4 (5V) and pin 6 (GND)
- LBO pin → GPIO 4 (optional, for battery monitoring)

### Buttons (to be implemented)
```
BTN1 (Up)     → GPIO 17
BTN2 (Down)   → GPIO 22
BTN3 (Select) → GPIO 23
BTN4 (Back)   → GPIO 27
```

## Software Architecture

```
musicplayer/
├── main.py              # Entry point, curses setup
├── config.py            # Configuration (reads from .env)
├── .env                 # Credentials (NOT in git)
├── ui/
│   ├── screens.py       # Screen classes (Menu, Browser, NowPlaying)
│   ├── widgets.py       # Reusable UI components
│   └── theme.py         # Colors, fonts, layout constants
├── player/
│   ├── navidrome.py     # Navidrome API client
│   ├── audio.py         # Audio playback (pygame)
│   └── queue.py         # Playback queue (to be implemented)
├── hardware/
│   ├── buttons.py       # GPIO button handling (to be implemented)
│   └── battery.py       # Battery monitoring (to be implemented)
└── setup/
    ├── config_backups/  # Hardware config backups
    ├── restore_configs.sh
    ├── SETUP.md         # Detailed setup instructions
    └── REIMAGING_CHECKLIST.md
```

## Installation

### Quick Start (Pre-configured SD Card)

1. **Clone repository:**
   ```bash
   git clone git@github.com:YOUR_USERNAME/musicplayer.git
   cd musicplayer
   ```

2. **Restore hardware configuration:**
   ```bash
   sudo ./setup/restore_configs.sh
   sudo reboot
   ```

3. **Install dependencies:**
   ```bash
   python3 -m venv env --system-site-packages
   source env/bin/activate
   pip install -r requirements.txt
   ```

4. **Configure credentials:**
   ```bash
   cp .env.example .env
   nano .env
   # Add your Navidrome server URL, username, and password
   ```

5. **Run:**
   ```bash
   python main.py
   ```

### Fresh Installation (See setup/SETUP.md)

For complete step-by-step instructions on setting up from a fresh Raspberry Pi OS Lite image, see [setup/SETUP.md](setup/SETUP.md).

## Hardware Configuration Files

### `/boot/firmware/config.txt`
```bash
# I2S DAC
dtparam=audio=off
dtoverlay=hifiberry-dac

# PiTFT 2.2" Display
dtoverlay=pitft22,rotate=270,speed=64000000,fps=30
```

### `/boot/firmware/cmdline.txt`
Add to end of line:
```
fbcon=map:10 fbcon=font:VGA8x8
```

### `/etc/asound.conf`
ALSA configuration to route audio to I2S DAC (card 1). See `setup/config_backups/asound.conf`.

## Usage

### Current Features (Phase 3)
- ✅ Browse albums from Navidrome server
- ✅ Stream and play music through I2S DAC
- ✅ Volume control (↑/↓ arrows)
- ✅ Pause/play (Spacebar)
- ✅ Navigation with keyboard

### Keyboard Controls
```
Main Menu:
  ↑/↓        - Navigate menu
  ENTER      - Select option
  Q          - Quit

Album Browser:
  ↑/↓        - Navigate lists
  ENTER      - Select album / Play song
  BACKSPACE  - Go back
  Q          - Quit

Now Playing:
  SPACE      - Play / Pause
  ↑/↓        - Volume up / down
  BACKSPACE  - Return to browser
  Q          - Quit
```

## Planned Features (Future Phases)

### Phase 4: Hardware Integration
- [ ] GPIO button support (replace keyboard)
- [ ] Battery level monitoring
- [ ] Power management

### Phase 5: Advanced Features
- [ ] Playlist support
- [ ] Queue management
- [ ] Shuffle/repeat modes
- [ ] Album art display
- [ ] Settings menu

### Phase 6: Polish
- [ ] Auto-start on boot
- [ ] Sleep timer
- [ ] Display timeout/dimming
- [ ] Safe shutdown on low battery

## Development

### Requirements
- Python 3.9+
- pygame
- requests
- python-dotenv

### Environment Variables (.env)
```bash
NAVIDROME_URL=https://your-server.com
NAVIDROME_USER=username
NAVIDROME_PASS=password
```

### Testing Audio
```bash
# Test I2S DAC
speaker-test -c2 -t wav

# Check audio devices
aplay -l

# Should show:
# card 1: sndrpihifiberry [snd_rpi_hifiberry_dac]
```

### Testing Display
```bash
# Display should show console after boot
# Run music player to see ncurses interface
python main.py
```

