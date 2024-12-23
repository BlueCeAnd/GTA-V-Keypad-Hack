def log(message, level="info"):
    """Log messages with different levels and colors."""
    colors = {
        "info": "\033[94m",  # Blue
        "success": "\033[92m",  # Green
        "warning": "\033[93m",  # Yellow
        "error": "\033[91m",  # Red
        "reset": "\033[0m",  # Reset color
    }
    color = colors.get(level, colors["info"])
    print(f"{color}{message}{colors['reset']}")
