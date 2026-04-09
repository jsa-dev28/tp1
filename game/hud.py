"""
HUD (Heads-Up Display): marcador, minimapa, power-ups activos, etc.
"""

import math
import pygame

from .constants import (
    SCREEN_W, SCREEN_H, WORLD_W, WORLD_H,
    POWERUP_COLORS, POWERUP_ICONS, POWERUP_DURATION,
    C_HUD_BG, C_WHITE,
)


class HUD:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self._fonts: dict[int, pygame.font.Font] = {}
        self._init_fonts()

        # Minimapa
        self.minimap_w = 180
        self.minimap_h = 180
        self.minimap_x = SCREEN_W - self.minimap_w - 10
        self.minimap_y = SCREEN_H - self.minimap_h - 10
        self._minimap_surf = pygame.Surface((self.minimap_w, self.minimap_h), pygame.SRCALPHA)

    def _init_fonts(self):
        try:
            base = pygame.font.match_font("consolas,couriernew,monospace")
            self._fonts[12] = pygame.font.Font(base, 12)
            self._fonts[14] = pygame.font.Font(base, 14)
            self._fonts[16] = pygame.font.Font(base, 16)
            self._fonts[20] = pygame.font.Font(base, 20)
            self._fonts[24] = pygame.font.Font(base, 24)
            self._fonts[32] = pygame.font.Font(base, 32)
            self._fonts[48] = pygame.font.Font(base, 48)
        except Exception:
            for s in [12, 14, 16, 20, 24, 32, 48]:
                self._fonts[s] = pygame.font.SysFont("monospace", s)

    def font(self, size: int) -> pygame.font.Font:
        return self._fonts.get(size, self._fonts[16])

    # ------------------------------------------------------------------ #
    def draw(self, snakes: list, food_list: list, powerups: list,
             focus_snake=None, t: float = 0.0, paused: bool = False,
             mode: str = "solo"):

        # Leaderboard lateral
        self._draw_leaderboard(snakes, t)

        # Power-ups activos del jugador enfocado
        if focus_snake and focus_snake.alive:
            self._draw_powerup_bar(focus_snake)
            self._draw_snake_stats(focus_snake)

        # Minimapa
        self._draw_minimap(snakes, food_list, powerups)

        # Pausa
        if paused:
            self._draw_pause()

    # ------------------------------------------------------------------ #
    def _draw_leaderboard(self, snakes: list, t: float):
        alive = [s for s in snakes if s.alive]
        dead  = [s for s in snakes if not s.alive]
        ordered = sorted(alive, key=lambda s: s.score, reverse=True) + \
                  sorted(dead,  key=lambda s: s.score, reverse=True)

        panel_w = 210
        panel_h = min(len(ordered), 10) * 26 + 38
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 160))
        pygame.draw.rect(panel, (80, 80, 120, 200), (0, 0, panel_w, panel_h), 2)

        title = self.font(14).render("🏆  RANKING", True, (255, 210, 50))
        panel.blit(title, (8, 8))

        for i, snake in enumerate(ordered[:10]):
            y = 34 + i * 26
            # Fondo del item
            if i % 2 == 0:
                pygame.draw.rect(panel, (255, 255, 255, 10), (2, y - 2, panel_w - 4, 24))

            # Posición
            pos_color = [(255, 210, 50), (200, 200, 200), (180, 120, 60)]
            pc = pos_color[i] if i < 3 else (160, 160, 180)
            pos_txt = self.font(14).render(f"#{i+1}", True, pc)
            panel.blit(pos_txt, (6, y))

            # Color del snake
            pygame.draw.circle(panel, snake.body_color[:3], (38, y + 8), 6)

            # Nombre
            name = snake.name[:12]
            if not snake.alive:
                name += " ☠"
            name_surf = self.font(14).render(name, True,
                                             (180, 180, 180) if not snake.alive else (220, 220, 240))
            panel.blit(name_surf, (50, y))

            # Score
            sc_surf = self.font(14).render(str(snake.score), True, (255, 255, 255))
            panel.blit(sc_surf, (panel_w - sc_surf.get_width() - 8, y))

            # Longitud
            len_surf = self.font(12).render(f"len:{snake.length}", True, (140, 140, 160))
            panel.blit(len_surf, (panel_w - len_surf.get_width() - 8, y + 14))

        self.screen.blit(panel, (10, 10))

    # ------------------------------------------------------------------ #
    def _draw_powerup_bar(self, snake):
        if not snake.powerups:
            return
        x = SCREEN_W // 2 - (len(snake.powerups) * 70) // 2
        y = SCREEN_H - 70

        for pu_type, remaining in snake.powerups.items():
            color = POWERUP_COLORS.get(pu_type, (200, 200, 200))
            icon  = POWERUP_ICONS.get(pu_type, "?")

            bg = pygame.Surface((64, 56), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 160))
            pygame.draw.rect(bg, color, (0, 0, 64, 56), 2, border_radius=6)
            self.screen.blit(bg, (x, y))

            icon_surf = self.font(20).render(icon, True, color)
            self.screen.blit(icon_surf, (x + 32 - icon_surf.get_width() // 2, y + 6))

            # Barra de tiempo
            ratio = max(0, remaining / POWERUP_DURATION)
            bar_w = int(60 * ratio)
            pygame.draw.rect(self.screen, (50, 50, 50), (x + 2, y + 44, 60, 8))
            pygame.draw.rect(self.screen, color, (x + 2, y + 44, bar_w, 8))

            x += 70

    # ------------------------------------------------------------------ #
    def _draw_snake_stats(self, snake):
        """Estadísticas del jugador enfocado en la esquina inferior izquierda."""
        lines = [
            f"Nombre:  {snake.name}",
            f"Score:   {snake.score}",
            f"Largo:   {snake.length}",
            f"Kills:   {snake.kills}",
        ]
        x, y = 10, SCREEN_H - len(lines) * 20 - 10
        for line in lines:
            surf = self.font(14).render(line, True, (200, 200, 220))
            shadow = self.font(14).render(line, True, (0, 0, 0))
            self.screen.blit(shadow, (x + 1, y + 1))
            self.screen.blit(surf, (x, y))
            y += 20

    # ------------------------------------------------------------------ #
    def _draw_minimap(self, snakes, food_list, powerups):
        mm = self._minimap_surf
        mm.fill((0, 0, 0, 180))
        pygame.draw.rect(mm, (80, 80, 120, 200), (0, 0, self.minimap_w, self.minimap_h), 2)

        sx = self.minimap_w / WORLD_W
        sy = self.minimap_h / WORLD_H

        # Comida (puntos diminutos)
        for f in food_list[::5]:
            px = int(f.x * sx)
            py = int(f.y * sy)
            c = (*f.color, 120)
            pygame.draw.circle(mm, c, (px, py), 1)

        # Power-ups
        for pu in powerups:
            px = int(pu.x * sx)
            py = int(pu.y * sy)
            pygame.draw.circle(mm, (*pu.color, 200), (px, py), 3)

        # Serpientes
        for snake in snakes:
            if not snake.alive:
                continue
            px = int(snake.head.x * sx)
            py = int(snake.head.y * sy)
            color = (*snake.head_color[:3], 230)
            r = 4 if snake.is_human else 3
            pygame.draw.circle(mm, color, (px, py), r)

        self.screen.blit(mm, (self.minimap_x, self.minimap_y))

        # Título del minimapa
        t = self.font(12).render("MAPA", True, (180, 180, 210))
        self.screen.blit(t, (self.minimap_x + 4, self.minimap_y - 16))

    # ------------------------------------------------------------------ #
    def _draw_pause(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))
        txt = self.font(48).render("⏸  PAUSA", True, (255, 255, 255))
        rect = txt.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 30))
        self.screen.blit(txt, rect)
        sub = self.font(20).render("ESC para continuar · Q para salir", True, (200, 200, 220))
        self.screen.blit(sub, sub.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 30)))

    # ------------------------------------------------------------------ #
    def draw_death_screen(self, snake, snakes, t: float):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        alpha = min(200, int(200 * min(1, t / 0.8)))
        overlay.fill((0, 0, 0, alpha))
        self.screen.blit(overlay, (0, 0))

        if t < 0.5:
            return

        # Título
        txt = self.font(48).render("☠  HAS MUERTO  ☠", True, (255, 80, 80))
        self.screen.blit(txt, txt.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 80)))

        # Stats
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

        if t > 2.0:
            blink = int(t * 2) % 2 == 0
            if blink:
                hint = self.font(20).render("Presioná ENTER para continuar · ESC para salir",
                                            True, (180, 180, 200))
                self.screen.blit(hint, hint.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 180)))

    def draw_countdown(self, n: int):
        if n <= 0:
            txt = self.font(96).render("¡YA!", True, (100, 255, 100))
        else:
            txt = self.font(96).render(str(n), True, (255, 200, 50))
        self.screen.blit(txt, txt.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2)))

    def draw_kill_feed(self, events: list, t: float):
        """Muestra feed de eliminaciones en la esquina superior derecha."""
        x = SCREEN_W - 260
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