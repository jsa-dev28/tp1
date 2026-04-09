"""
Sistema de partículas para efectos visuales.
"""

import math
import random
import pygame


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "radius", "fade")

    def __init__(self, x, y, vx, vy, life, color, radius=3, fade=True):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color
        self.radius = radius
        self.fade = fade

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= 0.95
        self.vy *= 0.95
        self.life -= dt
        return self.life > 0

    def draw(self, surface, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        alpha = int(255 * (self.life / self.max_life)) if self.fade else 255
        r = max(1, int(self.radius * (self.life / self.max_life)))
        surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color[:3], alpha), (r + 1, r + 1), r)
        surface.blit(surf, (sx - r - 1, sy - r - 1))


class ParticleSystem:
    def __init__(self):
        self.particles: list[Particle] = []

    def emit_death(self, x, y, color, count=40):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 250)
            life = random.uniform(0.4, 1.2)
            radius = random.uniform(3, 8)
            self.particles.append(Particle(
                x, y,
                speed * math.cos(angle),
                speed * math.sin(angle),
                life, color, radius
            ))

    def emit_eat(self, x, y, color, count=8):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(30, 100)
            life = random.uniform(0.2, 0.5)
            self.particles.append(Particle(
                x, y,
                speed * math.cos(angle),
                speed * math.sin(angle),
                life, color, 2
            ))

    def emit_boost(self, x, y, color, angle):
        """Estela de boost detrás de la cabeza."""
        for _ in range(3):
            a = angle + math.pi + random.uniform(-0.5, 0.5)
            speed = random.uniform(60, 140)
            life = random.uniform(0.1, 0.35)
            self.particles.append(Particle(
                x + random.uniform(-5, 5),
                y + random.uniform(-5, 5),
                speed * math.cos(a),
                speed * math.sin(a),
                life, color, random.uniform(2, 5)
            ))

    def emit_powerup(self, x, y, color, count=20):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(40, 180)
            life = random.uniform(0.3, 0.9)
            self.particles.append(Particle(
                x, y,
                speed * math.cos(angle),
                speed * math.sin(angle),
                life, color, random.uniform(2, 6)
            ))

    def update(self, dt):
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, surface, cam_x, cam_y):
        for p in self.particles:
            p.draw(surface, cam_x, cam_y)