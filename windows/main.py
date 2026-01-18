"""Windows entry point for OpenCode Activity Monitor."""

import sys
import time
import threading
import queue
from typing import Optional

from src import opencode_data
from src.config import CONFIG
from windows.overlay import OverlayWindow
from windows.tray import TrayIcon


class App:
    """Main application controller."""

    def __init__(self):
        self.running = True
        self.click_through = CONFIG["behavior"]["click_through"]
        self.refresh_interval = CONFIG["monitor"]["refresh_interval_ms"] / 1000.0

        # Create overlay window
        self.overlay = OverlayWindow(on_position_change=self._on_position_change)

        # Create system tray icon
        self.tray = TrayIcon(self)

        # Timer for periodic refresh
        self._refresh_timer: Optional[threading.Timer] = None
        
        # Thread-safe queue for passing data from background thread to main thread
        self._data_queue: queue.Queue = queue.Queue()

    def _on_position_change(self, x: int, y: int) -> None:
        """Called when user drags the overlay window."""
        # Could save position to config here if needed
        pass

    def toggle_visibility(self) -> bool:
        """Toggle overlay visibility. Returns new state."""
        return self.overlay.toggle_visibility()

    def toggle_click_through(self) -> bool:
        """Toggle click-through mode. Returns new state."""
        self.click_through = self.overlay.toggle_click_through()
        return self.click_through

    def quit(self) -> None:
        """Quit the application."""
        self.running = False

        # Cancel refresh timer
        if self._refresh_timer:
            self._refresh_timer.cancel()

        # Stop tray icon
        self.tray.stop()

        # Close overlay window
        self.overlay.close()

    def _fetch_data_async(self) -> None:
        """Fetch data in background thread and put in queue for main thread."""
        if not self.running:
            return

        try:
            sessions = opencode_data.fetch_data()
            # Put data in queue for main thread to pick up
            self._data_queue.put(sessions)
        except Exception as e:
            print(f"Error fetching data: {e}", file=sys.stderr)

        # Schedule next refresh
        if self.running:
            self._refresh_timer = threading.Timer(self.refresh_interval, self._fetch_data_async)
            self._refresh_timer.daemon = True
            self._refresh_timer.start()

    def _check_queue(self) -> None:
        """Check queue for new data and update UI (called from main thread)."""
        try:
            while True:
                sessions = self._data_queue.get_nowait()
                self._update_ui(sessions)
        except queue.Empty:
            pass

    def _update_ui(self, sessions) -> None:
        """Update UI on main thread."""
        if not self.running:
            return
        try:
            self.overlay.update_sessions(sessions)
            self.tray.update_tooltip(len(sessions))
        except Exception as e:
            print(f"Error updating UI: {e}", file=sys.stderr)

    def _initial_refresh(self) -> None:
        """Do initial data fetch synchronously on main thread."""
        try:
            sessions = opencode_data.fetch_data()
            self.overlay.update_sessions(sessions)
            self.tray.update_tooltip(len(sessions))
        except Exception as e:
            print(f"Error during initial refresh: {e}", file=sys.stderr)

    def run(self) -> None:
        """Run the application main loop."""
        # Start the tray icon (runs in separate thread)
        self.tray.start()

        # Show the overlay first
        self.overlay.show()

        # Initial data fetch (synchronous, on main thread)
        self._initial_refresh()

        # Start background refresh timer
        self._refresh_timer = threading.Timer(self.refresh_interval, self._fetch_data_async)
        self._refresh_timer.daemon = True
        self._refresh_timer.start()

        # Main loop - process tkinter events
        try:
            while self.running:
                try:
                    # Check for new data from background thread
                    self._check_queue()
                    # Process tkinter events
                    self.overlay.update()
                    time.sleep(0.01)  # Small delay to prevent CPU spinning
                except Exception:
                    # Window was closed or destroyed
                    break
        except KeyboardInterrupt:
            pass
        finally:
            self.quit()


def main() -> None:
    """Entry point."""
    # Check platform
    if sys.platform != "win32":
        print("Error: This module is for Windows only.", file=sys.stderr)
        print("Use 'python -m macos.main' on macOS or 'python -m omarchy.main' on Linux.")
        sys.exit(1)

    print("Starting OpenCode Activity Monitor...")

    app = App()
    app.run()


if __name__ == "__main__":
    main()
