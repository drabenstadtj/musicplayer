import curses
import config

# Screen dimensions
SCREEN_WIDTH = config.SCREEN_WIDTH
SCREEN_HEIGHT = config.SCREEN_HEIGHT

# Layout measurements (in lines for ncurses, not pixels)
STATUS_BAR_LINES = 1
FOOTER_LINES = 1
CONTENT_LINES = 20  # Adjust based on your terminal

# Color pair IDs (not the actual pairs - those are created in init_colors)
COLOR_NORMAL = 1
COLOR_SELECTED = 2
COLOR_STATUS = 3
COLOR_PLAYING = 4

# Initialize color pairs - call this after curses.initscr()
def init_colors():
    """Initialize color pairs for the UI"""
    curses.init_pair(COLOR_NORMAL, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(COLOR_SELECTED, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(COLOR_STATUS, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(COLOR_PLAYING, curses.COLOR_GREEN, curses.COLOR_BLACK)

# UI Symbols
SYMBOL_PLAYING = "▶"
SYMBOL_PAUSED = "⏸"
SYMBOL_SHUFFLE = "🔀"
SYMBOL_REPEAT = "🔁"
SYMBOL_BATTERY = "🔋"
SYMBOL_MUSIC = "♪"