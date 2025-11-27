"""
Button-to-UI Integration
Connects hardware buttons to UI navigation and player controls
"""

from hardware.buttons import Button, ButtonEvent, get_button_handler


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
        self._setup_bindings()
    
    def _setup_bindings(self):
        """Register button event handlers"""
        # UP button - navigate up in lists
        self.handler.on_button(Button.UP, ButtonEvent.PRESS, self._on_up)
        
        # DOWN button - navigate down in lists
        self.handler.on_button(Button.DOWN, ButtonEvent.PRESS, self._on_down)
        
        # SELECT button - confirm/play
        self.handler.on_button(Button.SELECT, ButtonEvent.PRESS, self._on_select)
        
        # BACK button - go back/cancel
        self.handler.on_button(Button.BACK, ButtonEvent.PRESS, self._on_back)
        
        # Long press BACK - quit application
        self.handler.on_button(Button.BACK, ButtonEvent.LONG_PRESS, self._on_back_long)
    
    def _get_current_screen(self):
        """Get the currently active screen"""
        if hasattr(self.app, 'current_screen'):
            return self.app.current_screen
        return None
    
    def _on_up(self):
        """Handle UP button press"""
        screen = self._get_current_screen()
        if screen and hasattr(screen, 'on_up'):
            screen.on_up()
    
    def _on_down(self):
        """Handle DOWN button press"""
        screen = self._get_current_screen()
        if screen and hasattr(screen, 'on_down'):
            screen.on_down()
    
    def _on_select(self):
        """Handle SELECT button press"""
        screen = self._get_current_screen()
        if screen and hasattr(screen, 'on_select'):
            screen.on_select()
    
    def _on_back(self):
        """Handle BACK button press"""
        screen = self._get_current_screen()
        if screen and hasattr(screen, 'on_back'):
            screen.on_back()
    
    def _on_back_long(self):
        """Handle long press of BACK button (quit app)"""
        if hasattr(self.app, 'quit'):
            self.app.quit()
    
    def start(self):
        """Start button monitoring"""
        self.handler.start()
    
    def stop(self):
        """Stop button monitoring and cleanup"""
        self.handler.stop()