import random

DEFAULT_JOB_TEL = "02438561234"
DEFAULT_SUPERVISOR_TEL = "0912345678"


def _prefix_len(chosen: str) -> int:
    if len(chosen) >= 3:
        return 3
    if len(chosen) >= 2:
        return 2
    return 1


def random_phone_like(chosen: str) -> str:
    """Return a random phone with the same prefix and length as ``chosen``."""
    prefix_len = _prefix_len(chosen)
    prefix = chosen[:prefix_len]
    suffix_len = len(chosen) - prefix_len
    suffix = "".join(str(random.randint(0, 9)) for _ in range(suffix_len))
    return prefix + suffix


def generate_job_tel(chosen: str = DEFAULT_JOB_TEL) -> str:
    return random_phone_like(chosen)


def generate_supervisor_tel(chosen: str = DEFAULT_SUPERVISOR_TEL) -> str:
    return random_phone_like(chosen)
