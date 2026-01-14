"""macOS menu bar icon implementation using NSStatusBar."""

from AppKit import (
    NSStatusBar, NSMenu, NSMenuItem, NSImage,
    NSVariableStatusItemLength
)
from Foundation import NSObject
import objc


class MenuBar(NSObject):
    """Menu bar item with actions."""

    def init_with_delegate(self, delegate):
        """Initialize menu bar with action delegate."""
        self = objc.super(MenuBar, self).init()
        if self is None:
            return None
        self.delegate = delegate
        self._setup()
        return self

    def _setup(self):
        """Create and configure the menu bar item."""
        self.status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(
            NSVariableStatusItemLength
        )

        button = self.status_item.button()

        icon = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
            "terminal.fill", "OpenCode Monitor"
        )
        if icon:
            icon.setTemplate_(True)
            button.setImage_(icon)
        else:
            button.setTitle_("●")

        menu = NSMenu.alloc().init()

        items = [
            ("Show/Hide Overlay", "toggleVisibility:", "h"),
            ("Toggle Click-Through", "toggleClickThrough:", "t"),
            None,
            ("Quit", "quitApp:", "q"),
        ]

        for item in items:
            if item is None:
                menu.addItem_(NSMenuItem.separatorItem())
            else:
                title, action, key = item
                menu_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                    title, action, key
                )
                menu_item.setTarget_(self.delegate)
                menu.addItem_(menu_item)

        self.status_item.setMenu_(menu)
