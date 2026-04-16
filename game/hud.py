"""
HUD: marcador, minimapa, power-ups activos con nombre, etc.
"""

import math
import pygame

from .constants import (
    SCREEN_W, SCREEN_H, WORLD_W, WORLD_H,
    POWERUP_COLORS, POWERUP_ICONS, POWERUP_DURATION,
    C_HUD_BG, C_WHITE,
)


POWERUP_NAMES = {
    "speed":  "VELOCIDAD",
    "ghost":  "FANTASMA",
    "magnet": "MAGNETO",
    "shield": "ESCUDO",
    "double": "DOBLE SCORE",
}


class HUD:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self._fonts = {}
        self._init_fonts()
        self.minimap_w = 180
        self.minimap_h = 180
        self.minimap_x = SCREEN_W - self.minimap_w - 10
        self.minimap_y = SCREEN_H - self.minimap_h - 10
        self._minimap_surf = pygame.Surface((self.minimap_w, self.minimap_h), pygame.SRCALPHA)

    def _init_fonts(self):
        try:
            base = pygame.font.match_font("consolas,couriernew,monospace")
            for s in [12, 14, 16, 20, 24, 32, 48, 96]:
                self._fonts[s] = pygame.font.Font(base, s)
        except Exception:
            for s in [12, 14, 16, 20, 24, 32, 48, 96]:
                self._fonts[s] = pygame.font.SysFont("monospace", s)

    def font(self, size):
        return self._fonts.get(size, self._fonts[16])

    def draw(self, snakes, food_list, powerups, focus_snake=None,
             t=0.0, paused=False, mode="solo"):
        self._draw_leaderboard(snakes, t)
        if focus_snake and focus_snake.alive:
            self._draw_powerup_bar(focus_snake, t)
            self._draw_snake_stats(focus_snake)
        self._draw_minimap(snakes, food_list, powerups)
        if paused:
            self._draw_pause()

    def _draw_leaderboard(self, snakes, t):
        alive = sorted([s for s in snakes if s.alive],  key=lambda s: s.score, reverse=True)
        dead  = sorted([s for s in snakes if not s.alive], key=lambda s: s.score, reverse=True)
        ordered = alive + dead

        panel_w = 220
        panel_h = min(len(ordered), 10) * 26 + 38
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 160))
        pygame.draw.rect(panel, (80, 80, 120, 200), (0, 0, panel_w, panel_h), 2)

        title = self.font(14).render("RANKING", True, (255, 210, 50))
        panel.blit(title, (8, 8))

        for i, snake in enumerate(ordered[:10]):
            y = 34 + i * 26
            if i % 2 == 0:
                pygame.draw.rect(panel, (255, 255, 255, 10), (2, y - 2, panel_w - 4, 24))
            pc = [(255, 210, 50), (200, 200, 200), (180, 120, 60)]
            pos_c = pc[i] if i < 3 else (160, 160, 180)
            panel.blit(self.font(14).render(f"#{i+1}", True, pos_c), (6, y))
            pygame.draw.circle(panel, snake.body_color[:3], (38, y + 8), 6)
            name = (snake.name[:12] + " X") if not snake.alive else snake.name[:14]
            nc = (180, 180, 180) if not snake.alive else (220, 220, 240)
            panel.blit(self.font(14).render(name, True, nc), (50, y))
            sc = self.font(14).render(str(snake.score), True, (255, 255, 255))
            panel.blit(sc, (panel_w - sc.get_width() - 8, y))
            lc = self.font(12).render(f"len:{snake.length}", True, (140, 140, 160))
            panel.blit(lc, (panel_w - lc.get_width() - 8, y + 14))

        self.screen.blit(panel, (10, 10))

    def _draw_powerup_bar(self, snake, t):
        """Barra de power-ups activos con icono, nombre y tiempo restante."""
        if not snake.powerups:
            return

        items = list(snake.powerups.items())
        card_w = 90
        total_w = len(items) * (card_w + 8) - 8
        start_x = SCREEN_W // 2 - total_w // 2
        y = SCREEN_H - 90

        for pu_type, remaining in items:
            color  = POWERUP_COLORS.get(pu_type, (200, 200, 200))
            icon   = POWERUP_ICONS.get(pu_type, "?")
            name   = POWERUP_NAMES.get(pu_type, pu_type.upper())

            pulse_alpha = 0
            if remaining < 2.0:
                pulse_alpha = int(60 * abs(math.sin(t * 6)))

            bg = pygame.Surface((card_w, 72), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 170))
            pygame.draw.rect(bg, (*color, 180), (0, 0, card_w, 72), 2, border_radius=8)
            if pulse_alpha:
                pygame.draw.rect(bg, (*color, pulse_alpha), (0, 0, card_w, 72),
                                 border_radius=8)
            self.screen.blit(bg, (start_x, y))

            icon_s = self.font(20).render(icon, True, color)
            self.screen.blit(icon_s, (start_x + card_w // 2 - icon_s.get_width() // 2, y + 4))

            name_s = self.font(12).render(name, True, (230, 230, 255))
            self.screen.blit(name_s, (start_x + card_w // 2 - name_s.get_width() // 2, y + 28))

            ratio = max(0.0, remaining / POWERUP_DURATION)
            bar_w = int((card_w - 8) * ratio)
            pygame.draw.rect(self.screen, (40, 40, 40), (start_x + 4, y + 56, card_w - 8, 8),
                             border_radius=4)
            if bar_w > 0:
                pygame.draw.rect(self.screen, color, (start_x + 4, y + 56, bar_w, 8),
                                 border_radius=4)

            secs = self.font(12).render(f"{remaining:.1f}s", True, (200, 200, 200))
            self.screen.blit(secs, (start_x + card_w // 2 - secs.get_width() // 2, y + 56))

            start_x += card_w + 8

    def _draw_snake_stats(self, snake):
        lines = [
            f"Nombre:  {snake.name}",
            f"Score:   {snake.score}",
            f"Largo:   {snake.length}",
            f"Kills:   {snake.kills}",
        ]
        x, y = 10, SCREEN_H - len(lines) * 20 - 10
        for line in lines:
            shadow = self.font(14).render(line, True, (0, 0, 0))
            surf   = self.font(14).render(line, True, (200, 200, 220))
            self.screen.blit(shadow, (x + 1, y + 1))
            self.screen.blit(surf,   (x,     y))
            y += 20

    def _draw_minimap(self, snakes, food_list, powerups):
        mm = self._minimap_surf
        mm.fill((0, 0, 0, 180))
        pygame.draw.rect(mm, (80, 80, 120, 200), (0, 0, self.minimap_w, self.minimap_h), 2)
        sx = self.minimap_w / WORLD_W
        sy = self.minimap_h / WORLD_H
        for f in food_list[::5]:
            mm_x = int(f.x * sx)
            mm_y = int(f.y * sy)
            pygame.draw.circle(mm, (*f.color, 120), (mm_x, mm_y), 1)
        for pu in powerups:
            pygame.draw.circle(mm, (*pu.color, 200),
                               (int(pu.x * sx), int(pu.y * sy)), 3)
        for snake in snakes:
            if not snake.alive:
                continue
            px = int(snake.head.x * sx)
            py = int(snake.head.y * sy)
            r = 4 if snake.is_human else 3
            pygame.draw.circle(mm, (*snake.head_color[:3], 230), (px, py), r)
        self.screen.blit(mm, (self.minimap_x, self.minimap_y))
        t = self.font(12).render("MAPA", True, (180, 180, 210))
        self.screen.blit(t, (self.minimap_x + 4, self.minimap_y - 16))

    def _draw_pause(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))
        txt = self.font(48).render("PAUSA", True, (255, 255, 255))
        self.screen.blit(txt, txt.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 30)))
        sub = self.font(20).render("ESC para continuar  |  Q para salir", True, (200, 200, 220))
        self.screen.blit(sub, sub.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 30)))

    def draw_death_screen(self, snake, snakes, t):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, min(200, int(200 * min(1, t / 0.8)))))
        self.screen.blit(overlay, (0, 0))
        if t < 0.5:
            return
        txt = self.font(48).render("HAS MUERTO", True, (255, 80, 80))
        self.screen.blit(txt, txt.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 80)))
        stats = [
            f"Score: {snake.score}",
            f"Longitud: {snake.length}",
            f"Kills: {snake.kills}",
            f"Alimentos: {snake.foods_eaten}",
        ]
        if snake.killed_by and snake.killed_by is not snake:
            stats.append(f"Eliminado por: {snake.killed_by.name}")
        for i, line in enumerate(stats):
            s = self.font(24).render(line, True, (220, 220, 240))
            self.screen.blit(s, s.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 10 + i * 34)))
        if t > 2.0 and int(t * 2) % 2 == 0:
            hint = self.font(20).render("ENTER para continuar  |  ESC para salir",
                                        True, (180, 180, 200))
            self.screen.blit(hint, hint.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 180)))

    def draw_countdown(self, n):
        txt = self.font(96).render("YA!" if n <= 0 else str(n),
                                   True, (100, 255, 100) if n <= 0 else (255, 200, 50))
        self.screen.blit(txt, txt.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2)))

    def draw_kill_feed(self, events, t):
        x = SCREEN_W - 280
        y = 220
        for event_text, age in events:
            alpha = max(0, int(255 * (1 - age / 4.0)))
            if alpha <= 0:
                continue
            s = self.font(14).render(event_text, True, (255, 200, 100))
            surf = pygame.Surface(s.get_size(), pygame.SRCALPHA)
            surf.blit(s, (0, 0))
            surf.set_alpha(alpha)
            self.screen.blit(surf, (x, y))
            y += 20