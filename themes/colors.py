"""
GitHub-inspired color palette with shadcn naming convention
"""

from enum import Enum


class Theme(Enum):
    """Available theme options"""

    DARK = "dark"
    LIGHT = "light"


# GitHub Color Palette với tên biến theo shadcn style
THEMES = {
    "dark": {
        # Base colors
        "background": "#0d1117",  # GitHub dark background
        "foreground": "#e6edf3",  # GitHub dark text
        # Card/Surface
        "card": "#161b22",  # GitHub dark surface
        "card-foreground": "#e6edf3",
        # Popover/Dropdown
        "popover": "#161b22",
        "popover-foreground": "#e6edf3",
        # Primary (green accent - GitHub style)
        "primary": "#238636",  # GitHub green dark
        "primary-foreground": "#ffffff",
        "primary-hover": "#2ea043",  # Lighter green on hover
        # Secondary
        "secondary": "#21262d",  # GitHub secondary bg
        "secondary-foreground": "#e6edf3",
        # Muted
        "muted": "#21262d",  # GitHub muted background
        "muted-foreground": "#7d8590",  # GitHub muted text
        # Accent
        "accent": "#1f6feb",  # GitHub accent blue
        "accent-foreground": "#ffffff",
        # Destructive (danger/error)
        "destructive": "#da3633",  # GitHub red
        "destructive-foreground": "#ffffff",
        # Success
        "success": "#2ea043",  # GitHub green
        "success-foreground": "#ffffff",
        # Warning
        "warning": "#bf8700",  # GitHub yellow/orange
        "warning-foreground": "#ffffff",
        # Borders & inputs
        "border": "#30363d",  # GitHub border
        "input": "#30363d",  # GitHub input border
        "ring": "#238636",  # Focus ring (green)
        # Hover states
        "hover": "#30363d",  # GitHub hover background
        "hover-secondary": "#292e33",
        # Disabled
        "disabled": "#484f58",
        "disabled-foreground": "#6e7681",
    },
    "light": {
        # Base colors
        "background": "#ffffff",  # GitHub light background
        "foreground": "#24292f",  # GitHub light text
        # Card/Surface
        "card": "#f6f8fa",  # GitHub light surface
        "card-foreground": "#24292f",
        # Popover/Dropdown
        "popover": "#ffffff",
        "popover-foreground": "#24292f",
        # Primary (green accent - GitHub style)
        "primary": "#1a7f37",  # GitHub green light (default button color)
        "primary-foreground": "#ffffff",
        "primary-hover": "#2da44e",  # Lighter green on hover
        # Secondary
        "secondary": "#f6f8fa",  # GitHub secondary bg light
        "secondary-foreground": "#24292f",
        # Muted
        "muted": "#f6f8fa",  # GitHub muted background light
        "muted-foreground": "#57606a",  # GitHub muted text light
        # Accent
        "accent": "#0969da",  # GitHub accent blue light
        "accent-foreground": "#ffffff",
        # Destructive (danger/error)
        "destructive": "#cf222e",  # GitHub red light
        "destructive-foreground": "#ffffff",
        # Success
        "success": "#1a7f37",  # GitHub green light
        "success-foreground": "#ffffff",
        # Warning
        "warning": "#9a6700",  # GitHub yellow/orange light
        "warning-foreground": "#ffffff",
        # Borders & inputs
        "border": "#d0d7de",  # GitHub border light
        "input": "#d0d7de",  # GitHub input border light
        "ring": "#1a7f37",  # Focus ring (green) light
        # Hover states
        "hover": "#f3f4f6",  # GitHub hover background light
        "hover-secondary": "#e1e4e8",
        # Disabled
        "disabled": "#8c959f",
        "disabled-foreground": "#57606a",
    },
}


def get_theme_colors(theme: Theme = Theme.DARK) -> dict:
    """
    Get color palette for specified theme

    Args:
        theme: Theme enum (DARK or LIGHT)

    Returns:
        Dictionary of color variables
    """
    return THEMES[theme.value]


def get_color(theme: Theme, color_name: str) -> str:
    """
    Get specific color from theme

    Args:
        theme: Theme enum
        color_name: Color variable name (e.g., 'background', 'primary')

    Returns:
        Hex color code
    """
    return THEMES[theme.value].get(color_name, "#000000")
