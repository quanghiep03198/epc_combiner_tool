from collections.abc import MutableMapping


def __flatten_dict_gen(d, parent_key, sep):
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            yield from flatten_dict(v, new_key, sep=sep).items()
        else:
            yield new_key, v


def flatten_dict(d: MutableMapping, parent_key: str = "", sep: str = "."):
    """
    Flatten a nested dictionary

    Args:
    - d: Dictionary to be flattened
    - parent_key: Parent key of the dictionary
    - sep: Separator for keys
    """
    return dict(__flatten_dict_gen(d, parent_key, sep))
