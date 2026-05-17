from dataclasses import asdict, fields


def debug_asdict(obj):
    for f in fields(obj):
        v = getattr(obj, f.name)
        print(
            f.name,
            type(v),
            v if isinstance(v, (str, int, bool, type(None))) else "",
        )
    return asdict(obj)
