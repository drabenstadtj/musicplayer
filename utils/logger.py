"""
Centralized logging system for Music Player application
Provides structured logging with rotation and different log levels
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime

# Log directory
LOG_DIR = Path("/tmp/musicplayer_logs")
LOG_DIR.mkdir(exist_ok=True)

# Log files
MAIN_LOG = LOG_DIR / "musicplayer.log"
AUDIO_LOG = LOG_DIR / "audio.log"
UI_LOG = LOG_DIR / "ui.log"
HARDWARE_LOG = LOG_DIR / "hardware.log"
NETWORK_LOG = LOG_DIR / "network.log"

# Log format
LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Create formatters
formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

def setup_logger(name, log_file, level=logging.INFO):
    """
    Create a logger with file rotation

    Args:
        name: Logger name (e.g., "audio", "ui")
        log_file: Path to log file
        level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # File handler with rotation (max 5MB, keep 3 backups)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger

# Pre-configured loggers for different components
main_logger = setup_logger("main", MAIN_LOG, level=logging.INFO)
audio_logger = setup_logger("audio", AUDIO_LOG, level=logging.DEBUG)
ui_logger = setup_logger("ui", UI_LOG, level=logging.INFO)
hardware_logger = setup_logger("hardware", HARDWARE_LOG, level=logging.INFO)
network_logger = setup_logger("network", NETWORK_LOG, level=logging.DEBUG)

def log_startup():
    """Log application startup"""
    main_logger.info("=" * 60)
    main_logger.info("Music Player Application Started")
    main_logger.info(f"Timestamp: {datetime.now()}")
    main_logger.info("=" * 60)

def log_shutdown():
    """Log application shutdown"""
    main_logger.info("=" * 60)
    main_logger.info("Music Player Application Shutdown")
    main_logger.info(f"Timestamp: {datetime.now()}")
    main_logger.info("=" * 60)

def get_logger(component):
    """
    Get logger for a specific component

    Args:
        component: Component name ("main", "audio", "ui", "hardware", "network")

    Returns:
        Logger instance
    """
    loggers = {
        "main": main_logger,
        "audio": audio_logger,
        "ui": ui_logger,
        "hardware": hardware_logger,
        "network": network_logger
    }
    return loggers.get(component, main_logger)
