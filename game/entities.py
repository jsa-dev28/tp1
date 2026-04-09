"""
Comida y Power-ups del mundo.
"""

import math
import random
import pygame

from .constants import (
    WORLD_W, WORLD_H, FOOD_RADIUS, FOOD_GLOW_SPEED,
    POWERUP_RADIUS, POWERUP_COLORS, POWERUP_ICONS,
    PU_SPEED, PU_GHOST, PU_MAGNET, PU_SHIELD, PU_DOUBLE,
)

FOOD_PALETTE = [
    (255, 80,  80),   # rojo
    (80,  255, 120),  # verde
    (80,  150, 255),  # azul
    (255, 220, 50),   # amarillo
    (220, 80,  255),  # violeta
    (255, 150, 50),   # naranja
    (50,  230, 230),  # cyan
    (255, 180, 180),  # rosa
]


class Food:

    def __init__(self, x: float = None, y: float = None, big: bool = False):
        self.x = x if x is not None else random.uniform(50, WORLD_W - 50)
        self.y = y if y is not None else random.uniform(50, WORLD_H - 50)
        self.color = random.choice(FOOD_PALETTE)
        self.big = big
        self.radius = FOOD_RADIUS * (1.8 if big else 1.0)
        self.value = 3 if big else 1
        self._phase = random.uniform(0, 2 * math.pi)

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float, t: float):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        r = int(self.radius)

        pulse = 0.5 + 0.5 * math.sin(FOOD_GLOW_SPEED * 2 * math.pi * t + self._phase)
        glow_r = int(r + 4 * pulse)
        glow_alpha = int(80 * pulse)

        glow_s = pygame.Surface((glow_r * 2 + 4, glow_r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (*self.color, glow_alpha),
                           (glow_r + 2, glow_r + 2), glow_r + 2)
        surface.blit(glow_s, (sx - glow_r - 2, sy - glow_r - 2))

        pygame.draw.circle(surface, self.color, (sx, sy), r)
        highlight = (min(255, self.color[0] + 80),
                     min(255, self.color[1] + 80),
                     min(255, self.color[2] + 80))
        pygame.draw.circle(surface, highlight, (sx - r // 3, sy - r // 3),
                           max(1, r // 3))


ALL_POWERUP_TYPES = [PU_SPEED, PU_GHOST, PU_MAGNET, PU_SHIELD, PU_DOUBLE]


class PowerUp:
    """Ítem de power-up que flota en el mapa."""

    def __init__(self, x: float = None, y: float = None):
        self.x = x if x is not None else random.uniform(100, WORLD_W - 100)
        self.y = y if y is not None else random.uniform(100, WORLD_H - 100)
        self.pu_type = random.choice(ALL_POWERUP_TYPES)
        self.color = POWERUP_COLORS[self.pu_type]
        self.icon = POWERUP_ICONS[self.pu_type]
        self._phase = random.uniform(0, 2 * math.pi)
        self._angle = 0.0
        self.alive = True

    def update(self, dt: float):
        self._angle += dt * 1.2

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float,
             t: float, font: pygame.font.Font):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        r = POWERUP_RADIUS

        bob = int(4 * math.sin(2 * t + self._phase))
        sy += bob

        pulse = 0.5 + 0.5 * math.sin(3 * t + self._phase)
        halo_r = r + int(6 * pulse)
        halo_s = pygame.Surface((halo_r * 2 + 6, halo_r * 2 + 6), pygame.SRCALPHA)
        pygame.draw.circle(halo_s, (*self.color, 70),
                           (halo_r + 3, halo_r + 3), halo_r + 3)
        surface.blit(halo_s, (sx - halo_r - 3, sy - halo_r - 3))

        pts = []
        for i in range(6):
            a = self._angle + i * math.pi / 3
            pts.append((sx + r * math.cos(a), sy + r * math.sin(a)))
        pygame.draw.polygon(surface, self.color, pts)
        pygame.draw.polygon(surface, (255, 255, 255), pts, 2)

        icon_surf = font.render(self.icon, True, (255, 255, 255))
        rect = icon_surf.get_rect(center=(sx, sy))
        surface.blit(icon_surf, rect)

    def collect_radius(self) -> float:
        return POWERUP_RADIUS * 2.5