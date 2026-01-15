"""Windows system tray icon using pystray."""

import threading
from typing import TYPE_CHECKING, Optional

import pystray
from PIL import Image, ImageDraw

if TYPE_CHECKING:
    from windows.main import App


def create_icon_image(size: int = 64) -> Image.Image:
    """Create a simple terminal-like icon."""
    # Create a dark background with a terminal prompt symbol
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Draw a rounded rectangle background
    margin = 4
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=8,
        fill=(30, 30, 30, 255)
    )

    # Draw a ">" prompt symbol
    prompt_color = (100, 181, 246, 255)  # Light blue (matches provider color)
    center_x = size // 2
    center_y = size // 2
    prompt_size = size // 4

    # Draw the ">" shape
    points = [
        (center_x - prompt_size // 2, center_y - prompt_size // 2),
        (center_x + prompt_size // 2, center_y),
        (center_x - prompt_size // 2, center_y + prompt_size // 2),
    ]
    draw.polygon(points, fill=prompt_color)

    return image


class TrayIcon:
    """System tray icon with menu for controlling the overlay."""

    def __init__(self, app: "App"):
        self.app = app
        self._icon: Optional[pystray.Icon] = None
        self._thread: Optional[threading.Thread] = None

    def _create_menu(self) -> pystray.Menu:
        """Create the tray context menu."""
        return pystray.Menu(
            pystray.MenuItem(
                "Show/Hide Overlay",
                self._on_toggle_visibility,
                default=True  # Double-click action
            ),
            pystray.MenuItem(
                lambda item: f"Click-Through {'[ON]' if self.app.click_through else '[OFF]'}",
                self._on_toggle_click_through
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._on_quit)
        )

    def _on_toggle_visibility(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Handle toggle visibility menu action."""
        self.app.toggle_visibility()

    def _on_toggle_click_through(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Handle toggle click-through menu action."""
        self.app.toggle_click_through()
        # Update menu to reflect new state
        icon.update_menu()

    def _on_quit(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Handle quit menu action."""
        self.app.quit()

    def start(self) -> None:
        """Start the tray icon in a separate thread."""
        self._icon = pystray.Icon(
            "opencode-monitor",
            create_icon_image(),
            "OpenCode Monitor",
            menu=self._create_menu()
        )

        # Run in a separate thread so it doesn't block the main loop
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the tray icon."""
        if self._icon:
            self._icon.stop()

    def update_tooltip(self, session_count: int) -> None:
        """Update the tray icon tooltip."""
        if self._icon:
            if session_count == 0:
                self._icon.title = "OpenCode Monitor - No sessions"
            elif session_count == 1:
                self._icon.title = "OpenCode Monitor - 1 session"
            else:
                self._icon.title = f"OpenCode Monitor - {session_count} sessions"
