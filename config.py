# Navidrome server configuration
NAVIDROME_URL = "https://listen.wintermute.lol"
NAVIDROME_USER = "jack"
NAVIDROME_PASS = "crypt0"

# Display settings
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 240

# UI Layout (in pixels)
STATUS_BAR_HEIGHT = 20
FOOTER_HEIGHT = 20
CONTENT_HEIGHT = SCREEN_HEIGHT - STATUS_BAR_HEIGHT - FOOTER_HEIGHT

# Split view widths
LEFT_PANEL_WIDTH = 160
RIGHT_PANEL_WIDTH = 160

# Now Playing layout
ALBUM_ART_SIZE = 180
PROGRESS_BAR_HEIGHT = 30

# Colors (curses color pair numbers)
COLOR_NORMAL = 1
COLOR_SELECTED = 2
COLOR_STATUS = 3
COLOR_PROGRESS = 4

# Button GPIO pins (for later)
BTN_UP = 17
BTN_DOWN = 22
BTN_SELECT = 23
BTN_BACK = 27

# Battery monitoring
LBO_PIN = 4  # PowerBoost Low Battery Output

# Playback settings
DEFAULT_VOLUME = 70
BUFFER_SIZE = 8192
