"""
HUD: métodos separados para:
  - draw_player_hud()   → HUD mínimo dentro de cada viewport
  - draw_leaderboard()  → leaderboard compartido sobre la pantalla completa
  - draw_kill_feed()    → feed de kills compartido
  - draw_pause/countdown/death → overlays globales
"""

import math
import pygame

from .constants import (
    SCREEN_W, SCREEN_H, WORLD_W, WORLD_H,
    POWERUP_COLORS, POWERUP_ICONS, POWERUP_DURATION,
)

POWERUP_NAMES = {
    "speed":  "VELOCIDAD",
    "ghost":  "FANTASMA",
    "magnet": "IMÁN",
    "shield": "ESCUDO",
    "double": "DOBLE PUNTUACIÓN",
}


class HUD:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self._fonts = {}
        self._minimap_surf = pygame.Surface((160, 160), pygame.SRCALPHA)
        self._init_fonts()

    def _init_fonts(self):
        try:
            base = pygame.font.match_font("consolas,couriernew,monospace")
            for s in [12, 14, 16, 20, 24, 32, 48, 96]:
                self._fonts[s] = pygame.font.Font(base, s)
        except Exception:
            for s in [12, 14, 16, 20, 24, 32, 48, 96]:
                self._fonts[s] = pygame.font.SysFont("monospace", s)

    def font(self, size: int) -> pygame.font.Font:
        return self._fonts.get(size, self._fonts[16])

    # ================================================================== #
    #  HUD mínimo por viewport
    # ================================================================== #

    def draw_player_hud(self, surf: pygame.Surface, snake, t: float,
                        vp_x: int, vp_y: int, vp_w: int, vp_h: int):
        """
        Dibuja el HUD mínimo dentro de `surf` (que puede ser un viewport recortado).
        vp_x/vp_y son el offset del viewport en la pantalla principal (para centrar
        la barra de powerups en pantalla completa si es solo un jugador).
        """
        # Stats en esquina inferior izquierda
        lines = [
            f"Score: {snake.score}",
            f"Largo: {snake.length}",
            f"Kills: {snake.kills}",
        ]
        y = vp_h - len(lines) * 18 - 8
        for line in lines:
            sh = self.font(14).render(line, True, (0, 0, 0))
            tx = self.font(14).render(line, True, (200, 200, 220))
            surf.blit(sh, (9, y + 1))
            surf.blit(tx, (8, y))
            y += 18

        # Barra de power-ups centrada en la parte inferior del viewport
        self._draw_powerup_bar(surf, snake, t, vp_w)

        # Boost: indicador de "TURBO" cuando está activo
        if snake.boosting:
            boost_s = self.font(16).render("TURBO", True, (255, 220, 50))
            surf.blit(boost_s, boost_s.get_rect(
                center=(vp_w // 2, vp_h - 110)))

    def _draw_powerup_bar(self, surf: pygame.Surface, snake, t: float, vp_w: int):
        if not snake.powerups:
            return
        items = list(snake.powerups.items())
        card_w = 82
        gap = 6
        total_w = len(items) * (card_w + gap) - gap
        start_x = vp_w // 2 - total_w // 2
        y = surf.get_height() - 82

        for pu_type, remaining in items:
            color = POWERUP_COLORS.get(pu_type, (200, 200, 200))
            icon  = POWERUP_ICONS.get(pu_type, "?")
            name  = POWERUP_NAMES.get(pu_type, pu_type.upper())

            pulse_alpha = int(60 * abs(math.sin(t * 6))) if remaining < 2.0 else 0

            bg = pygame.Surface((card_w, 68), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 170))
            pygame.draw.rect(bg, (*color, 180), (0, 0, card_w, 68), 2, border_radius=8)
            if pulse_alpha:
                pygame.draw.rect(bg, (*color, pulse_alpha),
                                 (0, 0, card_w, 68), border_radius=8)
            surf.blit(bg, (start_x, y))

            icon_s = self.font(18).render(icon, True, color)
            surf.blit(icon_s, (start_x + card_w // 2 - icon_s.get_width() // 2, y + 4))

            name_s = self.font(12).render(name, True, (230, 230, 255))
            surf.blit(name_s, (start_x + card_w // 2 - name_s.get_width() // 2, y + 26))

            ratio  = max(0.0, remaining / POWERUP_DURATION)
            bar_w  = int((card_w - 8) * ratio)
            pygame.draw.rect(surf, (40, 40, 40),
                             (start_x + 4, y + 52, card_w - 8, 8), border_radius=4)
            if bar_w > 0:
                pygame.draw.rect(surf, color,
                                 (start_x + 4, y + 52, bar_w, 8), border_radius=4)

            secs_s = self.font(12).render(f"{remaining:.1f}s", True, (200, 200, 200))
            surf.blit(secs_s, (start_x + card_w // 2 - secs_s.get_width() // 2, y + 52))

            start_x += card_w + gap

    # ================================================================== #
    #  Leaderboard compartido (dibuja directo en screen)
    # ================================================================== #

    def draw_leaderboard(self, screen: pygame.Surface, snakes: list):
        alive = sorted([s for s in snakes if s.alive],  key=lambda s: s.score, reverse=True)
        dead  = sorted([s for s in snakes if not s.alive], key=lambda s: s.score, reverse=True)
        ordered = alive + dead

        panel_w = 210
        rows = min(len(ordered), 10)
        panel_h = rows * 24 + 34
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 155))
        pygame.draw.rect(panel, (80, 80, 120, 200), (0, 0, panel_w, panel_h), 2)

        title = self.font(14).render("RANKING", True, (255, 210, 50))
        panel.blit(title, (8, 8))

        gold   = (255, 210, 50)
        silver = (200, 200, 200)
        bronze = (180, 120, 60)

        for i, snake in enumerate(ordered[:10]):
            y = 30 + i * 24
            if i % 2 == 0:
                pygame.draw.rect(panel, (255, 255, 255, 8),
                                 (2, y - 1, panel_w - 4, 22))
            pos_c = [gold, silver, bronze][i] if i < 3 else (160, 160, 180)
            panel.blit(self.font(13).render(f"#{i+1}", True, pos_c), (4, y + 2))
            pygame.draw.circle(panel, snake.body_color[:3], (36, y + 10), 5)
            label = (snake.name[:11] + " X") if not snake.alive else snake.name[:13]
            nc = (170, 170, 170) if not snake.alive else (220, 220, 240)
            panel.blit(self.font(13).render(label, True, nc), (46, y + 2))
            sc = self.font(13).render(str(snake.score), True, (255, 255, 255))
            panel.blit(sc, (panel_w - sc.get_width() - 6, y + 2))

        # Esquina superior derecha
        screen.blit(panel, (SCREEN_W - panel_w - 10, 10))

    # ================================================================== #
    #  Kill feed
    # ================================================================== #

    def draw_kill_feed(self, screen: pygame.Surface, events: list):
        x = SCREEN_W - 280
        y = 220
        for text, age in events:
            alpha = max(0, int(255 * (1 - age / 4.0)))
            if alpha <= 0:
                continue
            s = self.font(14).render(text, True, (255, 200, 100))
            tmp = pygame.Surface(s.get_size(), pygame.SRCALPHA)
            tmp.blit(s, (0, 0))
            tmp.set_alpha(alpha)
            screen.blit(tmp, (x, y))
            y += 20

    # ================================================================== #
    #  Overlays globales
    # ================================================================== #

    def draw_pause(self, screen: pygame.Surface):
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 140))
        screen.blit(ov, (0, 0))
        txt = self.font(48).render("PAUSA", True, (255, 255, 255))
        screen.blit(txt, txt.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 30)))
        sub = self.font(20).render("ESC continuar  |  Q salir", True, (200, 200, 220))
        screen.blit(sub, sub.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 30)))

    def draw_countdown(self, screen: pygame.Surface, n: int):
        color = (100, 255, 100) if n <= 0 else (255, 200, 50)
        txt = self.font(96).render("YA!" if n <= 0 else str(n), True, color)
        screen.blit(txt, txt.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2)))

    def draw_death_screen(self, screen: pygame.Surface, snake, t: float):
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, min(200, int(200 * min(1, t / 0.8)))))
        screen.blit(ov, (0, 0))
        if t < 0.5:
            return
        txt = self.font(48).render("HAS MUERTO", True, (255, 80, 80))
        screen.blit(txt, txt.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 80)))
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
            screen.blit(s, s.get_rect(
                center=(SCREEN_W // 2, SCREEN_H // 2 - 10 + i * 32)))
        if t > 2.0 and int(t * 2) % 2 == 0:
            hint = self.font(18).render("ENTER para continuar  |  ESC para salir",
                                        True, (180, 180, 200))
            screen.blit(hint, hint.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 175)))

    # ================================================================== #
    #  Minimapa compartido
    # ================================================================== #

    def draw_minimap(self, screen: pygame.Surface, snakes: list,
                     food_list: list, powerups: list,
                     cameras: list, viewports: list, t: float):
        """
        Minimapa compartido en la esquina inferior derecha de la pantalla.
        Muestra todas las serpientes, comida, power-ups y la posición
        de cada cámara de jugador como un rectángulo de color.
        """
        MM_W, MM_H = 200, 200
        MARGIN = 10
        mm_x = SCREEN_W - MM_W - MARGIN
        mm_y = SCREEN_H - MM_H - MARGIN

        mm = self._minimap_surf
        if mm.get_size() != (MM_W, MM_H):
            self._minimap_surf = pygame.Surface((MM_W, MM_H), pygame.SRCALPHA)
            mm = self._minimap_surf

        mm.fill((0, 0, 0, 190))

        sx = MM_W / WORLD_W
        sy = MM_H / WORLD_H

        # Comida (muestreo cada 4 para no saturar)
        for f in food_list[::4]:
            px = int(f.x * sx)
            py = int(f.y * sy)
            if 0 <= px < MM_W and 0 <= py < MM_H:
                pygame.draw.circle(mm, (*f.color[:3], 100), (px, py), 1)

        # Power-ups
        for pu in powerups:
            px = int(pu.x * sx)
            py = int(pu.y * sy)
            if 0 <= px < MM_W and 0 <= py < MM_H:
                pulse = int(160 + 80 * math.sin(t * 4))
                pygame.draw.circle(mm, (*pu.color[:3], pulse), (px, py), 3)

        # Rectángulos de cámara (área visible de cada jugador)
        for i, (cam, vp) in enumerate(zip(cameras, viewports)):
            cx, cy = cam[0], cam[1]
            rx = int(cx * sx)
            ry = int(cy * sy)
            rw = max(4, int(vp.w * sx))
            rh = max(4, int(vp.h * sy))
            # Color del jugador correspondiente
            s = next((sn for sn in snakes if sn.is_human and sn.id == i), None)
            cam_color = (*s.head_color[:3], 60) if s else (200, 200, 200, 40)
            cam_border = s.head_color[:3] if s else (200, 200, 200)
            cam_surf = pygame.Surface((rw, rh), pygame.SRCALPHA)
            cam_surf.fill(cam_color)
            mm.blit(cam_surf, (rx, ry))
            pygame.draw.rect(mm, (*cam_border, 180), (rx, ry, rw, rh), 1)

        # Serpientes
        for snake in snakes:
            if not snake.alive:
                continue
            # Cuerpo: línea del primer al último segmento muestreado
            segs = snake.segments[::max(1, len(snake.segments) // 8)]
            if len(segs) >= 2:
                pts = [(int(seg.x * sx), int(seg.y * sy)) for seg in segs]
                pygame.draw.lines(mm, (*snake.body_color[:3], 160), False, pts, 1)
            # Cabeza
            hx = int(snake.head.x * sx)
            hy = int(snake.head.y * sy)
            if 0 <= hx < MM_W and 0 <= hy < MM_H:
                r = 4 if snake.is_human else 2
                pygame.draw.circle(mm, (*snake.head_color[:3], 240), (hx, hy), r)
                # Punto blanco en el centro para jugadores humanos
                if snake.is_human:
                    pygame.draw.circle(mm, (255, 255, 255, 220), (hx, hy), 2)

        # Borde del minimapa
        pygame.draw.rect(mm, (80, 80, 130, 220), (0, 0, MM_W, MM_H), 2)

        screen.blit(mm, (mm_x, mm_y))

        # Etiqueta
        label = self.font(12).render("MAPA", True, (180, 180, 210))
        screen.blit(label, (mm_x + 4, mm_y - 16))

    # ================================================================== #

    # Compatibilidad con llamadas antiguas de game_state
    def draw(self, snakes, food_list, powerups, focus_snake=None,
             t=0.0, paused=False, mode="solo"):
        pass  # Reemplazado por métodos individuales