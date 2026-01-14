"""GTK overlay window and UI refresh logic."""

from __future__ import annotations

import time
import threading
from typing import Optional

import cairo
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk, GLib, Gtk4LayerShell as LayerShell

from .config import CONFIG
from . import ui
from . import opencode_data


class SessionOverlay(Gtk.Window):
    def __init__(self, app):
        super().__init__(application=app)

        self.click_through = CONFIG["behavior"]["click_through"]
        self.interactive_widgets = []

        LayerShell.init_for_window(self)
        LayerShell.set_layer(self, LayerShell.Layer.OVERLAY)
        LayerShell.set_namespace(self, "opencode-activity-monitor")
        LayerShell.set_keyboard_mode(self, LayerShell.KeyboardMode.NONE)
        self._setup_position()

        self.set_decorated(False)
        width = CONFIG["appearance"]["width"]
        self.set_size_request(width, -1)

        ui.load_css()

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.main_box.add_css_class("overlay-main")
        self.set_child(self.main_box)

        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.content_box.add_css_class("overlay-content")
        self.main_box.append(self.content_box)

        self.connect("realize", self.on_realize)

        self.refresh_data()
        GLib.timeout_add(CONFIG["monitor"]["refresh_interval_ms"], self.refresh_data)

    def _setup_position(self):
        pos = CONFIG["position"]
        anchor = pos["anchor"]

        for edge in [LayerShell.Edge.TOP, LayerShell.Edge.BOTTOM,
                     LayerShell.Edge.LEFT, LayerShell.Edge.RIGHT]:
            LayerShell.set_anchor(self, edge, False)

        if "top" in anchor:
            LayerShell.set_anchor(self, LayerShell.Edge.TOP, True)
            LayerShell.set_margin(self, LayerShell.Edge.TOP, pos["margin_top"])
        if "bottom" in anchor:
            LayerShell.set_anchor(self, LayerShell.Edge.BOTTOM, True)
            LayerShell.set_margin(self, LayerShell.Edge.BOTTOM, pos["margin_bottom"])
        if "left" in anchor:
            LayerShell.set_anchor(self, LayerShell.Edge.LEFT, True)
            LayerShell.set_margin(self, LayerShell.Edge.LEFT, pos["margin_left"])
        if "right" in anchor:
            LayerShell.set_anchor(self, LayerShell.Edge.RIGHT, True)
            LayerShell.set_margin(self, LayerShell.Edge.RIGHT, pos["margin_right"])

    def on_realize(self, widget):
        if self.click_through:
            self.set_input_passthrough(True)

    def set_input_passthrough(self, passthrough: bool):
        self.click_through = passthrough
        self.update_input_region()

    def update_input_region(self):
        native = self.get_native()
        if not native:
            return
        surface = native.get_surface()
        if not surface:
            return

        if not self.click_through:
            surface.set_input_region(None)
            return

        region = cairo.Region()

        for widget in self.interactive_widgets:
            success, rect = widget.compute_bounds(self)
            if success:
                region.union(cairo.Region(cairo.RectangleInt(
                    int(rect.origin.x),
                    int(rect.origin.y),
                    int(rect.size.width),
                    int(rect.size.height)
                )))

        surface.set_input_region(region)

    def toggle_input(self):
        self.set_input_passthrough(not self.click_through)

    def toggle_visibility(self):
        if self.get_visible():
            self.hide()
        else:
            self.show()
            self.present()
        width = CONFIG["appearance"]["width"]
        self.set_default_size(width, 1)
        self.set_size_request(width, -1)
        self.content_box.queue_resize()
        self.queue_resize()
        GLib.idle_add(self.update_input_region)


    def refresh_data(self) -> bool:
        def fetch():
            data_response = opencode_data.fetch_data()
            self._last_data = data_response
            GLib.idle_add(self.update_ui, data_response)
        threading.Thread(target=fetch, daemon=True).start()
        return True

    def _request_compact_height(self):
        width = CONFIG["appearance"]["width"]
        self.set_default_size(width, 1)
        self.set_size_request(width, 1)
        self.content_box.queue_resize()
        self.queue_resize()
        GLib.idle_add(self._relax_height)

    def _relax_height(self):
        width = CONFIG["appearance"]["width"]
        self.set_size_request(width, -1)
        self.content_box.queue_resize()
        self.queue_resize()
        return False

    def update_ui(self, sessions: list[opencode_data.Session]):
        while child := self.content_box.get_first_child():
            self.content_box.remove(child)

        self.interactive_widgets = []

        if not sessions:
            lbl = Gtk.Label(label="No active sessions")
            lbl.add_css_class("status-idle")
            lbl.set_halign(Gtk.Align.CENTER)
            self.content_box.append(lbl)
            self._request_compact_height()
            return

        header = Gtk.Label()
        header.set_markup("<b>OPENCODE</b>")
        header.set_halign(Gtk.Align.START)
        header.set_margin_bottom(2)
        header.add_css_class("provider-name")
        self.content_box.append(header)

        for session in sessions:
            if session.is_group_start:
                self.content_box.append(ui.make_separator())
            
            row = ui.make_session_row(
                session.project,
                session.status,
                session.last_active_fmt,
            )
            self.content_box.append(row)

        self._request_compact_height()
        GLib.idle_add(self.update_input_region)

