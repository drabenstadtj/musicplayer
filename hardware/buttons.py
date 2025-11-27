"""
GPIO Button Handler for Music Player
Handles 4 tactile buttons with debouncing and event callbacks
"""

import time
from enum import Enum
from typing import Callable, Dict, Optional
import threading

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO_AVAILABLE = False
    print("RPi.GPIO not available - button support disabled")


class Button(Enum):
    """Button definitions matching hardware GPIO pins"""
    UP = 17      # BTN1 - Navigate up
    DOWN = 22    # BTN2 - Navigate down
    SELECT = 23  # BTN3 - Select/Confirm
    BACK = 27    # BTN4 - Back/Cancel


class ButtonEvent(Enum):
    """Types of button events"""
    PRESS = "press"           # Button just pressed
    RELEASE = "release"       # Button just released
    LONG_PRESS = "long_press" # Button held for >1 second
    DOUBLE_PRESS = "double_press"  # Button pressed twice quickly


class ButtonHandler:
    """
    Manages GPIO buttons with debouncing and event callbacks.
    
    Usage:
        handler = ButtonHandler()
        handler.on_button(Button.SELECT, ButtonEvent.PRESS, lambda: print("Select!"))
        handler.start()
        # ... do other work ...
        handler.stop()
    """
    
    def __init__(self, debounce_time: float = 0.05, long_press_time: float = 1.0, 
                 double_press_time: float = 0.3):
        """
        Initialize button handler.
        
        Args:
            debounce_time: Minimum time between button state changes (seconds)
            long_press_time: Time to hold for long press event (seconds)
            double_press_time: Max time between presses for double press (seconds)
        """
        self.debounce_time = debounce_time
        self.long_press_time = long_press_time
        self.double_press_time = double_press_time
        
        self._callbacks: Dict[Button, Dict[ButtonEvent, list]] = {
            button: {event: [] for event in ButtonEvent}
            for button in Button
        }
        
        self._button_states: Dict[Button, bool] = {button: False for button in Button}
        self._last_press_time: Dict[Button, float] = {button: 0 for button in Button}
        self._last_release_time: Dict[Button, float] = {button: 0 for button in Button}
        self._press_count: Dict[Button, int] = {button: 0 for button in Button}
        
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        
        if GPIO_AVAILABLE:
            self._setup_gpio()
    
    def _setup_gpio(self):
        """Configure GPIO pins for buttons"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        for button in Button:
            # Use pull-up resistor, button connects to ground
            GPIO.setup(button.value, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            print(f"Configured {button.name} on GPIO {button.value}")
    
    def on_button(self, button: Button, event: ButtonEvent, callback: Callable):
        """
        Register a callback for a button event.
        
        Args:
            button: Which button to listen for
            event: What type of event to listen for
            callback: Function to call when event occurs (no arguments)
        """
        self._callbacks[button][event].append(callback)
    
    def remove_callback(self, button: Button, event: ButtonEvent, callback: Callable):
        """Remove a previously registered callback"""
        if callback in self._callbacks[button][event]:
            self._callbacks[button][event].remove(callback)
    
    def _trigger_callbacks(self, button: Button, event: ButtonEvent):
        """Execute all callbacks registered for this button/event combination"""
        for callback in self._callbacks[button][event]:
            try:
                callback()
            except Exception as e:
                print(f"Error in button callback: {e}")
    
    def _is_pressed(self, button: Button) -> bool:
        """Check if button is currently pressed (LOW = pressed with pull-up)"""
        if not GPIO_AVAILABLE:
            return False
        return GPIO.input(button.value) == GPIO.LOW
    
    def _monitor_buttons(self):
        """Main monitoring loop - runs in background thread"""
        while self._running:
            current_time = time.time()
            
            for button in Button:
                is_pressed = self._is_pressed(button)
                was_pressed = self._button_states[button]
                
                # State change detected
                if is_pressed != was_pressed:
                    # Debounce check
                    if is_pressed:
                        # Button press
                        time_since_last_press = current_time - self._last_press_time[button]
                        
                        if time_since_last_press >= self.debounce_time:
                            self._button_states[button] = True
                            self._last_press_time[button] = current_time
                            
                            # Check for double press
                            time_since_last_release = current_time - self._last_release_time[button]
                            if time_since_last_release < self.double_press_time:
                                self._press_count[button] += 1
                                if self._press_count[button] == 2:
                                    self._trigger_callbacks(button, ButtonEvent.DOUBLE_PRESS)
                                    self._press_count[button] = 0
                            else:
                                self._press_count[button] = 1
                            
                            # Trigger press event
                            self._trigger_callbacks(button, ButtonEvent.PRESS)
                    else:
                        # Button release
                        time_since_last_release = current_time - self._last_release_time[button]
                        
                        if time_since_last_release >= self.debounce_time:
                            self._button_states[button] = False
                            self._last_release_time[button] = current_time
                            
                            # Trigger release event
                            self._trigger_callbacks(button, ButtonEvent.RELEASE)
                
                # Check for long press
                elif is_pressed:
                    time_held = current_time - self._last_press_time[button]
                    if time_held >= self.long_press_time:
                        # Only trigger once per long press
                        if time_held < self.long_press_time + 0.1:
                            self._trigger_callbacks(button, ButtonEvent.LONG_PRESS)
            
            # Small sleep to prevent CPU spinning
            time.sleep(0.01)
    
    def start(self):
        """Start monitoring buttons in background thread"""
        if not GPIO_AVAILABLE:
            print("Cannot start button monitoring - GPIO not available")
            return
        
        if self._running:
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_buttons, daemon=True)
        self._monitor_thread.start()
        print("Button monitoring started")
    
    def stop(self):
        """Stop monitoring buttons and cleanup GPIO"""
        self._running = False
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
        
        if GPIO_AVAILABLE:
            GPIO.cleanup()
        
        print("Button monitoring stopped")
    
    def is_running(self) -> bool:
        """Check if button monitoring is active"""
        return self._running
    
    def get_button_state(self, button: Button) -> bool:
        """Get current state of a button (True = pressed)"""
        return self._button_states[button]


# Keyboard fallback for development/testing
class KeyboardButtonEmulator:
    """
    Emulates button events using keyboard input for testing without GPIO.
    Maps arrow keys and other keys to button events.
    """
    
    # Keyboard to Button mapping
    KEY_MAP = {
        'KEY_UP': Button.UP,
        'KEY_DOWN': Button.DOWN,
        '\n': Button.SELECT,  # Enter key
        'KEY_BACKSPACE': Button.BACK,
        '\x7f': Button.BACK,  # Delete key (alternative backspace)
    }
    
    def __init__(self):
        self._callbacks: Dict[Button, Dict[ButtonEvent, list]] = {
            button: {event: [] for event in ButtonEvent}
            for button in Button
        }
    
    def on_button(self, button: Button, event: ButtonEvent, callback: Callable):
        """Register a callback for a button event"""
        self._callbacks[button][event].append(callback)
    
    def remove_callback(self, button: Button, event: ButtonEvent, callback: Callable):
        """Remove a previously registered callback"""
        if callback in self._callbacks[button][event]:
            self._callbacks[button][event].remove(callback)
    
    def handle_key(self, key: str):
        """
        Process a keyboard key and trigger appropriate button callbacks.
        Called from main curses event loop.
        """
        button = self.KEY_MAP.get(key)
        if button:
            # Trigger press event for matched button
            for callback in self._callbacks[button][ButtonEvent.PRESS]:
                try:
                    callback()
                except Exception as e:
                    print(f"Error in button callback: {e}")
    
    def start(self):
        """No-op for compatibility with ButtonHandler"""
        pass
    
    def stop(self):
        """No-op for compatibility with ButtonHandler"""
        pass
    
    def is_running(self) -> bool:
        """Always returns True for compatibility"""
        return True


# Factory function to get appropriate handler
def get_button_handler(use_gpio: bool = True) -> ButtonHandler | KeyboardButtonEmulator:
    """
    Get appropriate button handler based on environment.
    
    Args:
        use_gpio: Try to use GPIO buttons if available
    
    Returns:
        ButtonHandler if GPIO available and use_gpio=True,
        KeyboardButtonEmulator otherwise
    """
    if use_gpio and GPIO_AVAILABLE:
        return ButtonHandler()
    else:
        print("Using keyboard emulation for buttons")
        return KeyboardButtonEmulator()


if __name__ == "__main__":
    # Test program
    print("Button Test Program")
    print("=" * 50)
    
    handler = get_button_handler()
    
    # Register test callbacks
    handler.on_button(Button.UP, ButtonEvent.PRESS, 
                     lambda: print("UP pressed"))
    handler.on_button(Button.DOWN, ButtonEvent.PRESS, 
                     lambda: print("DOWN pressed"))
    handler.on_button(Button.SELECT, ButtonEvent.PRESS, 
                     lambda: print("SELECT pressed"))
    handler.on_button(Button.BACK, ButtonEvent.PRESS, 
                     lambda: print("BACK pressed"))
    handler.on_button(Button.SELECT, ButtonEvent.LONG_PRESS, 
                     lambda: print("SELECT held (long press)"))
    handler.on_button(Button.UP, ButtonEvent.DOUBLE_PRESS, 
                     lambda: print("UP double pressed"))
    
    if isinstance(handler, ButtonHandler):
        handler.start()
        print("\nMonitoring GPIO buttons. Press Ctrl+C to exit...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            handler.stop()
    else:
        print("\nGPIO not available - use keyboard emulation in your main app")
