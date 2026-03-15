import time


def now_ts() -> int:
    return int(time.time())


def human_ts(ts: int) -> str:
    return f"<t:{ts}:F>"