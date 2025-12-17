"""
Button-to-UI Integration
Connects hardware buttons to UI navigation and player controls
"""

from hardware.buttons import Button, ButtonEvent, get_button_handler
from utils.logger import get_logger

logger = get_logger("hardware")


class ButtonController:
    """
    Maps button events to UI actions based on current screen/state.
    Acts as the glue between hardware buttons and UI screens.
    """
    
    def __init__(self, app, use_gpio=True):
        """
        Initialize button controller.

        Args:
            app: Main application instance with current_screen
            use_gpio: Whether to use GPIO or keyboard fallback
        """
        self.app = app
        self.handler = get_button_handler(use_gpio=use_gpio)
        self.button_states = {Button.UP: False, Button.DOWN: False, Button.SELECT: False, Button.BACK: False}
        self._setup_bindings()
    
    def _setup_bindings(self):
        """Register button event handlers"""
        # UP button - navigate up in lists
        self.handler.on_button(Button.UP, ButtonEvent.PRESS, self._on_up)
        self.handler.on_button(Button.UP, ButtonEvent.RELEASE, lambda: self._on_release(Button.UP))

        # DOWN button - navigate down in lists
        self.handler.on_button(Button.DOWN, ButtonEvent.PRESS, self._on_down)
        self.handler.on_button(Button.DOWN, ButtonEvent.RELEASE, lambda: self._on_release(Button.DOWN))

        # SELECT button - confirm/play
        self.handler.on_button(Button.SELECT, ButtonEvent.PRESS, self._on_select)
        self.handler.on_button(Button.SELECT, ButtonEvent.RELEASE, lambda: self._on_release(Button.SELECT))

        # BACK button - go back/cancel
        self.handler.on_button(Button.BACK, ButtonEvent.PRESS, self._on_back)
        self.handler.on_button(Button.BACK, ButtonEvent.RELEASE, lambda: self._on_release(Button.BACK))

        # Long press BACK - quit application
        self.handler.on_button(Button.BACK, ButtonEvent.LONG_PRESS, self._on_back_long)
    
    def _get_current_screen(self):
        """Get the currently active screen"""
        if hasattr(self.app, 'current_screen'):
            return self.app.current_screen
        return None
    
    def _on_up(self):
        """Handle UP button press"""
        self.button_states[Button.UP] = True
        # Check for combo: UP + BACK (return to now playing)
        if self.button_states[Button.BACK]:
            self._on_now_playing_combo()
            return

        # Check for combo: UP + SELECT (category jump in artist browser)
        if self.button_states[Button.SELECT]:
            self._on_category_jump_combo()
            return

        screen = self._get_current_screen()
        if screen and hasattr(screen, 'on_up'):
            screen.on_up()
    
    def _on_down(self):
        """Handle DOWN button press"""
        self.button_states[Button.DOWN] = True
        # Check for combo: DOWN + SELECT (category jump in artist browser)
        if self.button_states[Button.SELECT]:
            self._on_category_jump_combo()
            return

        screen = self._get_current_screen()
        if screen and hasattr(screen, 'on_down'):
            screen.on_down()

    def _on_select(self):
        """Handle SELECT button press"""
        self.button_states[Button.SELECT] = True
        # Check for combo: DOWN + SELECT or UP + SELECT (category jump in artist browser)
        if self.button_states[Button.DOWN] or self.button_states[Button.UP]:
            self._on_category_jump_combo()
            return

        screen = self._get_current_screen()
        if screen and hasattr(screen, 'on_select'):
            screen.on_select()
    
    def _on_back(self):
        """Handle BACK button press"""
        self.button_states[Button.BACK] = True
        # Check for combo: UP + BACK (BTN1 + BTN4)
        if self.button_states[Button.UP]:
            self._on_now_playing_combo()
            return

        screen = self._get_current_screen()
        if screen and hasattr(screen, 'on_back'):
            screen.on_back()
    
    def _on_back_long(self):
        """Handle long press of BACK button (quit app)"""
        if hasattr(self.app, 'quit'):
            self.app.quit()

    def _on_release(self, button):
        """Handle button release"""
        self.button_states[button] = False

    def _on_now_playing_combo(self):
        """Handle UP + BACK combo to return to now playing screen"""
        # Set a flag that the app can check
        if hasattr(self.app, 'return_to_now_playing'):
            self.app.return_to_now_playing()

    def _on_category_jump_combo(self):
        """Handle DOWN + SELECT combo to jump to next letter category"""
        logger.debug("Category jump combo pressed (DOWN + SELECT)")
        screen = self._get_current_screen()
        if screen and hasattr(screen, 'jump_to_next_category'):
            logger.info("Jumping to next letter category")
            screen.jump_to_next_category()
            # Redraw screen to show new position
            if hasattr(screen, 'draw'):
                screen.draw()

    def start(self):
        """Start button monitoring"""
        self.handler.start()

    def stop(self):
        """Stop button monitoring and cleanup"""
        self.handler.stop()