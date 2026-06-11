def _attr(obj, *path, default=None):
    """Walk a dotted attribute path on nipyapi objects safely.

    Returns default if any step along the path is None or missing.
    """
    for key in path:
        if obj is None:
            return default
        obj = getattr(obj, key, None)
    return obj if obj is not None else default
