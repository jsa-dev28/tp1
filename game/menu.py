"""
Menú principal del juego.
"""

import math
import random
import pygame

from .constants import SCREEN_W, SCREEN_H, C_BG, PLAYER_COLORS
from . import sounds


class AnimatedSnake:

    def __init__(self, color, y_start):
        self.segments = [(x, y_start + math.sin(x * 0.02) * 50)
                         for x in range(-200, SCREEN_W + 200, 14)]
        self.color = color
        self.speed = random.uniform(60, 120)
        self.amp = random.uniform(30, 80)
        self.freq = random.uniform(0.015, 0.03)
        self.phase = random.uniform(0, 2 * math.pi)
        self.y_center = y_start

    def update(self, dt, t):
        for i in range(len(self.segments)):
            x = self.segments[i][0] + self.speed * dt
            y = self.y_center + self.amp * math.sin(self.freq * x + self.phase + t)
            self.segments[i] = (x % (SCREEN_W + 400) - 200, y)

    def draw(self, surface):
        n = len(self.segments)
        for i, (x, y) in enumerate(self.segments):
            t = 1 - (i / n) * 0.3
            r = max(4, int(12 * t))
            alpha = int(180 * t)
            color = (*self.color[:3], alpha)
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (r, r), r)
            surface.blit(s, (int(x) - r, int(y) - r))


class Button:
    def __init__(self, rect, text, color=(60, 180, 100), font=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.color = color
        self.font = font
        self.hovered = False
        self._hover_scale = 0.0

    def update(self, mouse_pos, dt):
        self.hovered = self.rect.collidepoint(mouse_pos)
        target = 1.0 if self.hovered else 0.0
        self._hover_scale += (target - self._hover_scale) * 10 * dt

    def draw(self, surface, font):
        f = self.font or font
        scale = 1 + self._hover_scale * 0.05
        w = int(self.rect.w * scale)
        h = int(self.rect.h * scale)
        x = self.rect.centerx - w // 2
        y = self.rect.centery - h // 2

        bg_color = (
            min(255, int(self.color[0] * (1.2 if self.hovered else 1.0))),
            min(255, int(self.color[1] * (1.2 if self.hovered else 1.0))),
            min(255, int(self.color[2] * (1.2 if self.hovered else 1.0))),
        )
        if self.hovered:
            glow = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*self.color[:3], 60), (0, 0, w + 20, h + 20),
                             border_radius=14)
            surface.blit(glow, (x - 10, y - 10))

        pygame.draw.rect(surface, (20, 20, 40), (x + 3, y + 3, w, h), border_radius=10)
        pygame.draw.rect(surface, bg_color, (x, y, w, h), border_radius=10)
        pygame.draw.rect(surface, (255, 255, 255, 80 if self.hovered else 40),
                         (x, y, w, h), 2, border_radius=10)

        label = f.render(self.text, True, (255, 255, 255))
        surface.blit(label, label.get_rect(center=(x + w // 2, y + h // 2)))

    def clicked(self, event) -> bool:
        return (event.type == pygame.MOUSEBUTTONDOWN and
                event.button == 1 and
                self.rect.collidepoint(event.pos))


class Menu:
    """Menú principal con pantallas anidadas."""

    SCREEN_MAIN   = "main"
    SCREEN_LOCAL  = "local"
    SCREEN_NETWORK = "network"

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self._screen = self.SCREEN_MAIN
        self._t = 0.0
        self._result = None
        self._selected_players = 1
        self._selected_bots = 5
        self._net_mode = None
        self._net_ip = "127.0.0.1"
        self._net_port = 5555
        self._input_active = False
        self._input_text = ""

        try:
            base = pygame.font.match_font("impact,arialblack,impact,arial")
            self._font_title = pygame.font.Font(base, 72)
            self._font_sub   = pygame.font.Font(base, 28)
            base2 = pygame.font.match_font("consolas,couriernew,monospace")
            self._font_body  = pygame.font.Font(base2, 20)
            self._font_small = pygame.font.Font(base2, 16)
        except Exception:
            self._font_title = pygame.font.SysFont("impact", 72)
            self._font_sub   = pygame.font.SysFont("impact", 28)
            self._font_body  = pygame.font.SysFont("monospace", 20)
            self._font_small = pygame.font.SysFont("monospace", 16)

        self._bg_snakes = [
            AnimatedSnake(PLAYER_COLORS[i % len(PLAYER_COLORS)]["body"],
                          100 + i * 120)
            for i in range(6)
        ]

        self._stars = [(random.uniform(0, SCREEN_W), random.uniform(0, SCREEN_H),
                        random.uniform(0.5, 2.0)) for _ in range(200)]

        self._build_buttons()
        sounds.init()

    def _build_buttons(self):
        cx = SCREEN_W // 2
        BW, BH = 320, 54

        self._btns_main = {
            "local":   Button((cx - BW//2, 280, BW, BH), "🎮  JUGAR LOCAL",      (50, 160, 90)),
            "network": Button((cx - BW//2, 348, BW, BH), "🌐  MULTIJUGADOR LAN", (50, 110, 200)),
            "quit":    Button((cx - BW//2, 416, BW, BH), "✖   SALIR",            (180, 50, 50)),
        }

        self._btns_local = {
            "p_minus":  Button((cx - 180, 310, 44, 44), "◄",  (80, 80, 130)),
            "p_plus":   Button((cx - 60,  310, 44, 44), "►",  (80, 80, 130)),
            "b_minus":  Button((cx - 180, 380, 44, 44), "◄",  (80, 80, 130)),
            "b_plus":   Button((cx - 60,  380, 44, 44), "►",  (80, 80, 130)),
            "solo":     Button((cx - 220, 460, 200, 50), "⚡ SOLO vs IA",       (50, 160, 90)),
            "coop":     Button((cx + 20,  460, 200, 50), "👥 COOPERATIVO",      (80, 120, 200)),
            "vs":       Button((cx - 100, 524, 200, 50), "⚔  VERSUS LOCAL",     (180, 80, 50)),
            "back":     Button((cx - 100, 600, 200, 44), "◄ VOLVER",            (80, 60, 60)),
        }

        self._btns_network = {
            "server":   Button((cx - 180, 340, 340, 54), "🖥  CREAR PARTIDA (Server)", (50, 130, 80)),
            "client":   Button((cx - 180, 410, 340, 54), "📡  UNIRSE (Cliente)",      (50, 90, 180)),
            "back":     Button((cx - 100, 500, 200, 44), "◄ VOLVER",                 (80, 60, 60)),
        }

    def reset(self):
        self._screen = self.SCREEN_MAIN
        self._result = None
        self._t = 0.0

    def update_and_draw(self):
        dt = 1 / 60
        self._t += dt
        clock_result = None

        mouse = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and self._screen != self.SCREEN_MAIN:
                    self._screen = self.SCREEN_MAIN
                    sounds.play("menu_move")
                if self._input_active:
                    if event.key == pygame.K_BACKSPACE:
                        self._input_text = self._input_text[:-1]
                    elif event.key == pygame.K_RETURN:
                        self._input_active = False
                    else:
                        self._input_text += event.unicode
            if event.type == pygame.MOUSEBUTTONDOWN:
                sounds.play("menu_move")

            clock_result = self._handle_event(event)
            if clock_result:
                return clock_result

        self.screen.fill(C_BG)
        self._draw_stars()
        for sn in self._bg_snakes:
            sn.update(dt, self._t)
            sn.draw(self.screen)

        self._draw_title()

        if self._screen == self.SCREEN_MAIN:
            self._update_draw_buttons(self._btns_main, mouse, dt)
        elif self._screen == self.SCREEN_LOCAL:
            self._draw_local_screen(mouse, dt)
        elif self._screen == self.SCREEN_NETWORK:
            self._draw_network_screen(mouse, dt)

        ver = self._font_small.render("v1.0 · Slither Pygame Edition", True, (60, 60, 90))
        self.screen.blit(ver, (SCREEN_W - ver.get_width() - 10, SCREEN_H - 24))

        return None

    def _handle_event(self, event):
        if self._screen == self.SCREEN_MAIN:
            if self._btns_main["quit"].clicked(event):
                return "quit"
            if self._btns_main["local"].clicked(event):
                self._screen = self.SCREEN_LOCAL
                sounds.play("menu_sel")
            if self._btns_main["network"].clicked(event):
                self._screen = self.SCREEN_NETWORK
                sounds.play("menu_sel")

        elif self._screen == self.SCREEN_LOCAL:
            b = self._btns_local
            if b["p_minus"].clicked(event):
                self._selected_players = max(1, self._selected_players - 1)
            if b["p_plus"].clicked(event):
                self._selected_players = min(4, self._selected_players + 1)
            if b["b_minus"].clicked(event):
                self._selected_bots = max(0, self._selected_bots - 1)
            if b["b_plus"].clicked(event):
                self._selected_bots = min(12, self._selected_bots + 1)
            if b["back"].clicked(event):
                self._screen = self.SCREEN_MAIN
            if b["solo"].clicked(event):
                sounds.play("menu_sel")
                return ("local", 1, self._selected_bots, None, None)
            if b["coop"].clicked(event):
                sounds.play("menu_sel")
                return ("local", self._selected_players, self._selected_bots, None, None)
            if b["vs"].clicked(event):
                sounds.play("menu_sel")
                return ("local", self._selected_players, 0, None, None)

        elif self._screen == self.SCREEN_NETWORK:
            b = self._btns_network
            if b["back"].clicked(event):
                self._screen = self.SCREEN_MAIN
            if b["server"].clicked(event):
                sounds.play("menu_sel")
                return ("network", 1, self._selected_bots, "server",
                        ("0.0.0.0", self._net_port))
            if b["client"].clicked(event):
                sounds.play("menu_sel")
                return ("network", 1, 0, "client",
                        (self._net_ip, self._net_port))
        return None

    def _update_draw_buttons(self, btns: dict, mouse, dt):
        for btn in btns.values():
            btn.update(mouse, dt)
            btn.draw(self.screen, self._font_body)

    def _draw_title(self):
        cx = SCREEN_W // 2
        t = self._t

        shadow_offset = int(4 + 2 * math.sin(t * 1.5))
        title_text = "SLITHER.IO"
        shadow = self._font_title.render(title_text, True, (10, 40, 10))
        self.screen.blit(shadow, shadow.get_rect(center=(cx + shadow_offset,
                                                          140 + shadow_offset)))

        title1 = self._font_title.render(title_text, True, (80, 240, 100))
        title2 = self._font_title.render(title_text, True, (50, 180, 70))
        self.screen.blit(title2, title2.get_rect(center=(cx, 141)))
        self.screen.blit(title1, title1.get_rect(center=(cx, 140)))

        sub = self._font_sub.render("PYGAME EDITION", True, (100, 180, 110))
        self.screen.blit(sub, sub.get_rect(center=(cx, 200)))

    def _draw_stars(self):
        t = self._t
        for sx, sy, br in self._stars:
            twinkle = 0.5 + 0.5 * math.sin(br * 7 + t * br)
            c = int(30 + 50 * twinkle)
            pygame.draw.circle(self.screen, (c, c, c + 10), (int(sx), int(sy)), 1)

    def _draw_local_screen(self, mouse, dt):
        cx = SCREEN_W // 2
        f = self._font_body
        fs = self._font_small

        sec = self._font_sub.render("CONFIGURAR PARTIDA LOCAL", True, (180, 220, 180))
        self.screen.blit(sec, sec.get_rect(center=(cx, 250)))

        p_label = f.render(f"Jugadores humanos:  {self._selected_players}", True, (220, 220, 255))
        self.screen.blit(p_label, p_label.get_rect(center=(cx - 50, 330)))

        b_label = f.render(f"Bots de IA:         {self._selected_bots}", True, (220, 220, 255))
        self.screen.blit(b_label, b_label.get_rect(center=(cx - 50, 400)))

        hints = [
            "J1: WASD + SHIFT(boost)",
            "J2: ↑↓←→ + RSHIFT",
            "J3: IJKL + U",
            "J4: Numpad 8456 + 0",
        ]
        for i, h in enumerate(hints[:self._selected_players]):
            ht = fs.render(h, True, PLAYER_COLORS[i]["head"])
            self.screen.blit(ht, (cx + 100, 300 + i * 22))

        self._update_draw_buttons(self._btns_local, mouse, dt)

    def _draw_network_screen(self, mouse, dt):
        cx = SCREEN_W // 2
        f = self._font_body

        sec = self._font_sub.render("MULTIJUGADOR LAN", True, (180, 200, 255))
        self.screen.blit(sec, sec.get_rect(center=(cx, 250)))

        info_lines = [
            f"IP local:  {self._net_ip}",
            f"Puerto:    {self._net_port}",
            "",
            "El servidor crea la partida.",
            "Los clientes se unen con la IP del host.",
        ]
        for i, line in enumerate(info_lines):
            s = f.render(line, True, (200, 200, 220))
            self.screen.blit(s, s.get_rect(center=(cx, 290 + i * 26)))

        self._update_draw_buttons(self._btns_network, mouse, dt)