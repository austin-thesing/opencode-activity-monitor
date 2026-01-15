"""Windows overlay window using tkinter with Win32 extensions."""

import ctypes
import tkinter as tk
from tkinter import font as tkfont
from typing import List, Optional, Callable

from src.config import CONFIG
from src.opencode_data import Session


# Win32 constants
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20
WS_EX_TOOLWINDOW = 0x80
WS_EX_TOPMOST = 0x8
WS_EX_NOACTIVATE = 0x08000000

user32 = ctypes.windll.user32


def get_window_handle(window: tk.Tk) -> int:
    """Get the Win32 HWND from a tkinter window."""
    return int(window.wm_frame(), 16)


def set_window_ex_style(hwnd: int, add_styles: int = 0, remove_styles: int = 0) -> None:
    """Modify extended window styles."""
    current = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    new_style = (current | add_styles) & ~remove_styles
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)


class OverlayWindow:
    """Transparent overlay window for displaying OpenCode sessions."""

    def __init__(self, on_position_change: Optional[Callable] = None):
        self.on_position_change = on_position_change
        self.click_through = CONFIG["behavior"]["click_through"]
        self.visible = True
        self.sessions: List[Session] = []

        # Window configuration from config
        self.width = CONFIG["appearance"]["width"]
        self.bg_opacity = CONFIG["appearance"]["background_opacity"]
        self.text_opacity = CONFIG["appearance"]["text_opacity"]

        # Colors from config
        self.colors = {
            "ok": CONFIG["colors"]["ok"],
            "warning": CONFIG["colors"]["warning"],
            "critical": CONFIG["colors"]["critical"],
            "provider": CONFIG["colors"]["provider"],
        }

        # Parse background color (RGB format: "10, 12, 16")
        bg_rgb = CONFIG["colors"]["background"]
        if isinstance(bg_rgb, str):
            r, g, b = [int(x.strip()) for x in bg_rgb.split(",")]
        else:
            r, g, b = 10, 12, 16
        self.bg_color = f"#{r:02x}{g:02x}{b:02x}"

        # Transparent color key (must be different from bg_color)
        self.transparent_color = "#010101"

        self._create_window()

    def _create_window(self) -> None:
        """Create the overlay window."""
        self.root = tk.Tk()
        self.root.title("OpenCode Monitor")

        # Remove window decorations
        self.root.overrideredirect(True)

        # Set window attributes
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", self.bg_opacity)

        # Calculate initial position based on config
        anchor = CONFIG["position"]["anchor"]
        margin_top = CONFIG["position"]["margin_top"]
        margin_right = CONFIG["position"]["margin_right"]
        margin_left = CONFIG["position"]["margin_left"]

        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Initial height estimate
        initial_height = 150

        # Calculate position based on anchor
        if "right" in anchor:
            x = screen_width - self.width - margin_right
        else:
            x = margin_left

        if "bottom" in anchor:
            y = screen_height - initial_height - CONFIG["position"]["margin_bottom"]
        else:
            y = margin_top

        self.root.geometry(f"{self.width}x{initial_height}+{x}+{y}")

        # Create main frame with background
        self.main_frame = tk.Frame(self.root, bg=self.bg_color)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Create header
        self._create_header()

        # Create session list container
        self.session_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        self.session_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Bind drag events when not in click-through mode
        self._setup_drag()

        # Apply Win32 styles after window is created
        self.root.update_idletasks()
        self.hwnd = get_window_handle(self.root)

        # Set as tool window (no taskbar icon) and layered
        set_window_ex_style(
            self.hwnd,
            add_styles=WS_EX_TOOLWINDOW | WS_EX_LAYERED | WS_EX_NOACTIVATE
        )

        if self.click_through:
            self._apply_click_through(True)

    def _create_header(self) -> None:
        """Create the header section."""
        header_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        # Title
        title_font = tkfont.Font(family="Consolas", size=11, weight="bold")
        title_label = tk.Label(
            header_frame,
            text="OPENCODE",
            font=title_font,
            fg=self.colors["provider"],
            bg=self.bg_color
        )
        title_label.pack(side=tk.LEFT)

        # Separator
        separator = tk.Frame(self.main_frame, bg="#333333", height=1)
        separator.pack(fill=tk.X, padx=10, pady=(0, 5))

    def _setup_drag(self) -> None:
        """Setup window dragging."""
        self._drag_data = {"x": 0, "y": 0}

        def start_drag(event):
            if not self.click_through:
                self._drag_data["x"] = event.x
                self._drag_data["y"] = event.y

        def do_drag(event):
            if not self.click_through:
                x = self.root.winfo_x() + (event.x - self._drag_data["x"])
                y = self.root.winfo_y() + (event.y - self._drag_data["y"])
                self.root.geometry(f"+{x}+{y}")
                if self.on_position_change:
                    self.on_position_change(x, y)

        self.root.bind("<Button-1>", start_drag)
        self.root.bind("<B1-Motion>", do_drag)
        self.main_frame.bind("<Button-1>", start_drag)
        self.main_frame.bind("<B1-Motion>", do_drag)

    def _apply_click_through(self, enable: bool) -> None:
        """Apply or remove click-through mode using Win32 API."""
        if enable:
            set_window_ex_style(self.hwnd, add_styles=WS_EX_TRANSPARENT)
        else:
            set_window_ex_style(self.hwnd, remove_styles=WS_EX_TRANSPARENT)

    def toggle_click_through(self) -> bool:
        """Toggle click-through mode. Returns new state."""
        self.click_through = not self.click_through
        self._apply_click_through(self.click_through)
        return self.click_through

    def toggle_visibility(self) -> bool:
        """Toggle window visibility. Returns new state."""
        self.visible = not self.visible
        if self.visible:
            self.root.deiconify()
            self.root.attributes("-topmost", True)
        else:
            self.root.withdraw()
        return self.visible

    def show(self) -> None:
        """Show the window."""
        self.visible = True
        self.root.deiconify()
        self.root.attributes("-topmost", True)

    def hide(self) -> None:
        """Hide the window."""
        self.visible = False
        self.root.withdraw()

    def update_sessions(self, sessions: List[Session]) -> None:
        """Update the displayed sessions."""
        self.sessions = sessions

        # Clear existing session widgets
        for widget in self.session_frame.winfo_children():
            widget.destroy()

        if not sessions:
            # Show "No active sessions" message
            no_sessions_font = tkfont.Font(family="Consolas", size=9)
            no_sessions = tk.Label(
                self.session_frame,
                text="No active sessions",
                font=no_sessions_font,
                fg="#666666",
                bg=self.bg_color
            )
            no_sessions.pack(pady=10)
        else:
            # Create row for each session
            session_font = tkfont.Font(family="Consolas", size=9)

            for session in sessions:
                row_frame = tk.Frame(self.session_frame, bg=self.bg_color)
                row_frame.pack(fill=tk.X, pady=1)

                # Status color
                status_color = self._get_status_color(session.status)

                # Project name (truncated if needed)
                project_name = session.project[:25] if len(session.project) > 25 else session.project
                project_label = tk.Label(
                    row_frame,
                    text=project_name.ljust(26),
                    font=session_font,
                    fg="#cccccc",
                    bg=self.bg_color,
                    anchor="w"
                )
                project_label.pack(side=tk.LEFT)

                # Status
                status_label = tk.Label(
                    row_frame,
                    text=session.status.center(8),
                    font=session_font,
                    fg=status_color,
                    bg=self.bg_color
                )
                status_label.pack(side=tk.LEFT)

                # Time
                time_label = tk.Label(
                    row_frame,
                    text=session.last_active_fmt.rjust(6),
                    font=session_font,
                    fg="#888888",
                    bg=self.bg_color
                )
                time_label.pack(side=tk.LEFT)

        # Resize window to fit content
        self._resize_to_fit()

    def _get_status_color(self, status: str) -> str:
        """Get the color for a status."""
        status_colors = {
            "active": self.colors["ok"],
            "idle": self.colors["warning"],
            "stale": self.colors["critical"],
        }
        return status_colors.get(status, "#888888")

    def _resize_to_fit(self) -> None:
        """Resize window to fit content."""
        self.root.update_idletasks()

        # Calculate required height
        header_height = 50  # Approximate header + separator height
        session_height = max(len(self.sessions), 1) * 22  # Per-session row height
        padding = 20

        new_height = header_height + session_height + padding
        new_height = max(new_height, 80)  # Minimum height

        # Get current position
        current_x = self.root.winfo_x()
        current_y = self.root.winfo_y()

        self.root.geometry(f"{self.width}x{new_height}+{current_x}+{current_y}")

    def close(self) -> None:
        """Close the window."""
        self.root.quit()
        self.root.destroy()

    def update(self) -> None:
        """Process pending events (call from main loop)."""
        self.root.update()
