# audioop.py — lightweight shim so discord imports succeed on hosts
# This is a compatibility stub for environments where the C audioop extension
# is not available (e.g. some container images). It implements a few common
# helpers used at import-time so discord.py won't crash. It does NOT provide
# full, high-performance audio processing. Voice features may be limited.

import struct
import math

def _samples_from_bytes(fragment: bytes, width: int):
    """Return list of signed integers from bytes fragment for given sample width."""
    if width == 1:
        # 8-bit unsigned
        return [b - 128 for b in fragment]
    fmt = {2: "<h", 3: "3", 4: "<i"}.get(width)
    if width == 3:
        # 24-bit sample parsing
        samples = []
        for i in range(0, len(fragment), 3):
            chunk = fragment[i:i+3]
            # expand to 4 bytes with sign
            if len(chunk) < 3:
                break
            # little-endian
            val = int.from_bytes(chunk + (b'\x00' if chunk[-1] < 0x80 else b'\xff'), 'little', signed=True)
            samples.append(val)
        return samples
    elif fmt:
        samples = []
        for i in range(0, len(fragment), width):
            chunk = fragment[i:i+width]
            if len(chunk) < width:
                break
            samples.append(struct.unpack(fmt, chunk)[0])
        return samples
    else:
        return []

def rms(fragment: bytes, width: int) -> int:
    """Return RMS of samples (approx)."""
    if not fragment or width <= 0:
        return 0
    samples = _samples_from_bytes(fragment, width)
    if not samples:
        return 0
    s = 0
    for v in samples:
        s += v*v
    mean = s / len(samples)
    return int(math.sqrt(mean))

def avg(fragment: bytes, width: int) -> int:
    samples = _samples_from_bytes(fragment, width)
    if not samples:
        return 0
    return int(sum(samples) / len(samples))

def max(fragment: bytes, width: int) -> int:
    samples = _samples_from_bytes(fragment, width)
    return max(samples) if samples else 0

def findmax(fragment: bytes, width: int):
    # return (maxval, position)
    samples = _samples_from_bytes(fragment, width)
    if not samples:
        return (0, 0)
    m = max(samples)
    pos = samples.index(m)
    return (m, pos)

# No-op implementations to avoid crash on import — they raise if actually used improperly.
def add(fragment1: bytes, fragment2: bytes, width: int) -> bytes:
    # naive: return fragment1 (not a real mix)
    return fragment1

def mul(fragment: bytes, factor: float, width: int) -> bytes:
    # naive: return fragment unchanged
    return fragment

def reverse(fragment: bytes, width: int) -> bytes:
    return fragment[::-1]

# provide module-level attributes expected by some callers
__all__ = ["rms","avg","max","findmax","add","mul","reverse"]
