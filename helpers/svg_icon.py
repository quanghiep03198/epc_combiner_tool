"""
SVG Icon Helper
Load SVG icons with custom colors
"""

from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtSvg import QSvgRenderer
from helpers.resolve_path import resolve_path


def load_svg_icon(icon_path: str, color: str = None, size: int = 24) -> QIcon:
    """
    Load SVG icon with optional color replacement

    Args:
        icon_path: Path to SVG file (relative or absolute)
        color: Hex color to apply (e.g., "#ffffff")
        size: Icon size in pixels

    Returns:
        QIcon with the SVG rendered in the specified color
    """
    # Resolve path
    if not icon_path.startswith("/") and not ":" in icon_path:
        icon_path = resolve_path(icon_path)

    # If no color specified, return normal icon
    if color is None:
        return QIcon(icon_path)

    # Read SVG content
    with open(icon_path, "r", encoding="utf-8") as f:
        svg_content = f.read()

    # Replace stroke and fill colors with specified color
    # This works for most simple SVG icons
    svg_content = svg_content.replace('stroke="#6e7681"', f'stroke="{color}"')
    svg_content = svg_content.replace('stroke="#ffffff"', f'stroke="{color}"')
    svg_content = svg_content.replace('fill="#fafafa"', f'fill="{color}"')
    svg_content = svg_content.replace('fill="#ffffff"', f'fill="{color}"')
    svg_content = svg_content.replace('stroke="white"', f'stroke="{color}"')
    svg_content = svg_content.replace('fill="white"', f'fill="{color}"')

    # Render SVG with new color
    renderer = QSvgRenderer()
    renderer.load(svg_content.encode("utf-8"))

    # Create pixmap and paint the SVG
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return QIcon(pixmap)


def load_svg_pixmap(
    icon_path: str, color: str = None, width: int = 24, height: int = 24
) -> QPixmap:
    """
    Load SVG as QPixmap with optional color replacement

    Args:
        icon_path: Path to SVG file (relative or absolute)
        color: Hex color to apply (e.g., "#ffffff")
        width: Pixmap width in pixels
        height: Pixmap height in pixels

    Returns:
        QPixmap with the SVG rendered in the specified color
    """
    # Resolve path
    if not icon_path.startswith("/") and not ":" in icon_path:
        icon_path = resolve_path(icon_path)

    # If no color specified, return normal pixmap
    if color is None:
        pixmap = QPixmap(icon_path)
        return pixmap.scaled(
            width,
            height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    # Read SVG content
    with open(icon_path, "r", encoding="utf-8") as f:
        svg_content = f.read()

    # Replace stroke and fill colors with specified color
    svg_content = svg_content.replace('stroke="#6e7681"', f'stroke="{color}"')
    svg_content = svg_content.replace('stroke="#ffffff"', f'stroke="{color}"')
    svg_content = svg_content.replace('fill="#fafafa"', f'fill="{color}"')
    svg_content = svg_content.replace('fill="#ffffff"', f'fill="{color}"')
    svg_content = svg_content.replace('stroke="white"', f'stroke="{color}"')
    svg_content = svg_content.replace('fill="white"', f'fill="{color}"')

    # Render SVG with new color
    renderer = QSvgRenderer()
    renderer.load(svg_content.encode("utf-8"))

    # Create pixmap and paint the SVG
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return pixmap


def create_colored_icon(icon_path: str, color: str, sizes: list = None) -> QIcon:
    """
    Create QIcon with multiple sizes in specified color

    Args:
        icon_path: Path to SVG file
        color: Hex color to apply
        sizes: List of sizes to generate (default: [16, 24, 32, 48])

    Returns:
        QIcon with multiple size variants
    """
    if sizes is None:
        sizes = [16, 24, 32, 48]

    icon = QIcon()
    for size in sizes:
        pixmap = load_svg_pixmap(icon_path, color, size, size)
        icon.addPixmap(pixmap)

    return icon
