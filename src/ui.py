"""
OpenCode Session Activity Monitor - UI Components
"""

from gi.repository import Gtk, Gdk, Pango
from .config import CONFIG


def get_css() -> bytes:
    """Generate CSS from config."""
    
    appearance = CONFIG["appearance"]
    colors = CONFIG["colors"]
    
    bg_opacity = appearance["background_opacity"]
    text_opacity = appearance["text_opacity"]
    radius = appearance["corner_radius"]
    bg_rgb = colors["background"]
    
    return f"""
    window {{
        background: transparent;
    }}
    
    .overlay-main {{
        background: rgba({bg_rgb}, {bg_opacity});
        border-radius: {radius}px;
        border: 1px solid rgba(100, 140, 180, 0.15);
    }}
    
    .overlay-content {{
        padding: 8px;
    }}
    
    /* Provider name header (legacy support) */
    .provider-name {{
        font-weight: bold;
        font-size: 0.78em;
        color: {colors["provider"]};
        opacity: {text_opacity};
        margin-top: 1px;
        margin-bottom: 1px;
    }}
    
    .session-project {{
        font-family: "JetBrains Mono", "Fira Code", monospace;
        font-weight: normal;
        font-size: 0.72em;
        color: #ffffff;
        opacity: 0.9;
        margin-top: 0px;
        margin-bottom: 0px;
    }}

    .session-status {{
        font-family: "JetBrains Mono", "Fira Code", monospace;
        font-size: 0.65em;
        font-weight: bold;
        min-width: 40px;
    }}
    
    .status-active {{ color: {colors["ok"]}; }}
    .status-idle {{ color: {colors["warning"]}; }}
    .status-stale {{ color: {colors["critical"]}; }}
    
    .session-time {{
        font-family: "JetBrains Mono", "Fira Code", monospace;
        font-size: 0.65em;
        color: rgba(255, 255, 255, 0.35);
        min-width: 45px;
    }}

    .session-separator {{
        border-top: 1px solid rgba(100, 120, 140, 0.12);
        margin-top: 2px;
        margin-bottom: 2px;
        min-height: 1px;
    }}
    """.encode()


def load_css():
    """Load CSS into GTK."""
    css_provider = Gtk.CssProvider()
    css_provider.load_from_data(get_css())
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(),
        css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )


def make_separator() -> Gtk.Box:
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    box.add_css_class("session-separator")
    return box


def make_session_row(project: str, status: str, time_ago: str) -> Gtk.Box:
    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)

    lbl_project = Gtk.Label(label=project)
    lbl_project.set_halign(Gtk.Align.START)
    lbl_project.add_css_class("session-project")
    lbl_project.set_hexpand(True)
    lbl_project.set_ellipsize(Pango.EllipsizeMode.END)
    row.append(lbl_project)

    lbl_status = Gtk.Label(label=status)
    lbl_status.add_css_class("session-status")
    lbl_status.add_css_class(f"status-{status.lower()}")
    lbl_status.set_xalign(1.0)  # Right align status to push against timer
    row.append(lbl_status)

    lbl_time = Gtk.Label(label=time_ago or " ")
    lbl_time.add_css_class("session-time")
    # Compact width - "23h59m" fits in ~40-45px at this font size
    lbl_time.set_size_request(45, -1)
    lbl_time.set_xalign(1.0) 
    row.append(lbl_time)

    return row
