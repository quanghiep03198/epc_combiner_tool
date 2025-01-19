from pathlib import Path


def resolve_path(path: str):
    """
    Resolve the path of a file

    Args:
    - path (str): Relative path of the file from the root directory
    """
    current_file = Path(__file__).resolve()
    abs_path = current_file.parent.parent / path
    return str(abs_path)
