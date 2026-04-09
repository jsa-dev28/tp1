"""
Generador de sonidos procedurales.
No requiere archivos externos; todo se sintetiza con numpy + pygame.mixer.
"""

import math
import array
import pygame

_sounds: dict = {}


def _make_wave(freq: float, duration: float, volume: float = 0.5,
               wave: str = "sine", decay: float = 1.0) -> pygame.mixer.Sound:
    """Genera un sonido sintético y lo devuelve como pygame.mixer.Sound."""
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    buf = array.array("h")

    for i in range(n_samples):
        t = i / sample_rate
        env = math.exp(-decay * t / duration)
        amp = int(32767 * volume * env)

        if wave == "sine":
            val = amp * math.sin(2 * math.pi * freq * t)
        elif wave == "square":
            val = amp * (1 if math.sin(2 * math.pi * freq * t) >= 0 else -1)
        elif wave == "sawtooth":
            val = amp * (2 * (freq * t % 1) - 1)
        elif wave == "noise":
            import random
            val = amp * random.uniform(-1, 1)
        else:
            val = amp * math.sin(2 * math.pi * freq * t)

        val = max(-32767, min(32767, int(val)))
        buf.append(val)
        buf.append(val)

    snd = pygame.mixer.Sound(buffer=buf)
    return snd


def _make_jingle(notes, duration_each=0.08, volume=0.4) -> pygame.mixer.Sound:
    """Encadena varias notas en un solo Sound."""
    sample_rate = 44100
    buf = array.array("h")
    for freq in notes:
        n = int(sample_rate * duration_each)
        for i in range(n):
            t = i / sample_rate
            env = math.exp(-5 * t / duration_each)
            val = int(32767 * volume * env * math.sin(2 * math.pi * freq * t))
            val = max(-32767, min(32767, val))
            buf.append(val)
            buf.append(val)
    return pygame.mixer.Sound(buffer=buf)


def init():
    """Construye y cachea todos los efectos de sonido."""
    global _sounds
    if not pygame.mixer.get_init():
        return

    _sounds["eat"]        = _make_wave(880,  0.08, 0.4, "sine",     8.0)
    _sounds["eat_big"]    = _make_wave(1100, 0.15, 0.5, "sine",     6.0)
    _sounds["boost"]      = _make_wave(300,  0.25, 0.3, "sawtooth", 4.0)
    _sounds["die"]        = _make_wave(150,  0.6,  0.6, "square",   3.0)
    _sounds["powerup"]    = _make_jingle([523, 659, 784, 1046], 0.1, 0.45)
    _sounds["shield_hit"] = _make_wave(440,  0.15, 0.4, "square",   6.0)
    _sounds["menu_move"]  = _make_wave(660,  0.05, 0.25, "sine",    10.0)
    _sounds["menu_sel"]   = _make_jingle([523, 784], 0.08, 0.4)
    _sounds["countdown"]  = _make_wave(880,  0.15, 0.5, "sine",     5.0)
    _sounds["go"]         = _make_jingle([523, 659, 784, 1046, 1318], 0.08, 0.5)
    _sounds["kill"]       = _make_jingle([784, 880, 988, 1175], 0.09, 0.45)


def play(name: str, volume: float = 1.0):
    """Reproduce un efecto de sonido por nombre."""
    try:
        snd = _sounds.get(name)
        if snd:
            snd.set_volume(max(0.0, min(1.0, volume)))
            snd.play()
    except Exception:
        pass