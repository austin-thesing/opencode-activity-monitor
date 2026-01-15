#!/usr/bin/env python3
"""macOS menu bar app for OpenCode session monitoring."""

from AppKit import (
    NSApplication, NSTimer, NSRunLoop, NSDefaultRunLoopMode,
    NSApplicationActivationPolicyAccessory
)
from Foundation import NSObject, NSDate
from PyObjCTools import AppHelper
import objc

from src.config import CONFIG
from src import opencode_data
from macos.overlay import OverlayWindow
from macos.menu_bar import MenuBar


class AppDelegate(NSObject):
    """Application delegate for macOS menu bar app."""

    def init(self):
        """Initialize app delegate."""
        self = objc.super(AppDelegate, self).init()
        if self is None:
            return None
        self.overlay = None
        self.menu_bar = None
        self.timer = None
        return self

    def applicationDidFinishLaunching_(self, notification):
        """Called when app finishes launching."""
        NSApplication.sharedApplication().setActivationPolicy_(
            NSApplicationActivationPolicyAccessory
        )

        self.overlay = OverlayWindow()
        self.overlay.show()

        self.menu_bar = MenuBar.alloc().init_with_delegate(self)

        interval = CONFIG["monitor"]["refresh_interval_ms"] / 1000.0
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            interval,
            self,
            objc.selector(self.refresh_, signature=b'v@:@'),
            None,
            True
        )
        print(f"[DEBUG] Timer created with interval {interval}s, firing initial refresh")
        self.timer.fire()

    def refresh_(self, timer):
        """Refresh session data and update overlay."""
        import sys
        sessions = opencode_data.fetch_data()
        self.overlay.update_sessions(sessions)
        
        # Update position based on menu bar icon
        if self.menu_bar:
            frame = self.menu_bar.get_button_frame()
            if frame:
                self.overlay.update_position(frame)

    @objc.IBAction
    def toggleVisibility_(self, sender):
        """Toggle overlay visibility (menu action)."""
        self.overlay.toggle_visibility()
        # Immediately update position when showing
        if self.overlay.window.isVisible() and self.menu_bar:
            frame = self.menu_bar.get_button_frame()
            if frame:
                self.overlay.update_position(frame)

    @objc.IBAction
    def toggleClickThrough_(self, sender):
        """Toggle click-through mode (menu action)."""
        self.overlay.toggle_click_through()

    @objc.IBAction
    def resetPosition_(self, sender):
        """Reset overlay position to menu bar icon (menu action)."""
        self.overlay.user_positioned = False
        self.overlay.expected_position = None
        if self.menu_bar:
            frame = self.menu_bar.get_button_frame()
            if frame:
                self.overlay.update_position(frame)

    @objc.IBAction
    def quitApp_(self, sender):
        """Quit the application (menu action)."""
        if self.timer:
            self.timer.invalidate()
        NSApplication.sharedApplication().terminate_(None)


def main():
    """Main entry point."""
    app = NSApplication.sharedApplication()
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    AppHelper.runEventLoop()


if __name__ == "__main__":
    main()
