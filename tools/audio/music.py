"""Música propia de The Seed (síntesis chiptune + pads), en bucle sin cortes.

Uso:  python3 tools/audio/music.py
Salida: game/assets/audio/music/<pista>.ogg (estéreo, 32 kHz, Vorbis vía ffmpeg).
Requiere: numpy, scipy, ffmpeg con libvorbis.
Determinista: mismas notas → mismo archivo. Composición original del proyecto.

Pistas:
  space    «Órbita silenciosa»  72 BPM, re menor. Pads, arpegio con eco, campanas.
  mission  «Paso a paso»       112 BPM, la menor. Melodía de pulso, bajo triangular, batería.
  title    «La Semilla»         66 BPM, mi menor. Piano suave y cuerdas (menú y cinemáticas).
  cantina  «Neón de cantina»   100 BPM, do mayor. Piano eléctrico, bajo caminante, vibráfono (bares y tiendas).
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import wave

import numpy as np
from scipy.signal import lfilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "..", "game", "assets", "audio", "music"))
SR = 32000
TAIL = 4.0  # segundos de cola que se pliegan al inicio para un bucle limpio

NOTE_INDEX = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midi(name: str) -> int:
    """'A4', 'F#5', 'Bb3' → número MIDI."""
    letter, rest = name[0], name[1:]
    shift = 0
    while rest and rest[0] in "#b":
        shift += 1 if rest[0] == "#" else -1
        rest = rest[1:]
    return 12 * (int(rest) + 1) + NOTE_INDEX[letter] + shift


def freq(note: int | str) -> float:
    n = midi(note) if isinstance(note, str) else note
    return 440.0 * 2 ** ((n - 69) / 12)


# ------------------------------------------------------------ osciladores

def t_axis(dur: float) -> np.ndarray:
    return np.arange(int(dur * SR)) / SR


def osc_tri(f: float, t: np.ndarray) -> np.ndarray:
    p = (t * f) % 1.0
    return 4 * np.abs(p - 0.5) - 1


def osc_pulse(f: float, t: np.ndarray, duty: float = 0.5, vib: float = 0.0) -> np.ndarray:
    if vib > 0:
        phase = np.cumsum(f * (1 + vib * np.sin(2 * np.pi * 5.5 * t) * np.clip(t * 3 - 0.6, 0, 1))) / SR
    else:
        phase = t * f
    return np.where(phase % 1.0 < duty, 1.0, -1.0)


def osc_saw_soft(f: float, t: np.ndarray, harmonics: int = 10, tilt: float = 1.4) -> np.ndarray:
    """Diente de sierra sin aliasing y con brillo reducido (filtro implícito)."""
    out = np.zeros_like(t)
    for k in range(1, harmonics + 1):
        if k * f > SR / 2.2:
            break
        out += np.sin(2 * np.pi * k * f * t) / k ** tilt
    return out * 0.7


def adsr(n: int, a: float, d: float, s: float, r: float) -> np.ndarray:
    a_n, d_n, r_n = int(a * SR), int(d * SR), int(r * SR)
    env = np.full(n, float(s))
    if a_n > 0:
        env[: min(a_n, n)] = np.linspace(0, 1, a_n)[: min(a_n, n)]
    if d_n > 0 and a_n < n:
        seg = np.linspace(1, s, d_n)[: max(0, min(d_n, n - a_n))]
        env[a_n: a_n + len(seg)] = seg
    if r_n > 0:
        r_n = min(r_n, n)
        env[n - r_n:] *= np.linspace(1, 0, r_n)
    return env


# ------------------------------------------------------------ instrumentos

def inst_pad(f: float, dur: float) -> np.ndarray:
    t = t_axis(dur)
    v = sum(osc_saw_soft(f * d, t, 8, 1.6) for d in (0.997, 1.0, 1.003)) / 3
    return v * adsr(len(t), 0.9, 0.5, 0.8, 1.2)


def inst_strings(f: float, dur: float) -> np.ndarray:
    t = t_axis(dur)
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.0 * t)
    v = sum(osc_saw_soft(f * d, t * vib, 12, 1.2) for d in (0.996, 1.004)) / 2
    return v * adsr(len(t), 0.5, 0.3, 0.85, 0.8)


def inst_arp(f: float, dur: float) -> np.ndarray:
    t = t_axis(dur)
    return osc_tri(f, t) * np.exp(-t * 6.0) * adsr(len(t), 0.004, 0, 1, 0.03)


def inst_bell(f: float, dur: float) -> np.ndarray:
    t = t_axis(dur)
    mod = np.sin(2 * np.pi * f * 3.5 * t) * 1.6 * np.exp(-t * 3)
    return np.sin(2 * np.pi * f * t + mod) * np.exp(-t * 1.6) * adsr(len(t), 0.005, 0, 1, 0.1)


def inst_piano(f: float, dur: float) -> np.ndarray:
    t = t_axis(dur)
    v = (np.sin(2 * np.pi * f * t) + 0.45 * np.sin(4 * np.pi * f * t) * np.exp(-t * 2)
         + 0.2 * np.sin(6 * np.pi * f * t) * np.exp(-t * 4))
    return v * np.exp(-t * 1.1) * adsr(len(t), 0.004, 0, 1, 0.15)


def inst_piano_soft(f: float, dur: float) -> np.ndarray:
    """Piano de acompañamiento: decae rápido y se corta al final de la nota."""
    t = t_axis(dur)
    v = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t) * np.exp(-t * 3)
    return v * np.exp(-t * 2.5) * adsr(len(t), 0.004, 0, 1, 0.12)


def inst_lead(f: float, dur: float) -> np.ndarray:
    t = t_axis(dur)
    return osc_pulse(f, t, 0.25, vib=0.006) * adsr(len(t), 0.01, 0.12, 0.7, 0.06)


def inst_bass_tri(f: float, dur: float) -> np.ndarray:
    t = t_axis(dur)
    return osc_tri(f, t) * adsr(len(t), 0.005, 0.05, 0.9, 0.03)


def inst_sub(f: float, dur: float) -> np.ndarray:
    t = t_axis(dur)
    return np.sin(2 * np.pi * f * t) * adsr(len(t), 0.4, 0.2, 0.9, 0.8)


def drum_kick(dur: float = 0.35) -> np.ndarray:
    t = t_axis(dur)
    f = 45 + 110 * np.exp(-t * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def drum_snare(rng: np.random.Generator, dur: float = 0.22) -> np.ndarray:
    t = t_axis(dur)
    noise = rng.uniform(-1, 1, len(t))
    noise = noise - np.concatenate([[0], noise[:-1]]) * 0.6  # brillo
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30)
    return (noise * 0.7 * np.exp(-t * 16) + tone * 0.5)


def drum_hat(rng: np.random.Generator, dur: float = 0.06) -> np.ndarray:
    t = t_axis(dur)
    noise = rng.uniform(-1, 1, len(t))
    noise = noise - np.concatenate([[0], noise[:-1]])
    return noise * np.exp(-t * 70) * 0.5


# ------------------------------------------------------------ mezcla

class Mix:
    def __init__(self, bpm: float, bars: int):
        self.beat = 60.0 / bpm
        self.length = bars * 4 * self.beat
        n = int((self.length + TAIL) * SR)
        self.buses: dict[str, np.ndarray] = {}
        self.n = n

    def bus(self, name: str) -> np.ndarray:
        if name not in self.buses:
            self.buses[name] = np.zeros((self.n, 2))
        return self.buses[name]

    def add(self, bus: str, sig: np.ndarray, at_beat: float, gain: float, pan: float = 0.0) -> None:
        start = int(at_beat * self.beat * SR)
        end = min(self.n, start + len(sig))
        if start >= self.n:
            return
        left = gain * np.sqrt(0.5 * (1 - pan))
        right = gain * np.sqrt(0.5 * (1 + pan))
        b = self.bus(bus)
        b[start:end, 0] += sig[: end - start] * left
        b[start:end, 1] += sig[: end - start] * right

    def notes(self, bus: str, inst, seq: list, start_beat: float, gain: float, pan: float = 0.0,
              legato: float = 1.0) -> None:
        beat = start_beat
        for note, beats in seq:
            if note is not None:
                for nn in (note if isinstance(note, (list, tuple)) else [note]):
                    self.add(bus, inst(freq(nn), beats * self.beat * legato), beat, gain, pan)
            beat += beats

    def render(self, sends: dict[str, tuple[float, float]]) -> np.ndarray:
        """sends: bus → (eco, reverb)."""
        dry = np.zeros((self.n, 2))
        echo_in = np.zeros((self.n, 2))
        verb_in = np.zeros((self.n, 2))
        for name, sig in self.buses.items():
            e, r = sends.get(name, (0.0, 0.0))
            dry += sig
            echo_in += sig * e
            verb_in += sig * r
        out = dry + ping_pong(echo_in, self.beat * 0.75) + reverb(verb_in)
        # Bucle: la cola se suma al principio
        loop_n = int(self.length * SR)
        tail = out[loop_n:]
        out = out[:loop_n].copy()
        out[: len(tail)] += tail
        out = np.tanh(out * 1.1)
        peak = np.max(np.abs(out))
        return out / peak * 0.89 if peak > 0 else out


def ping_pong(sig: np.ndarray, delay_s: float, feedback: float = 0.45, taps: int = 6) -> np.ndarray:
    out = np.zeros_like(sig)
    d = int(delay_s * SR)
    mono = lowpass(sig.mean(axis=1), 0.35)
    g = 0.6
    for i in range(1, taps + 1):
        shift = d * i
        if shift >= len(sig):
            break
        ch = i % 2
        out[shift:, ch] += mono[:-shift] * g
        g *= feedback
    return out


def reverb(sig: np.ndarray) -> np.ndarray:
    out = np.zeros_like(sig)
    mono = lowpass(sig.mean(axis=1), 0.25)
    taps = [(0.031, 0.5), (0.047, 0.45), (0.067, 0.42), (0.089, 0.38), (0.113, 0.34), (0.149, 0.3),
            (0.197, 0.26), (0.251, 0.22), (0.331, 0.18), (0.433, 0.14), (0.557, 0.1), (0.719, 0.07)]
    for i, (sec, g) in enumerate(taps):
        shift = int(sec * SR)
        out[shift:, i % 2] += mono[:-shift] * g
    return out * 0.6


def lowpass(x: np.ndarray, a: float) -> np.ndarray:
    """Filtro de un polo (a ∈ (0,1], menor = más oscuro)."""
    return lfilter([a], [1.0, a - 1.0], x)


def chord_tones(root: str, kind: str) -> list[int]:
    shapes = {
        "m": [0, 3, 7], "M": [0, 4, 7], "m9": [0, 3, 7, 10, 14], "M7": [0, 4, 7, 11],
        "add9": [0, 4, 7, 14], "m7": [0, 3, 7, 10], "sus4": [0, 5, 7], "7": [0, 4, 7, 10],
    }
    r = midi(root)
    return [r + i for i in shapes[kind]]


# ------------------------------------------------------------ pistas

def track_space() -> np.ndarray:
    mix = Mix(72, 16)
    prog = [("D3", "m9"), ("Bb2", "M7"), ("F3", "M7"), ("C3", "add9")] * 2  # 2 compases cada uno
    rng = np.random.default_rng(7)
    for i, (root, kind) in enumerate(prog):
        bar_beat = i * 8
        tones = chord_tones(root, kind)
        for n in tones[:4]:
            mix.add("pad", inst_pad(freq(n + 12), 8 * mix.beat), bar_beat, 0.16, pan=rng.uniform(-0.5, 0.5))
        mix.add("sub", inst_sub(freq(midi(root) - 12), 8 * mix.beat), bar_beat, 0.32)
        # Arpegio en corcheas: sube y baja
        pattern = tones + tones[-2:0:-1]
        for s in range(16):
            n = pattern[s % len(pattern)] + 24
            if s % 8 == 7 and i % 2 == 1:
                continue
            mix.add("arp", inst_arp(freq(n), mix.beat * 0.9), bar_beat + s * 0.5, 0.12, pan=0.35 if s % 2 else -0.35)
    bell = [("A5", 2), ("F5", 1), ("E5", 1), ("D5", 4), ("F5", 2), ("A5", 2), ("D6", 3), ("C6", 1),
            ("A5", 2), ("G5", 1), ("F5", 1), ("E5", 4), ("G5", 2), ("E5", 1), ("D5", 1), ("E5", 4)]
    mix.notes("bell", inst_bell, bell, 32, 0.17, pan=0.1)
    # Primer ciclo: solo un eco lejano de la melodía, una octava abajo
    echo_bell = [(n, b) for n, b in bell[:4]]
    mix.notes("bell", inst_bell, [(f"{n[:-1]}{int(n[-1]) - 1}", b) for n, b in echo_bell], 16, 0.1, pan=-0.3)
    return mix.render({"pad": (0.0, 0.5), "arp": (0.6, 0.35), "bell": (0.5, 0.6), "sub": (0.0, 0.0)})


def track_mission() -> np.ndarray:
    mix = Mix(112, 16)
    rng = np.random.default_rng(3)
    prog = [("A2", "m"), ("F2", "M"), ("C3", "M"), ("G2", "M"), ("A2", "m"), ("F2", "M"), ("C3", "M"), ("G2", "M"),
            ("F2", "M"), ("G2", "M"), ("E2", "m"), ("A2", "m"), ("F2", "M"), ("G2", "M"), ("C3", "M"), ("E2", "M")]
    for bar, (root, kind) in enumerate(prog):
        b0 = bar * 4
        tones = chord_tones(root, kind)
        r = midi(root)
        # Bajo: raíz-raíz-octava-raíz en corcheas
        for s, off in enumerate([0, 0, 12, 0, 0, 7, 12, 7]):
            mix.add("bass", inst_bass_tri(freq(r + off), mix.beat * 0.45), b0 + s * 0.5, 0.42)
        # Arpegio de pulso en semicorcheas, suave
        for s in range(16):
            n = tones[[0, 1, 2, 1][s % 4]] + 24
            t = t_axis(mix.beat * 0.22)
            sig = osc_pulse(freq(n), t, 0.125) * np.exp(-t * 18)
            mix.add("arp", sig, b0 + s * 0.25, 0.05, pan=-0.4)
        # Acordes sostenidos (cuerdas suaves)
        for n in tones:
            mix.add("pad", inst_strings(freq(n + 12), 4 * mix.beat), b0, 0.05, pan=0.3)
        # Batería
        for beat in range(4):
            if beat in (0, 2):
                mix.add("drums", drum_kick(), b0 + beat, 0.55)
            if beat in (1, 3):
                mix.add("drums", drum_snare(rng), b0 + beat, 0.28, pan=0.05)
            for half in (0, 0.5):
                mix.add("hats", drum_hat(rng), b0 + beat + half, 0.22 if half else 0.3, pan=0.4)
        if bar % 4 == 3:
            mix.add("drums", drum_kick(), b0 + 3.5, 0.4)
    lead = [
        ("A4", 1), ("C5", .5), ("E5", 1.5), ("D5", .5), ("C5", .5),
        ("A4", 1.5), ("F4", .5), ("A4", 1), ("C5", 1),
        ("G4", 1), ("E5", 1), ("D5", .5), ("C5", .5), ("D5", 1),
        ("B4", 3), (None, 1),
        ("A4", 1), ("C5", .5), ("E5", 1.5), ("A5", 1),
        ("G5", .5), ("F5", .5), ("E5", 1), ("C5", 2),
        ("E5", 1), ("G5", 1), ("E5", .5), ("D5", .5), ("C5", 1),
        ("D5", 3), (None, 1),
        ("C5", .5), ("D5", .5), ("E5", 1), ("F5", 1), ("E5", 1),
        ("D5", 1.5), ("B4", .5), ("G4", 2),
        ("B4", 1), ("E5", 1), ("G5", 1.5), ("F5", .5),
        ("E5", 3), (None, 1),
        ("A5", 1), ("G5", .5), ("F5", .5), ("E5", 1), ("C5", 1),
        ("D5", 1), ("B4", 1), ("G4", 1), ("B4", 1),
        ("C5", 1.5), ("E5", .5), ("G5", 2),
        ("B4", 1), ("G#4", 1), ("E4", 2),
    ]
    mix.notes("lead", inst_lead, lead, 0, 0.14, pan=0.05, legato=0.92)
    # Segunda voz una tercera abajo en la parte B (compases 9-16)
    harmony = [(n if n is None else midi(n) - 4, b) for n, b in lead[33:]]
    beat = 32.0
    for n, b in harmony:
        if n is not None:
            mix.add("lead2", inst_lead(freq(n), b * mix.beat * 0.9), beat, 0.06, pan=-0.3)
        beat += b
    return mix.render({"lead": (0.15, 0.15), "lead2": (0.1, 0.15), "arp": (0.4, 0.1), "pad": (0.0, 0.4),
                       "drums": (0.0, 0.08), "hats": (0.0, 0.0), "bass": (0.0, 0.0)})


def track_title() -> np.ndarray:
    mix = Mix(66, 16)
    prog = [("E3", "m"), ("C3", "M"), ("G2", "M"), ("D3", "M"), ("E3", "m"), ("C3", "M"), ("G2", "M"), ("D3", "M"),
            ("A2", "m"), ("E3", "m"), ("C3", "M"), ("D3", "M"), ("E3", "m"), ("C3", "M"), ("D3", "M"), ("E3", "m")]
    for bar, (root, kind) in enumerate(prog):
        b0 = bar * 4
        tones = chord_tones(root, kind)
        for n in tones:
            mix.add("strings", inst_strings(freq(n + 12), 4 * mix.beat * 0.95), b0, 0.065, pan=0.25 if n % 2 else -0.25)
        mix.add("bass", inst_sub(freq(midi(root) - 12), 4 * mix.beat), b0, 0.25)
        # Piano: arpegio en negras, notas cortas para que no se amontonen
        left = [tones[0], tones[2], tones[1] + 12, tones[2]]
        for s in range(4):
            mix.add("piano", inst_piano_soft(freq(left[s] + 12), mix.beat * 0.9), b0 + s, 0.09, pan=-0.2)
    melody = [
        ("B4", 1), ("E5", 1), ("G5", 1), ("F#5", 1),
        ("E5", 3), ("D5", 1),
        ("D5", 1), ("B4", 1), ("D5", 1), ("G5", 1),
        ("F#5", 3), (None, 1),
        ("E5", 1), ("A5", 1), ("G5", 1), ("E5", 1),
        ("B4", 3), ("E5", 1),
        ("G5", 1.5), ("F#5", .5), ("E5", 1), ("C5", 1),
        ("D5", 3), ("A4", 1),
        ("B4", 1), ("E5", 1), ("G5", 1), ("B5", 1),
        ("A5", 2), ("G5", 1), ("E5", 1),
        ("F#5", 1), ("D5", 1), ("A4", 1), ("F#5", 1),
        ("E5", 4),
    ]
    mix.notes("melody", inst_piano, melody, 16, 0.24, pan=0.1, legato=0.85)
    return mix.render({"strings": (0.0, 0.3), "piano": (0.0, 0.15), "melody": (0.08, 0.25), "bass": (0.0, 0.0)})


def inst_epiano(f: float, dur: float) -> np.ndarray:
    t = t_axis(dur)
    tine = np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 18) * 0.25
    v = np.sin(2 * np.pi * f * t + 0.4 * np.sin(2 * np.pi * f * t) * np.exp(-t * 4)) + tine
    return v * np.exp(-t * 3.0) * adsr(len(t), 0.004, 0, 1, 0.08)


def inst_vibes(f: float, dur: float) -> np.ndarray:
    t = t_axis(dur)
    trem = 1 + 0.25 * np.sin(2 * np.pi * 5.5 * t)
    v = np.sin(2 * np.pi * f * t) + 0.15 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 6)
    return v * trem * np.exp(-t * 2.2) * adsr(len(t), 0.003, 0, 1, 0.1)


def track_cantina() -> np.ndarray:
    mix = Mix(100, 16)
    rng = np.random.default_rng(11)
    prog = [("C3", [0, 4, 7, 11]), ("A2", [0, 3, 7, 10]), ("D3", [0, 3, 7, 10]), ("G2", [0, 4, 7, 10])] * 4
    swing = 0.16
    for bar, (root, shape) in enumerate(prog):
        b0 = bar * 4
        r = midi(root)
        # Piano eléctrico: acordes cortos en el 2 y el 4
        for beat in (1, 3):
            for iv in shape[1:]:
                mix.add("keys", inst_epiano(freq(r + 12 + iv), mix.beat * 0.6), b0 + beat, 0.06, pan=-0.25)
        # Bajo caminante en negras
        walk = [0, 7, 12, 11] if bar % 2 == 0 else [0, 4, 7, 5]
        for beat, iv in enumerate(walk):
            mix.add("bass", inst_bass_tri(freq(r + iv), mix.beat * 0.85), b0 + beat, 0.36)
        # Escobillas: charles con swing y aro en el 4
        for beat in range(4):
            mix.add("hats", drum_hat(rng), b0 + beat, 0.16, pan=0.35)
            mix.add("hats", drum_hat(rng), b0 + beat + 0.5 + swing, 0.1, pan=0.35)
        mix.add("drums", drum_snare(rng, 0.08), b0 + 3, 0.1)
        mix.add("drums", drum_kick(0.25), b0, 0.35)
    vibes = [
        ("E5", 1), ("G5", .5), ("B5", 1.5), ("A5", 1),
        ("G5", 1), ("E5", 1), ("C5", 2),
        ("F5", 1), ("A5", .5), ("C6", 1.5), ("B5", 1),
        ("A5", 1), ("G5", 1), ("F5", 1), ("D5", 1),
        ("E5", 1.5), ("D5", .5), ("C5", 1), ("E5", 1),
        ("C5", 2), ("A4", 2),
        ("D5", 1), ("F5", 1), ("A5", 1), ("C6", 1),
        ("B5", 3), (None, 1),
    ]
    mix.notes("vibes", inst_vibes, vibes, 32, 0.15, pan=0.15, legato=0.9)
    return mix.render({"keys": (0.0, 0.25), "vibes": (0.1, 0.3), "bass": (0.0, 0.0), "hats": (0.0, 0.0),
                       "drums": (0.0, 0.05)})


TRACKS = {"space": track_space, "mission": track_mission, "title": track_title, "cantina": track_cantina}


def write_ogg(name: str, data: np.ndarray) -> str:
    os.makedirs(OUT, exist_ok=True)
    pcm = (np.clip(data, -1, 1) * 32767).astype("<i2")
    with tempfile.TemporaryDirectory() as tmp:
        wav_path = os.path.join(tmp, f"{name}.wav")
        with wave.open(wav_path, "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(pcm.tobytes())
        out_path = os.path.join(OUT, f"{name}.ogg")
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", wav_path, "-c:a", "libvorbis", "-q:a", "4",
             "-map_metadata", "-1", "-fflags", "+bitexact", out_path],
            check=True,
        )
    return out_path


def main() -> None:
    for name, fn in TRACKS.items():
        data = fn()
        path = write_ogg(name, data)
        print(f"{name}: {len(data) / SR:.1f} s → {os.path.relpath(path)} ({os.path.getsize(path) // 1024} KB)")


if __name__ == "__main__":
    main()
