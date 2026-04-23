"""
Estado principal del juego.
Soporta pantalla dividida para 1-4 jugadores humanos.
"""

import math
import random
import pygame

from .constants import (
    SCREEN_W, SCREEN_H, WORLD_W, WORLD_H,
    FOOD_COUNT_TARGET, POWERUP_SPAWN_INTERVAL,
    SEGMENT_RADIUS, GROW_PER_FOOD,
    BOT_COLORS, C_BG, C_GRID, PU_MAGNET,
)
from .snake import PlayerSnake, BotSnake, PLAYER_KEYS
from .entities import Food, PowerUp
from .particles import ParticleSystem
from .hud import HUD
from . import sounds

_LAYOUTS = {
    1: [(0.0, 0.0, 1.0, 1.0)],
    2: [(0.0, 0.0, 0.5, 1.0),
        (0.5, 0.0, 0.5, 1.0)],
    3: [(0.0, 0.0, 0.5, 0.5),
        (0.5, 0.0, 0.5, 0.5),
        (0.0, 0.5, 1.0, 0.5)],
    4: [(0.0, 0.0, 0.5, 0.5),
        (0.5, 0.0, 0.5, 0.5),
        (0.0, 0.5, 0.5, 0.5),
        (0.5, 0.5, 0.5, 0.5)],
}

_LEADERBOARD_H = 0


def _get_viewports(num_players: int):
    """Devuelve lista de pygame.Rect, uno por jugador humano."""
    layout = _LAYOUTS.get(num_players, _LAYOUTS[1])
    rects = []
    for nx, ny, nw, nh in layout:
        rects.append(pygame.Rect(
            int(nx * SCREEN_W),
            int(ny * SCREEN_H),
            int(nw * SCREEN_W),
            int(nh * SCREEN_H),
        ))
    return rects


class GameState:
    def __init__(self, screen: pygame.Surface, mode: str,
                 num_players: int, num_bots: int,
                 player_configs=None, server=None, client=None):
        self.screen = screen
        self.mode = mode
        self.num_players = num_players
        self.num_bots = num_bots

        self._split = num_players > 1
        self._viewports = _get_viewports(num_players)

        self._vp_surfs = [
            pygame.Surface((vp.w, vp.h)) for vp in self._viewports
        ]

        self.hud = HUD(screen)
        self.particles = ParticleSystem()

        self._t = 0.0
        self._paused = False
        self._state = "countdown"
        self._countdown = 3.0
        self._death_timer = 0.0

        self._cameras = [[0.0, 0.0] for _ in range(max(num_players, 1))]

        self._pu_timer = POWERUP_SPAWN_INTERVAL
        self._kill_feed = []

        self.snakes = []
        self._init_snakes(player_configs or [])

        self.food = []
        self._spawn_initial_food()
        self.powerups = []

        self._stars = [(random.uniform(0, WORLD_W), random.uniform(0, WORLD_H),
                        random.uniform(0.5, 2.0)) for _ in range(400)]

        sounds.init()
        sounds.play("countdown")

    def _init_snakes(self, player_configs):
        from .menu import COLOR_OPTIONS
        margin = 400
        for i in range(self.num_players):
            if i < len(player_configs):
                cfg = player_configs[i]
                color_info = dict(COLOR_OPTIONS[cfg.color_index])
                color_info["name"] = cfg.name.strip() or f"Jugador {i+1}"
            else:
                from .constants import PLAYER_COLORS
                color_info = dict(PLAYER_COLORS[i % len(PLAYER_COLORS)])
            keys = PLAYER_KEYS[i % len(PLAYER_KEYS)]
            x = random.uniform(margin, WORLD_W - margin)
            y = random.uniform(margin, WORLD_H - margin)
            self.snakes.append(PlayerSnake(color_info, i, keys, x, y))

        for j in range(self.num_bots):
            color = BOT_COLORS[j % len(BOT_COLORS)]
            x = random.uniform(margin, WORLD_W - margin)
            y = random.uniform(margin, WORLD_H - margin)
            self.snakes.append(
                BotSnake(color, self.num_players + j,
                         random.uniform(0.8, 1.6), x, y)
            )

    def _spawn_initial_food(self):
        for _ in range(FOOD_COUNT_TARGET):
            self.food.append(Food(big=random.random() < 0.08))

    def _human_snakes(self):
        return [s for s in self.snakes if s.is_human]

    def _get_focus_snake(self, player_idx: int = 0):
        humans = self._human_snakes()
        if player_idx < len(humans):
            return humans[player_idx]
        alive = [s for s in self.snakes if s.alive]
        return max(alive, key=lambda s: s.length) if alive else None

    def update(self, dt: float):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "menu"
            if event.type == pygame.KEYDOWN:
                r = self._handle_key(event.key)
                if r:
                    return r

        if self._state == "countdown":
            self._countdown -= dt
            if self._countdown < 0:
                self._state = "playing"
                sounds.play("go")
            return None

        if self._paused:
            return None

        if self._state == "death":
            self._death_timer += dt
            self.particles.update(dt)
            if self._death_timer > 2.0:
                pressed = pygame.key.get_pressed()
                if pressed[pygame.K_RETURN] or pressed[pygame.K_KP_ENTER]:
                    return "menu"
            return None

        if self._state == "gameover":
            self._death_timer += dt
            if self._death_timer > 3.5:
                return "menu"
            return None

        self._t += dt
        self._pu_timer -= dt
        self._kill_feed = [(txt, age + dt) for txt, age in self._kill_feed if age + dt < 4.0]

        pressed = pygame.key.get_pressed()
        for s in self.snakes:
            if s.is_human and s.alive:
                s.handle_input_dt(pressed, dt)
        for s in self.snakes:
            if not s.is_human and s.alive:
                s.ai_update(dt, self.food, self.snakes, self.powerups)
        for s in self.snakes:
            if s.alive:
                s.update(dt)
                if s.boosting and s._boost_particle_timer <= 0:
                    self.particles.emit_boost(s.head.x, s.head.y, s.body_color, s.angle)
                    s._boost_particle_timer = 0.04
        for s in self.snakes:
            if s.alive and s.has_magnet:
                self._apply_magnet(s)

        self._check_collisions()

        while len(self.food) < FOOD_COUNT_TARGET:
            self.food.append(Food(big=random.random() < 0.08))
        if self._pu_timer <= 0:
            self.powerups.append(PowerUp())
            self._pu_timer = POWERUP_SPAWN_INTERVAL + random.uniform(-2, 2)
        for pu in self.powerups:
            pu.update(dt)
        self.particles.update(dt)

        humans = self._human_snakes()
        for i, cam in enumerate(self._cameras):
            snake = humans[i] if i < len(humans) else None
            if snake and snake.alive:
                vp = self._viewports[i]
                tx = snake.head.x - vp.w / 2
                ty = snake.head.y - vp.h / 2
            elif snake:
                tx, ty = cam[0], cam[1]
            else:
                tx, ty = cam[0], cam[1]
            cam[0] += (tx - cam[0]) * 0.1
            cam[1] += (ty - cam[1]) * 0.1

        humans_alive = [s for s in self.snakes if s.is_human and s.alive]
        if self.num_players > 0 and not humans_alive:
            self._state = "death"
            self._death_timer = 0.0

        all_alive = [s for s in self.snakes if s.alive]
        if len(all_alive) <= 1 and len(self.snakes) > 1:
            self._state = "gameover"
            self._death_timer = 0.0

        return None

    def _handle_key(self, key):
        if key == pygame.K_ESCAPE:
            if self._state == "playing":
                self._paused = not self._paused
            elif self._state in ("death", "gameover", "countdown"):
                return "menu"
        if self._paused and key == pygame.K_q:
            return "menu"
        return None

    def _apply_magnet(self, snake):
        magnet_r = 200
        hx, hy = snake.head.x, snake.head.y
        for f in self.food:
            dx, dy = hx - f.x, hy - f.y
            d = math.hypot(dx, dy)
            if 0 < d < magnet_r:
                force = (magnet_r - d) / magnet_r * 180
                f.x += dx / d * force * 0.016
                f.y += dy / d * force * 0.016

    def _check_collisions(self):
        alive = [s for s in self.snakes if s.alive]
        for snake in alive:
            hx, hy = snake.head.x, snake.head.y
            eaten = [i for i, f in enumerate(self.food)
                     if (hx-f.x)**2 + (hy-f.y)**2 < (SEGMENT_RADIUS + f.radius)**2]
            for i in reversed(eaten):
                f = self.food.pop(i)
                snake.grow(GROW_PER_FOOD * f.value)
                self.particles.emit_eat(f.x, f.y, f.color)
                sounds.play("eat_big" if f.big else "eat", 0.6)

            collected = [i for i, pu in enumerate(self.powerups)
                         if (hx-pu.x)**2 + (hy-pu.y)**2 < pu.collect_radius()**2]
            for i in reversed(collected):
                pu = self.powerups.pop(i)
                snake.add_powerup(pu.pu_type)
                self.particles.emit_powerup(pu.x, pu.y, pu.color)
                sounds.play("powerup")

            for other in alive:
                if snake is other:
                    continue
                if snake.invincible_timer > 0:
                    break
                if snake.collides_with_snake(other):
                    if snake.has_shield:
                        sounds.play("shield_hit")
                        del snake.powerups["shield"]
                        snake.invincible_timer = 1.5
                    else:
                        self._kill_snake(snake, killer=other)
                        break


    def _kill_snake(self, snake, killer=None):
        if not snake.alive:
            return
        snake.die(killer)
        for fx, fy in snake.get_food_drops():
            self.food.append(Food(fx + random.uniform(-20, 20),
                                  fy + random.uniform(-20, 20),
                                  big=random.random() < 0.15))
        self.particles.emit_death(snake.head.x, snake.head.y, snake.head_color)
        sounds.play("die")
        if killer and killer is not snake:
            sounds.play("kill", 0.7)
            self._kill_feed.append((f"{killer.name} elimino a {snake.name}", 0.0))


    def draw(self):
        self.screen.fill(C_BG)

        if self._split:
            self._draw_split()
        else:
            self._draw_single()

        self.hud.draw_leaderboard(self.screen, self.snakes)

        self.hud.draw_minimap(self.screen, self.snakes, self.food, self.powerups,
                              self._cameras, self._viewports, self._t)

        self.hud.draw_kill_feed(self.screen, self._kill_feed)

        if self._split:
            self._draw_viewport_borders()

        if self._state == "countdown":
            self.hud.draw_countdown(self.screen, max(0, math.ceil(self._countdown)))
        if self._state == "death":
            dead = next((s for s in self.snakes if s.is_human and not s.alive), None)
            if dead:
                self.hud.draw_death_screen(self.screen, dead, self._death_timer)
        if self._state == "gameover":
            self._draw_gameover()
        if self._paused:
            self.hud.draw_pause(self.screen)

    def _draw_single(self):
        """Modo un jugador: dibuja directo en screen."""
        cam = self._cameras[0]
        cx, cy = cam[0], cam[1]
        vp = self._viewports[0]
        surf = self.screen

        self._draw_world(surf, cx, cy, vp.w, vp.h, offset_x=0, offset_y=0)

        focus = self._get_focus_snake(0)
        if focus and focus.alive:
            self.hud.draw_player_hud(surf, focus, self._t,
                                     vp.x, vp.y, vp.w, vp.h)

    def _draw_split(self):
        """Pantalla dividida: renderiza cada viewport en su surface y lo blitea."""
        humans = self._human_snakes()
        for i, (vp, vp_surf) in enumerate(zip(self._viewports, self._vp_surfs)):
            cam = self._cameras[i]
            cx, cy = cam[0], cam[1]

            vp_surf.fill(C_BG)
            self._draw_world(vp_surf, cx, cy, vp.w, vp.h, offset_x=0, offset_y=0)

            snake = self._get_focus_snake(i)
            if snake and snake.alive:
                self.hud.draw_player_hud(vp_surf, snake, self._t,
                                         0, 0, vp.w, vp.h)

            label = self.hud.font(16).render(
                f"[ {snake.name if snake else '?'} ]", True,
                snake.head_color if snake else (200, 200, 200)
            )
            vp_surf.blit(label, (8, 8))

            self.screen.blit(vp_surf, (vp.x, vp.y))

    def _draw_viewport_borders(self):
        """Líneas de separación entre viewports."""
        n = self.num_players
        if n == 2:
            pygame.draw.line(self.screen, (40, 40, 60),
                             (SCREEN_W // 2, 0), (SCREEN_W // 2, SCREEN_H), 3)
        elif n == 3:
            pygame.draw.line(self.screen, (40, 40, 60),
                             (SCREEN_W // 2, 0), (SCREEN_W // 2, SCREEN_H // 2), 3)
            pygame.draw.line(self.screen, (40, 40, 60),
                             (0, SCREEN_H // 2), (SCREEN_W, SCREEN_H // 2), 3)
        elif n == 4:
            pygame.draw.line(self.screen, (40, 40, 60),
                             (SCREEN_W // 2, 0), (SCREEN_W // 2, SCREEN_H), 3)
            pygame.draw.line(self.screen, (40, 40, 60),
                             (0, SCREEN_H // 2), (SCREEN_W, SCREEN_H // 2), 3)

    def _draw_world(self, surf, cx, cy, vp_w, vp_h, offset_x, offset_y):
        """Dibuja el mundo (fondo + entidades) en `surf` con la cámara dada."""
        grid_size = 80
        sx = -(int(cx) % grid_size)
        sy = -(int(cy) % grid_size)
        for gx in range(sx, vp_w + grid_size, grid_size):
            pygame.draw.line(surf, C_GRID, (gx, 0), (gx, vp_h), 1)
        for gy in range(sy, vp_h + grid_size, grid_size):
            pygame.draw.line(surf, C_GRID, (0, gy), (vp_w, gy), 1)

        for stx, sty, br in self._stars:
            px = int((stx - cx * 0.2) % vp_w)
            py = int((sty - cy * 0.2) % vp_h)
            c = int(br * 50)
            pygame.draw.circle(surf, (c, c, c + 20), (px, py), 1 if br < 1.2 else 2)

        for f in self.food:
            sx_f = f.x - cx
            sy_f = f.y - cy
            if -20 < sx_f < vp_w + 20 and -20 < sy_f < vp_h + 20:
                f.draw(surf, cx, cy, self._t)

        for pu in self.powerups:
            sx_p = pu.x - cx
            sy_p = pu.y - cy
            if -30 < sx_p < vp_w + 30 and -30 < sy_p < vp_h + 30:
                pu.draw(surf, cx, cy, self._t, self.hud.font(14))

        for s in sorted(self.snakes, key=lambda x: x.length):
            if s.alive:
                s.draw(surf, cx, cy)
                s.draw_name(surf, cx, cy, self.hud.font(12))

        self.particles.draw(surf, cx, cy)

        bx1, by1 = int(-cx), int(-cy)
        bx2, by2 = int(WORLD_W - cx), int(WORLD_H - cy)
        pygame.draw.rect(surf, (200, 80, 80), (bx1, by1, bx2 - bx1, by2 - by1), 4)

    def _draw_gameover(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        winner = max(self.snakes, key=lambda s: s.score)
        txt = self.hud.font(48).render("FIN DE PARTIDA", True, (255, 210, 50))
        self.screen.blit(txt, txt.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 60)))
        wt = self.hud.font(32).render(
            f"Ganador: {winner.name}  ({winner.score} pts)", True, (255, 255, 255))
        self.screen.blit(wt, wt.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 10)))
        sub = self.hud.font(18).render("Volviendo al menu...", True, (180, 180, 200))
        self.screen.blit(sub, sub.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 70)))