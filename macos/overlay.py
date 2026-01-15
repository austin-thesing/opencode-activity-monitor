"""macOS overlay window implementation using NSWindow."""

from AppKit import (
    NSWindow, NSView, NSTextField, NSFont, NSColor,
    NSBorderlessWindowMask, NSBackingStoreBuffered,
    NSFloatingWindowLevel, NSScreen, NSMakeRect,
    NSAttributedString, NSFontAttributeName,
    NSVisualEffectView, NSVisualEffectMaterial,
    NSVisualEffectBlendingMode
)
from Foundation import NSObject, NSString, NSRect

from src.config import CONFIG
from src.opencode_data import Session


class OverlayWindow:
    """Transparent overlay window for session display."""

    def __init__(self):
        self.click_through = CONFIG["behavior"]["click_through"]
        self.user_positioned = False  # Track if user has manually positioned the window
        self._create_window()
        self._create_content_view()

    def _create_window(self):
        """Create and configure the overlay window with glass effect."""
        from AppKit import NSAppearance
        
        # Initial dummy rect, will be positioned correctly on first show/refresh
        rect = NSMakeRect(0, 0, CONFIG["appearance"]["width"], 200)

        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect,
            NSBorderlessWindowMask,
            NSBackingStoreBuffered,
            False
        )

        corner_radius = CONFIG["appearance"]["corner_radius"]

        # Critical: window must be non-opaque with clear background for blur to work
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(NSColor.clearColor())
        self.window.setLevel_(NSFloatingWindowLevel)
        self.window.setIgnoresMouseEvents_(self.click_through)
        self.window.setHasShadow_(True)
        
        # Allow dragging when not in click-through mode
        self.window.setMovableByWindowBackground_(True)
        
        # Track expected position for detecting user drag
        self.expected_position = None
        
        # Force dark appearance for the window
        dark_appearance = NSAppearance.appearanceNamed_("NSAppearanceNameVibrantDark")
        if dark_appearance:
            self.window.setAppearance_(dark_appearance)
        
        # 1 << 0 is NSWindowCollectionBehaviorCanJoinAllSpaces
        # 1 << 7 is NSWindowCollectionBehaviorIgnoresCycle
        self.window.setCollectionBehavior_((1 << 0) | (1 << 7))

        # Create vibrancy/glass effect view
        content_bounds = self.window.contentView().bounds()
        self.effect_view = NSVisualEffectView.alloc().initWithFrame_(content_bounds)
        
        # Use dark material - HUDWindow (11) or Dark (2)
        # HUDWindow gives that dark translucent look
        self.effect_view.setMaterial_(2)  # Dark material
        
        # Blending mode: 0 = behindWindow (blur what's behind), 1 = withinWindow
        self.effect_view.setBlendingMode_(0)
        
        # State: 0 = followsWindowActiveState, 1 = active, 2 = inactive
        self.effect_view.setState_(1)  # Always active
        
        # Autoresizing mask: 18 = flexible width + height
        self.effect_view.setAutoresizingMask_(18)
        
        # Apply rounded corners via layer
        self.effect_view.setWantsLayer_(True)
        self.effect_view.layer().setCornerRadius_(corner_radius)
        self.effect_view.layer().setMasksToBounds_(True)
        
        # Add effect view as subview (not replacing content view)
        self.window.contentView().addSubview_(self.effect_view)
        self.window.contentView().setWantsLayer_(True)


    def _create_content_view(self):
        """Create the content view with text label."""
        bounds = self.effect_view.bounds()
        # Add some padding
        padding = 12
        label_rect = NSMakeRect(padding, padding, bounds.size.width - (padding * 2), bounds.size.height - (padding * 2))

        self.label = NSTextField.alloc().initWithFrame_(label_rect)
        self.label.setEditable_(False)
        self.label.setBezeled_(False)
        self.label.setDrawsBackground_(False)
        self.label.setSelectable_(False)
        self.label.setAlignment_(0)  # NSLeftTextAlignment
        # Enable wrapping for long project names
        self.label.cell().setLineBreakMode_(0)  # NSLineBreakByWordWrapping
        self.label.cell().setWraps_(True)
        
        # Add label on top of effect view
        self.effect_view.addSubview_(self.label)

    def _get_color(self, hex_color, alpha=1.0):
        """Convert hex color string to NSColor."""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, alpha)

    def update_sessions(self, sessions):
        """Update overlay content with session data in table format."""
        from AppKit import (
            NSMutableAttributedString, NSForegroundColorAttributeName, NSFontAttributeName,
            NSShadowAttributeName, NSShadow
        )

        colors = CONFIG["colors"]
        text_opacity = CONFIG["appearance"]["text_opacity"]
        font = NSFont.monospacedSystemFontOfSize_weight_(13, 0.0)
        header_font = NSFont.monospacedSystemFontOfSize_weight_(13, 0.6)

        # Create text shadow for better readability on light backgrounds
        shadow = NSShadow.alloc().init()
        shadow.setShadowColor_(NSColor.blackColor().colorWithAlphaComponent_(0.7))
        shadow.setShadowOffset_((0, -1))
        shadow.setShadowBlurRadius_(2)

        full_attr_string = NSMutableAttributedString.alloc().init()

        # Header with provider color
        header_color = self._get_color(colors["provider"])
        header_attr = {
            NSForegroundColorAttributeName: header_color,
            NSFontAttributeName: header_font,
            NSShadowAttributeName: shadow
        }
        header_str = NSAttributedString.alloc().initWithString_attributes_("OPENCODE\n", header_attr)
        full_attr_string.appendAttributedString_(header_str)

        if not sessions:
            none_color = NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.7)
            none_attr = {
                NSForegroundColorAttributeName: none_color,
                NSFontAttributeName: font,
                NSShadowAttributeName: shadow
            }
            none_str = NSAttributedString.alloc().initWithString_attributes_("No active sessions", none_attr)
            full_attr_string.appendAttributedString_(none_str)
        else:
            status_colors = {
                "active": self._get_color(colors["ok"]),
                "idle": self._get_color(colors["warning"]),
                "stale": self._get_color(colors["critical"])
            }

            # Calculate column widths for alignment
            max_title_len = 28

            for i, session in enumerate(sessions):
                # Session title in white (truncate if needed)
                title = session.title
                if len(title) > max_title_len:
                    title = title[:max_title_len - 1] + "…"
                
                title_color = NSColor.whiteColor()
                title_attr = {
                    NSForegroundColorAttributeName: title_color,
                    NSFontAttributeName: font,
                    NSShadowAttributeName: shadow
                }
                
                # Pad title to align status column
                padded_title = f"{title:<{max_title_len}}  "
                title_str = NSAttributedString.alloc().initWithString_attributes_(padded_title, title_attr)
                full_attr_string.appendAttributedString_(title_str)
                
                # Status word with color
                status_color = status_colors.get(session.status, NSColor.whiteColor())
                status_attr = {
                    NSForegroundColorAttributeName: status_color,
                    NSFontAttributeName: font,
                    NSShadowAttributeName: shadow
                }
                
                status_text = f"{session.status:<6}"
                status_str = NSAttributedString.alloc().initWithString_attributes_(status_text, status_attr)
                full_attr_string.appendAttributedString_(status_str)
                
                # Time in slightly dimmed color
                time_color = NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.8)
                time_attr = {
                    NSForegroundColorAttributeName: time_color,
                    NSFontAttributeName: font,
                    NSShadowAttributeName: shadow
                }
                time_text = f"  {session.last_active_fmt:>4}" if session.last_active_fmt else ""
                time_str = NSAttributedString.alloc().initWithString_attributes_(time_text, time_attr)
                full_attr_string.appendAttributedString_(time_str)

                # Add newline between sessions (except last)
                if i < len(sessions) - 1:
                    newline_str = NSAttributedString.alloc().initWithString_attributes_("\n", title_attr)
                    full_attr_string.appendAttributedString_(newline_str)

        self.label.setAttributedStringValue_(full_attr_string)
        self._resize_to_fit()


    def update_position(self, button_frame):
        """Update window position to be anchored to the menu bar icon (only if not user-positioned)."""
        # Check if window has been moved from expected position (user dragged it)
        if self.expected_position is not None and not self.user_positioned:
            current_frame = self.window.frame()
            expected_x, expected_y = self.expected_position
            # Allow small tolerance for floating point comparison
            if abs(current_frame.origin.x - expected_x) > 5 or abs(current_frame.origin.y - expected_y) > 5:
                self.user_positioned = True
        
        # Skip auto-positioning if user has manually positioned the window
        if self.user_positioned:
            return
            
        if not button_frame:
            return

        window_frame = self.window.frame()
        width = window_frame.size.width
        height = window_frame.size.height

        # Center the window under the button
        x = button_frame.origin.x + (button_frame.size.width / 2) - (width / 2)
        # Ensure it doesn't go off screen
        screen_frame = NSScreen.mainScreen().visibleFrame()
        if x < screen_frame.origin.x:
            x = screen_frame.origin.x
        elif x + width > screen_frame.origin.x + screen_frame.size.width:
            x = screen_frame.origin.x + screen_frame.size.width - width

        # Position just below the menu bar
        # In macOS coordinate system, y increases upwards
        y = button_frame.origin.y - height - 5

        new_rect = NSMakeRect(x, y, width, height)
        self.window.setFrame_display_animate_(new_rect, True, False)
        
        # Store expected position to detect user drag
        self.expected_position = (x, y)

    def _resize_to_fit(self):
        """Resize window to fit content and maintain position."""
        # Calculate height based on content
        line_count = self.label.attributedStringValue().string().count('\n') + 1
        line_height = 20  # Approximate line height for font size 13
        padding = 12
        height = (line_count * line_height) + (padding * 2) + 8  # Extra for header

        current_frame = self.window.frame()
        width = current_frame.size.width
        
        # Keep the top-center point fixed when resizing
        new_x = current_frame.origin.x
        new_y = current_frame.origin.y + (current_frame.size.height - height)
        
        new_rect = NSMakeRect(new_x, new_y, width, height)
        self.window.setFrame_display_animate_(new_rect, True, False)
        
        # Update effect view to fill window content area
        content_bounds = self.window.contentView().bounds()
        self.effect_view.setFrame_(content_bounds)
        
        # Update label frame within effect view
        self.label.setFrame_(NSMakeRect(padding, padding, width - (padding * 2), height - (padding * 2)))


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
