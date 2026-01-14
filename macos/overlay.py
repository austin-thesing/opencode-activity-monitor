"""macOS overlay window implementation using NSWindow."""

from AppKit import (
    NSWindow, NSView, NSTextField, NSFont, NSColor,
    NSBorderlessWindowMask, NSBackingStoreBuffered,
    NSFloatingWindowLevel, NSScreen, NSMakeRect,
    NSAttributedString, NSFontAttributeName
)
from Foundation import NSObject, NSString

from src.config import CONFIG
from src.opencode_data import Session


class OverlayWindow:
    """Transparent overlay window for session display."""

    def __init__(self):
        self.click_through = CONFIG["behavior"]["click_through"]
        self._create_window()
        self._create_content_view()

    def _create_window(self):
        """Create and configure the overlay window."""
        screen = NSScreen.mainScreen()
        frame = screen.visibleFrame()

        width = CONFIG["appearance"]["width"]
        height = 200

        anchor = CONFIG["position"]["anchor"]
        margins = CONFIG["position"]

        if "right" in anchor:
            x = frame.origin.x + frame.size.width - width - margins["margin_right"]
        else:
            x = frame.origin.x + margins["margin_left"]

        if "bottom" in anchor:
            y = frame.origin.y + margins["margin_bottom"]
        else:
            y = frame.origin.y + frame.size.height - height - margins["margin_top"]

        rect = NSMakeRect(x, y, width, height)

        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect,
            NSBorderlessWindowMask,
            NSBackingStoreBuffered,
            False
        )

        bg_rgb = CONFIG["colors"]["background"]
        r, g, b = [int(x.strip()) / 255.0 for x in bg_rgb.split(",")]
        opacity = CONFIG["appearance"]["background_opacity"]

        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(
            NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, opacity)
        )
        self.window.setLevel_(NSFloatingWindowLevel)
        self.window.setIgnoresMouseEvents_(self.click_through)
        self.window.setHasShadow_(False)
        self.window.setCollectionBehavior_((1 << 0) | (1 << 7))

    def _create_content_view(self):
        """Create the content view with text label."""
        bounds = self.window.contentView().bounds()

        self.label = NSTextField.alloc().initWithFrame_(bounds)
        self.label.setEditable_(False)
        self.label.setBezeled_(False)
        self.label.setDrawsBackground_(False)
        self.label.setTextColor_(
            NSColor.colorWithCalibratedWhite_alpha_(1.0, CONFIG["appearance"]["text_opacity"])
        )
        self.label.setFont_(NSFont.monospacedSystemFontOfSize_weight_(11, 0.0))

        self.window.contentView().addSubview_(self.label)

    def update_sessions(self, sessions):
        """Update overlay content with session data."""
        if not sessions:
            self.label.setStringValue_("No active sessions")
            self._resize_to_fit()
            return

        colors = CONFIG["colors"]
        status_symbols = {"active": "●", "idle": "○", "stale": "◌"}
        status_colors = {
            "active": colors["ok"],
            "idle": colors["warning"],
            "stale": colors["critical"]
        }

        lines = [f"OPENCODE\n{'─' * 30}"]
        for session in sessions:
            symbol = status_symbols.get(session.status, "?")
            color_hex = status_colors.get(session.status, "#ffffff")
            lines.append(f"{symbol} {session.project:<20} {session.last_active_fmt:>6}")

        self.label.setStringValue_("\n".join(lines))
        self._resize_to_fit()

    def _resize_to_fit(self):
        """Resize window to fit content."""
        text = self.label.stringValue()
        if text:
            font = self.label.font()
            text_height = text.count('\n') * int(font.defaultLineHeightForFont_() + 2)
            height = max(100, text_height + 20)

            current_frame = self.window.frame()
            anchor = CONFIG["position"]["anchor"]
            margins = CONFIG["position"]

            if "bottom" in anchor:
                new_y = current_frame.origin.y
            else:
                new_y = current_frame.origin.y + (current_frame.size.height - height)

            new_rect = NSMakeRect(
                current_frame.origin.x,
                new_y,
                current_frame.size.width,
                height
            )

            self.window.setFrame_display_animate_(new_rect, True, False)

    def toggle_visibility(self):
        """Toggle overlay visibility."""
        if self.window.isVisible():
            self.window.orderOut_(None)
        else:
            self.window.orderFrontRegardless()

    def toggle_click_through(self):
        """Toggle click-through mode."""
        self.click_through = not self.click_through
        self.window.setIgnoresMouseEvents_(self.click_through)

    def show(self):
        """Show the overlay window."""
        self.window.orderFrontRegardless()

    def hide(self):
        """Hide the overlay window."""
        self.window.orderOut_(None)
