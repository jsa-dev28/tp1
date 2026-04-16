"""
Menú principal del juego.
Incluye: selector de nombre, selector de color, sin modo LAN.
"""

import math
import random
import pygame

from .constants import SCREEN_W, SCREEN_H, C_BG, PLAYER_COLORS
from . import sounds

COLOR_OPTIONS = [
    {"body": (50,  200, 100), "head": (80,  255, 130), "glow": (50,  200, 80,  60)},
    {"body": (60,  140, 220), "head": (100, 180, 255), "glow": (60,  140, 220, 60)},
    {"body": (220, 70,  70),  "head": (255, 110, 110), "glow": (220, 70,  70,  60)},
    {"body": (200, 160, 30),  "head": (255, 210, 50),  "glow": (200, 160, 30,  60)},
    {"body": (160, 60,  200), "head": (200, 100, 255), "glow": (160, 60,  200, 50)},
    {"body": (200, 110, 40),  "head": (255, 150, 80),  "glow": (200, 110, 40,  50)},
    {"body": (40,  190, 190), "head": (80,  240, 240), "glow": (40,  190, 190, 50)},
    {"body": (210, 210, 80),  "head": (255, 255, 130), "glow": (210, 210, 80,  50)},
    {"body": (190, 60,  120), "head": (240, 100, 160), "glow": (190, 60,  120, 50)},
    {"body": (255, 255, 255), "head": (200, 230, 255), "glow": (200, 200, 255, 50)},
]


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
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color[:3], alpha), (r, r), r)
            surface.blit(s, (int(x) - r, int(y) - r))


class Button:
    def __init__(self, rect, text, color=(60, 180, 100)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.color = color
        self.hovered = False
        self._hover_scale = 0.0

    def update(self, mouse_pos, dt):
        self.hovered = self.rect.collidepoint(mouse_pos)
        target = 1.0 if self.hovered else 0.0
        self._hover_scale += (target - self._hover_scale) * 10 * dt

    def draw(self, surface, font):
        scale = 1 + self._hover_scale * 0.05
        w = int(self.rect.w * scale)
        h = int(self.rect.h * scale)
        x = self.rect.centerx - w // 2
        y = self.rect.centery - h // 2
        bg_color = tuple(min(255, int(c * (1.2 if self.hovered else 1.0))) for c in self.color)
        if self.hovered:
            glow = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*self.color[:3], 60), (0, 0, w + 20, h + 20), border_radius=14)
            surface.blit(glow, (x - 10, y - 10))
        pygame.draw.rect(surface, (20, 20, 40), (x + 3, y + 3, w, h), border_radius=10)
        pygame.draw.rect(surface, bg_color, (x, y, w, h), border_radius=10)
        pygame.draw.rect(surface, (255, 255, 255), (x, y, w, h), 2, border_radius=10)
        label = font.render(self.text, True, (255, 255, 255))
        surface.blit(label, label.get_rect(center=(x + w // 2, y + h // 2)))

    def clicked(self, event) -> bool:
        return (event.type == pygame.MOUSEBUTTONDOWN and
                event.button == 1 and self.rect.collidepoint(event.pos))


class PlayerConfig:
    """Nombre y color elegidos por un jugador en el menú."""
    def __init__(self, index: int):
        self.index = index
        self.name = f"Jugador {index + 1}"
        self.color_index = index % len(COLOR_OPTIONS)
        self.typing = False


class Menu:
    SCREEN_MAIN   = "main"
    SCREEN_CONFIG = "config"

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self._screen = self.SCREEN_MAIN
        self._t = 0.0
        self._selected_players = 1
        self._selected_bots = 5
        self._player_configs = [PlayerConfig(i) for i in range(4)]

        try:
            base = pygame.font.match_font("impact,arialblack,arial")
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
            AnimatedSnake(PLAYER_COLORS[i % len(PLAYER_COLORS)]["body"], 100 + i * 120)
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
            "play": Button((cx - BW // 2, 300, BW, BH), "JUGAR",  (50, 160, 90)),
            "quit": Button((cx - BW // 2, 368, BW, BH), "SALIR",  (180, 50, 50)),
        }
        self._btns_config = {
            "p_minus": Button((cx - 230, 248, 40, 40), "<", (80, 80, 130)),
            "p_plus":  Button((cx - 60,  248, 40, 40), ">", (80, 80, 130)),
            "b_minus": Button((cx - 230, 298, 40, 40), "<", (80, 80, 130)),
            "b_plus":  Button((cx - 60,  298, 40, 40), ">", (80, 80, 130)),
            "solo":    Button((cx - 230, 620, 200, 50), "SOLO vs IA",   (50, 160, 90)),
            "coop":    Button((cx + 30,  620, 200, 50), "COOPERATIVO",  (80, 120, 200)),
            "vs":      Button((cx - 100, 680, 200, 50), "VERSUS",       (180, 80, 50)),
            "back":    Button((cx - 100, 740, 200, 44), "< VOLVER",     (80, 60, 60)),
        }

    def reset(self):
        self._screen = self.SCREEN_MAIN
        self._t = 0.0

    def update_and_draw(self):
        dt = 1 / 60
        self._t += dt
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                result = self._handle_key(event)
                if result:
                    return result
            if event.type == pygame.MOUSEBUTTONDOWN:
                sounds.play("menu_move")
            result = self._handle_click(event)
            if result:
                return result

        self.screen.fill(C_BG)
        self._draw_stars()
        for sn in self._bg_snakes:
            sn.update(dt, self._t)
            sn.draw(self.screen)
        self._draw_title()

        if self._screen == self.SCREEN_MAIN:
            self._draw_main(mouse, dt)
        elif self._screen == self.SCREEN_CONFIG:
            self._draw_config(mouse, dt)

        ver = self._font_small.render("v1.1 - Slither Pygame Edition", True, (60, 60, 90))
        self.screen.blit(ver, (SCREEN_W - ver.get_width() - 10, SCREEN_H - 24))
        return None

    def _handle_key(self, event):
        if event.key == pygame.K_ESCAPE:
            for pc in self._player_configs:
                pc.typing = False
            if self._screen != self.SCREEN_MAIN:
                self._screen = self.SCREEN_MAIN
                sounds.play("menu_move")
            return None
        for pc in self._player_configs:
            if pc.typing:
                if event.key == pygame.K_BACKSPACE:
                    pc.name = pc.name[:-1]
                elif event.key == pygame.K_RETURN:
                    pc.typing = False
                elif len(pc.name) < 16 and event.unicode.isprintable() and event.unicode != "":
                    pc.name += event.unicode
                return None
        return None

    def _handle_click(self, event):
        if self._screen == self.SCREEN_MAIN:
            if self._btns_main["quit"].clicked(event):
                return "quit"
            if self._btns_main["play"].clicked(event):
                self._screen = self.SCREEN_CONFIG
                sounds.play("menu_sel")

        elif self._screen == self.SCREEN_CONFIG:
            b = self._btns_config
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

            for i in range(self._selected_players):
                pc = self._player_configs[i]
                col_l, col_r, name_rect = self._player_row_rects(i)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if col_l.collidepoint(event.pos):
                        pc.color_index = (pc.color_index - 1) % len(COLOR_OPTIONS)
                    elif col_r.collidepoint(event.pos):
                        pc.color_index = (pc.color_index + 1) % len(COLOR_OPTIONS)
                    elif name_rect.collidepoint(event.pos):
                        for other in self._player_configs:
                            other.typing = False
                        pc.typing = True
                    else:
                        pc.typing = False

            if b["solo"].clicked(event):
                sounds.play("menu_sel")
                return self._build_result("solo", 1, self._selected_bots)
            if b["coop"].clicked(event):
                sounds.play("menu_sel")
                return self._build_result("coop", self._selected_players, self._selected_bots)
            if b["vs"].clicked(event):
                sounds.play("menu_sel")
                return self._build_result("vs", self._selected_players, 0)
        return None

    def _build_result(self, mode, num_players, num_bots):
        cfgs = self._player_configs[:num_players]
        return (mode, num_players, num_bots, None, None, cfgs)

    def _player_row_rects(self, index):
        cx = SCREEN_W // 2
        base_y = 360 + index * 56
        col_l     = pygame.Rect(cx + 10,  base_y + 6, 30, 30)
        col_r     = pygame.Rect(cx + 110, base_y + 6, 30, 30)
        name_rect = pygame.Rect(cx - 230, base_y, 220, 42)
        return col_l, col_r, name_rect

    def _draw_main(self, mouse, dt):
        for btn in self._btns_main.values():
            btn.update(mouse, dt)
            btn.draw(self.screen, self._font_body)
        hint = self._font_small.render("Hasta 4 jugadores  |  IA configurable  |  Power-ups",
                                       True, (80, 100, 80))
        self.screen.blit(hint, hint.get_rect(center=(SCREEN_W // 2, 450)))

    def _draw_config(self, mouse, dt):
        cx = SCREEN_W // 2
        f  = self._font_body
        fs = self._font_small

        sec = self._font_sub.render("CONFIGURAR PARTIDA", True, (180, 220, 180))
        self.screen.blit(sec, sec.get_rect(center=(cx, 210)))

        p_label = f.render(f"Jugadores humanos:  {self._selected_players}", True, (220, 220, 255))
        self.screen.blit(p_label, p_label.get_rect(midleft=(cx - 185, 268)))
        b_label = f.render(f"Bots de IA:         {self._selected_bots}", True, (220, 220, 255))
        self.screen.blit(b_label, b_label.get_rect(midleft=(cx - 185, 318)))

        self.screen.blit(fs.render("NOMBRE  (clic para editar)", True, (140, 160, 140)),
                         (cx - 230, 342))
        self.screen.blit(fs.render("COLOR", True, (140, 160, 140)), (cx + 10, 342))
        self.screen.blit(fs.render("TECLAS", True, (140, 160, 140)), (cx + 160, 342))

        KEY_HINTS = ["WASD + LSHIFT", "Flechas + RSHIFT", "IJKL + U", "Num 8456 + 0"]

        for i in range(self._selected_players):
            pc = self._player_configs[i]
            col = COLOR_OPTIONS[pc.color_index]
            col_l, col_r, name_rect = self._player_row_rects(i)
            base_y = name_rect.y

            row_bg = pygame.Surface((SCREEN_W - 80, 44), pygame.SRCALPHA)
            row_bg.fill((255, 255, 255, 8) if i % 2 == 0 else (0, 0, 0, 0))
            self.screen.blit(row_bg, (40, base_y))

            border_color = col["head"] if pc.typing else (80, 80, 100)
            pygame.draw.rect(self.screen, (20, 20, 35), name_rect, border_radius=6)
            pygame.draw.rect(self.screen, border_color, name_rect, 2, border_radius=6)
            display = (pc.name or " ") + ("|" if pc.typing and int(self._t * 2) % 2 == 0 else "")
            ns = f.render(display, True, (230, 230, 255))
            self.screen.blit(ns, ns.get_rect(midleft=(name_rect.x + 8, name_rect.centery)))

            pygame.draw.circle(self.screen, col["body"], (cx + 75, base_y + 21), 14)
            pygame.draw.circle(self.screen, col["head"], (cx + 75, base_y + 21), 9)
            self.screen.blit(fs.render("<", True, (180, 180, 220)),
                             fs.render("<", True, (180, 180, 220)).get_rect(center=col_l.center))
            self.screen.blit(fs.render(">", True, (180, 180, 220)),
                             fs.render(">", True, (180, 180, 220)).get_rect(center=col_r.center))

            ks = fs.render(KEY_HINTS[i], True, col["head"])
            self.screen.blit(ks, (cx + 160, base_y + 12))

        for btn in self._btns_config.values():
            btn.update(mouse, dt)
            btn.draw(self.screen, self._font_body)

    def _draw_title(self):
        cx = SCREEN_W // 2
        t = self._t
        off = int(4 + 2 * math.sin(t * 1.5))
        shadow = self._font_title.render("SLITHER.IO", True, (10, 40, 10))
        self.screen.blit(shadow, shadow.get_rect(center=(cx + off, 120 + off)))
        title = self._font_title.render("SLITHER.IO", True, (80, 240, 100))
        self.screen.blit(title, title.get_rect(center=(cx, 120)))
        sub = self._font_sub.render("PYGAME EDITION", True, (100, 180, 110))
        self.screen.blit(sub, sub.get_rect(center=(cx, 178)))

    def _draw_stars(self):
        for sx, sy, br in self._stars:
            twinkle = 0.5 + 0.5 * math.sin(br * 7 + self._t * br)
            c = int(30 + 50 * twinkle)
            pygame.draw.circle(self.screen, (c, c, c + 10), (int(sx), int(sy)), 1)