"""Efectos de sonido chiptune propios de The Seed.

Uso:  python3 tools/pixelart/sfx.py
Salida: game/assets/audio/sfx/*.wav (mono, 22 050 Hz, 16 bit).
"""
from __future__ import annotations

import math
import os
import random
import struct
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "..", "game", "assets", "audio", "sfx"))
RATE = 22050


def square(freq: float, t: float, duty: float = 0.5) -> float:
    return 1.0 if (t * freq) % 1.0 < duty else -1.0


def tri(freq: float, t: float) -> float:
    p = (t * freq) % 1.0
    return 4 * p - 1 if p < 0.5 else 3 - 4 * p


def env(i: int, n: int, attack: float = 0.01, release: float = 0.3) -> float:
    t = i / n
    if t < attack:
        return t / attack
    if t > 1 - release:
        return max(0.0, (1 - t) / release)
    return 1.0


def write(name: str, samples: list[float], volume: float = 0.35) -> None:
    os.makedirs(OUT, exist_ok=True)
    with wave.open(os.path.join(OUT, f"{name}.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, s * volume)) * 32767)) for s in samples))


def tone_seq(notes: list[tuple[float, float]], wave_fn=square) -> list[float]:
    out: list[float] = []
    for freq, dur in notes:
        n = int(RATE * dur)
        for i in range(n):
            t = i / RATE
            out.append(0.0 if freq <= 0 else wave_fn(freq, t) * env(i, n, 0.02, 0.4))
    return out


def sweep(f0: float, f1: float, dur: float, wave_fn=tri) -> list[float]:
    n = int(RATE * dur)
    out, phase = [], 0.0
    for i in range(n):
        f = f0 + (f1 - f0) * (i / n)
        phase += f / RATE
        out.append(wave_fn(1.0, phase) * env(i, n, 0.05, 0.3))
    return out


def noise(dur: float, f_start: float, f_end: float, seed: int = 1) -> list[float]:
    rng = random.Random(seed)
    n = int(RATE * dur)
    out, val, hold = [], 0.0, 0
    for i in range(n):
        f = f_start + (f_end - f_start) * (i / n)
        period = max(1, int(RATE / max(f, 1)))
        if hold <= 0:
            val = rng.uniform(-1, 1)
            hold = period
        hold -= 1
        out.append(val * env(i, n, 0.1, 0.5))
    return out


def main() -> None:
    write("blip", tone_seq([(880, 0.03)]), 0.18)
    write("confirm", tone_seq([(660, 0.06), (990, 0.08)]))
    write("error", tone_seq([(220, 0.09), (165, 0.14)]))
    write("scan", sweep(300, 1400, 0.45) + tone_seq([(1760, 0.05)], tri))
    write("success", tone_seq([(523, 0.08), (659, 0.08), (784, 0.08), (1047, 0.22)]))
    write("pickup", tone_seq([(784, 0.05), (1175, 0.1)], tri))
    write("takeoff", [a * 0.7 + b * 0.5 for a, b in zip(noise(1.4, 200, 1600, 3), sweep(80, 400, 1.4, square))])
    write("land", [a * 0.6 + b * 0.4 for a, b in zip(noise(0.9, 1200, 150, 5), sweep(300, 90, 0.9, square))])
    write("step", noise(0.05, 900, 400, 9), 0.12)
    write("bump", noise(0.18, 500, 120, 11), 0.4)
    print("OK →", OUT)


if __name__ == "__main__":
    main()
