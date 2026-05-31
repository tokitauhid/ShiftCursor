"""
ShiftCursor — SVG Icon Resources

Embedded SVG icons as Python strings. No external files needed.
"""


def _svg(path_data: str, size: int = 24, color: str = "currentColor", viewbox: str = "0 0 24 24") -> str:
    """Helper to generate an SVG string."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="{viewbox}" fill="none" stroke="{color}" '
        f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        f'{path_data}</svg>'
    )


# ── Icon SVG Paths (Lucide icon style) ──────────────────────────────────────

ICONS = {
    "folder_upload": _svg(
        '<path d="M12 10v6"/>'
        '<path d="m9 13 3-3 3 3"/>'
        '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h16z"/>'
    ),
    "folder": _svg(
        '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h16z"/>'
    ),
    "folder_open": _svg(
        '<path d="m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2"/>'
    ),
    "check_circle": _svg(
        '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>'
        '<polyline points="22 4 12 14.01 9 11.01"/>'
    ),
    "x_circle": _svg(
        '<circle cx="12" cy="12" r="10"/>'
        '<line x1="15" y1="9" x2="9" y2="15"/>'
        '<line x1="9" y1="9" x2="15" y2="15"/>'
    ),
    "loader": _svg(
        '<line x1="12" y1="2" x2="12" y2="6"/>'
        '<line x1="12" y1="18" x2="12" y2="22"/>'
        '<line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/>'
        '<line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/>'
        '<line x1="2" y1="12" x2="6" y2="12"/>'
        '<line x1="18" y1="12" x2="22" y2="12"/>'
        '<line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/>'
        '<line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/>'
    ),
    "clock": _svg(
        '<circle cx="12" cy="12" r="10"/>'
        '<polyline points="12 6 12 12 16 14"/>'
    ),
    "sun": _svg(
        '<circle cx="12" cy="12" r="5"/>'
        '<line x1="12" y1="1" x2="12" y2="3"/>'
        '<line x1="12" y1="21" x2="12" y2="23"/>'
        '<line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>'
        '<line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>'
        '<line x1="1" y1="12" x2="3" y2="12"/>'
        '<line x1="21" y1="12" x2="23" y2="12"/>'
        '<line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>'
        '<line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>'
    ),
    "moon": _svg(
        '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>'
    ),
    "download": _svg(
        '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
        '<polyline points="7 10 12 15 17 10"/>'
        '<line x1="12" y1="15" x2="12" y2="3"/>'
    ),
    "external_link": _svg(
        '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>'
        '<polyline points="15 3 21 3 21 9"/>'
        '<line x1="10" y1="14" x2="21" y2="3"/>'
    ),
    "x": _svg(
        '<line x1="18" y1="6" x2="6" y2="18"/>'
        '<line x1="6" y1="6" x2="18" y2="18"/>'
    ),
    "mouse_pointer": _svg(
        '<path d="m3 3 7.07 16.97 2.51-7.39 7.39-2.51L3 3z"/>'
        '<path d="m13 13 6 6"/>'
    ),
    "play": _svg(
        '<polygon points="5 3 19 12 5 21 5 3" fill="white" stroke="none"/>'
    ),
    "chevron_down": _svg(
        '<polyline points="6 9 12 15 18 9"/>'
    ),
    "chevron_up": _svg(
        '<polyline points="18 15 12 9 6 15"/>'
    ),
}


def get_icon_svg(name: str, color: str = "#A0A0B8", size: int = 24) -> str:
    """Get an SVG icon string with the specified color and size."""
    svg = ICONS.get(name, ICONS["folder"])
    # Replace color
    svg = svg.replace('stroke="currentColor"', f'stroke="{color}"')
    # Replace size
    svg = svg.replace(f'width="24"', f'width="{size}"')
    svg = svg.replace(f'height="24"', f'height="{size}"')
    return svg


def svg_to_pixmap(name: str, color: str = "#A0A0B8", size: int = 24):
    """Convert an SVG icon to a QPixmap."""
    from PySide6.QtCore import QByteArray
    from PySide6.QtGui import QPixmap
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtGui import QPainter

    svg_data = get_icon_svg(name, color, size)
    renderer = QSvgRenderer(QByteArray(svg_data.encode()))

    pixmap = QPixmap(size, size)
    pixmap.fill()  # transparent
    from PySide6.QtCore import Qt
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return pixmap


def svg_to_icon(name: str, color: str = "#A0A0B8", size: int = 24):
    """Convert an SVG icon to a QIcon."""
    from PySide6.QtGui import QIcon
    return QIcon(svg_to_pixmap(name, color, size))
