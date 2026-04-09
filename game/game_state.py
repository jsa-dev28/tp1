"""
Estado principal del juego: inicializa, actualiza y dibuja todo.
"""

import math
import random
import time
import pygame

from .constants import (
    SCREEN_W, SCREEN_H, WORLD_W, WORLD_H, FPS,
    FOOD_COUNT_TARGET, FOOD_RADIUS,
    POWERUP_SPAWN_INTERVAL,
    SEGMENT_RADIUS, GROW_PER_FOOD,
    PLAYER_COLORS, BOT_COLORS, PLAYER_KEYS,
    C_BG, C_GRID,
    PU_MAGNET,
)
from .snake import PlayerSnake, BotSnake
from .entities import Food, PowerUp
from .particles import ParticleSystem
from .hud import HUD
from . import sounds


class GameState:
    """Gestiona toda la lógica y el renderizado de una partida."""

    def __init__(self, screen: pygame.Surface, mode: str,
                 num_players: int, num_bots: int,
                 server=None, client=None):
        self.screen = screen
        self.mode = mode
        self.num_players = num_players
        self.num_bots = num_bots
        self.server = server
        self.client = client

        self.hud = HUD(screen)
        self.particles = ParticleSystem()

        self._t = 0.0
        self._paused = False
        self._state = "countdown"
        self._countdown = 3.0
        self._death_timer = 0.0

        self.cam_x = 0.0
        self.cam_y = 0.0

        self._pu_timer = POWERUP_SPAWN_INTERVAL

        self._kill_feed: list[tuple[str, float]] = []

        self.snakes: list = []
        self._init_snakes()

        self.food: list[Food] = []
        self._spawn_initial_food()

        self.powerups: list[PowerUp] = []

        self._stars = [(random.uniform(0, WORLD_W), random.uniform(0, WORLD_H),
                        random.uniform(0.5, 2.0)) for _ in range(400)]

        sounds.init()
        sounds.play("countdown")

    def _init_snakes(self):
        margin = 400
        positions = []

        for i in range(self.num_players):
            color = PLAYER_COLORS[i % len(PLAYER_COLORS)]
            keys  = PLAYER_KEYS[i % len(PLAYER_KEYS)]
            x = random.uniform(margin, WORLD_W - margin)
            y = random.uniform(margin, WORLD_H - margin)
            s = PlayerSnake(color, i, keys, x, y)
            positions.append((x, y))
            self.snakes.append(s)

        for j in range(self.num_bots):
            color = BOT_COLORS[j % len(BOT_COLORS)]
            difficulty = random.uniform(0.8, 1.6)
            x = random.uniform(margin, WORLD_W - margin)
            y = random.uniform(margin, WORLD_H - margin)
            b = BotSnake(color, self.num_players + j, difficulty, x, y)
            self.snakes.append(b)

    def _spawn_initial_food(self):
        for _ in range(FOOD_COUNT_TARGET):
            big = random.random() < 0.08
            self.food.append(Food(big=big))

    def _get_focus_snake(self):
        """Devuelve la serpiente a seguir con la cámara."""
        humans = [s for s in self.snakes if s.is_human and s.alive]
        if humans:
            return humans[0]
        alive = [s for s in self.snakes if s.alive]
        if alive:
            return max(alive, key=lambda s: s.length)
        return None

    def update(self, dt: float) -> str | None:
        """Actualiza el estado. Devuelve "menu" si se debe volver al menú."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "menu"
            if event.type == pygame.KEYDOWN:
                result = self._handle_key(event.key)
                if result:
                    return result

        if self._state == "countdown":
            self._update_countdown(dt)
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
            if self._death_timer > 3.0:
                return "menu"
            return None

        self._t += dt
        self._pu_timer -= dt
        self._update_kill_feed(dt)

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
                    self.particles.emit_boost(s.head.x, s.head.y,
                                             s.body_color, s.angle)
                    s._boost_particle_timer = 0.04

        for s in self.snakes:
            if s.alive and s.has_magnet:
                self._apply_magnet(s)

        self._check_collisions()

        while len(self.food) < FOOD_COUNT_TARGET:
            big = random.random() < 0.08
            self.food.append(Food(big=big))

        if self._pu_timer <= 0:
            self.powerups.append(PowerUp())
            self._pu_timer = POWERUP_SPAWN_INTERVAL + random.uniform(-2, 2)

        for pu in self.powerups:
            pu.update(dt)

        self.particles.update(dt)

        focus = self._get_focus_snake()
        if focus:
            target_cx = focus.head.x - SCREEN_W / 2
            target_cy = focus.head.y - SCREEN_H / 2
            self.cam_x += (target_cx - self.cam_x) * 0.1
            self.cam_y += (target_cy - self.cam_y) * 0.1

        humans_alive = [s for s in self.snakes if s.is_human and s.alive]
        if self.num_players > 0 and not humans_alive:
            self._state = "death"
            self._death_timer = 0.0

        all_alive = [s for s in self.snakes if s.alive]
        if len(all_alive) <= 1 and len(self.snakes) > 1:
            self._state = "gameover"
            self._death_timer = 0.0

        if self.server:
            self.server.broadcast_state(self._serialize_state())
        if self.client:
            remote = self.client.poll_state()
            if remote:
                self._apply_remote_state(remote)

        return None

    def _update_countdown(self, dt):
        self._countdown -= dt
        n = max(0, math.ceil(self._countdown))
        if n == 0 and self._countdown < 0:
            self._state = "playing"
            sounds.play("go")

    def _handle_key(self, key):
        if key == pygame.K_ESCAPE:
            if self._state == "playing":
                self._paused = not self._paused
            elif self._state in ("death", "gameover", "countdown"):
                return "menu"
        if self._paused and key == pygame.K_q:
            return "menu"
        return None

    def _update_kill_feed(self, dt):
        self._kill_feed = [(t, a + dt) for t, a in self._kill_feed if a + dt < 4.0]

    def _apply_magnet(self, snake):
        magnet_r = 200
        hx, hy = snake.head.x, snake.head.y
        for f in self.food:
            dx = hx - f.x
            dy = hy - f.y
            d = math.hypot(dx, dy)
            if 0 < d < magnet_r:
                force = (magnet_r - d) / magnet_r * 180
                f.x += dx / d * force * 0.016
                f.y += dy / d * force * 0.016

    def _check_collisions(self):
        alive = [s for s in self.snakes if s.alive]

        for snake in alive:
            hx, hy = snake.head.x, snake.head.y

            eaten = []
            for i, f in enumerate(self.food):
                dx = hx - f.x
                dy = hy - f.y
                if dx * dx + dy * dy < (SEGMENT_RADIUS + f.radius) ** 2:
                    snake.grow(GROW_PER_FOOD * f.value)
                    self.particles.emit_eat(f.x, f.y, f.color)
                    sounds.play("eat" if not f.big else "eat_big", 0.6)
                    eaten.append(i)
            for i in reversed(eaten):
                self.food.pop(i)

            collected = []
            for i, pu in enumerate(self.powerups):
                dx = hx - pu.x
                dy = hy - pu.y
                if dx * dx + dy * dy < pu.collect_radius() ** 2:
                    snake.add_powerup(pu.pu_type)
                    self.particles.emit_powerup(pu.x, pu.y, pu.color)
                    sounds.play("powerup")
                    collected.append(i)
            for i in reversed(collected):
                self.powerups.pop(i)

            for other in alive:
                if snake is other:
                    continue
                if snake.collides_with_snake(other, skip_head=(other is snake)):
                    if snake.has_shield:
                        sounds.play("shield_hit")
                        del snake.powerups["shield"]
                    else:
                        self._kill_snake(snake, killer=other)
                        break

            if snake.alive and len(snake.segments) > 25:
                for seg in snake.segments[20:]:
                    dx = hx - seg.x
                    dy = hy - seg.y
                    if dx * dx + dy * dy < (SEGMENT_RADIUS * 1.8) ** 2:
                        self._kill_snake(snake, killer=snake)
                        break

    def _kill_snake(self, snake, killer=None):
        if not snake.alive:
            return
        snake.die(killer)

        drops = snake.get_food_drops()
        for (fx, fy) in drops:
            big = random.random() < 0.15
            self.food.append(Food(fx + random.uniform(-20, 20),
                                  fy + random.uniform(-20, 20), big))

        self.particles.emit_death(snake.head.x, snake.head.y, snake.head_color)
        sounds.play("die")

        if killer and killer is not snake:
            sounds.play("kill", 0.7)
            self._kill_feed.append((f"☠ {killer.name} eliminó a {snake.name}", 0.0))

    def draw(self):
        self.screen.fill(C_BG)
        self._draw_background()

        cx, cy = self.cam_x, self.cam_y

        for s in sorted(self.snakes, key=lambda x: x.length):
            if s.alive:
                s.draw(self.screen, cx, cy)
                s.draw_name(self.screen, cx, cy, self.hud.font(12))

        for f in self.food:
            f.draw(self.screen, cx, cy, self._t)

        for pu in self.powerups:
            pu.draw(self.screen, cx, cy, self._t, self.hud.font(14))

        self.particles.draw(self.screen, cx, cy)

        self._draw_world_border(cx, cy)

        focus = self._get_focus_snake()
        self.hud.draw(self.snakes, self.food, self.powerups, focus,
                      self._t, self._paused, self.mode)
        self.hud.draw_kill_feed(self._kill_feed, self._t)

        if self._state == "countdown":
            n = max(0, math.ceil(self._countdown))
            self.hud.draw_countdown(n)

        if self._state == "death":
            dead_human = next((s for s in self.snakes if s.is_human and not s.alive), None)
            if dead_human:
                self.hud.draw_death_screen(dead_human, self.snakes, self._death_timer)

        if self._state == "gameover":
            self._draw_gameover()

    def _draw_background(self):
        """Grid y estrellas del fondo."""
        cx, cy = int(self.cam_x), int(self.cam_y)
        grid_size = 80

        start_x = -(cx % grid_size)
        start_y = -(cy % grid_size)
        for gx in range(start_x, SCREEN_W + grid_size, grid_size):
            pygame.draw.line(self.screen, C_GRID, (gx, 0), (gx, SCREEN_H), 1)
        for gy in range(start_y, SCREEN_H + grid_size, grid_size):
            pygame.draw.line(self.screen, C_GRID, (0, gy), (SCREEN_W, gy), 1)

        for sx, sy, br in self._stars:
            px = int((sx - cx * 0.2) % SCREEN_W)
            py = int((sy - cy * 0.2) % SCREEN_H)
            c = int(br * 50)
            r = 1 if br < 1.2 else 2
            pygame.draw.circle(self.screen, (c, c, c + 20), (px, py), r)

    def _draw_world_border(self, cx, cy):
        """Dibuja el borde del mundo visible."""
        bx1 = int(-cx)
        by1 = int(-cy)
        bx2 = int(WORLD_W - cx)
        by2 = int(WORLD_H - cy)
        pygame.draw.rect(self.screen, (200, 80, 80),
                         (bx1, by1, bx2 - bx1, by2 - by1), 4)
        focus = self._get_focus_snake()
        if focus:
            hx, hy = focus.head.x, focus.head.y
            warn_dist = 150
            near_border = (hx < warn_dist or hx > WORLD_W - warn_dist or
                           hy < warn_dist or hy > WORLD_H - warn_dist)
            if near_border:
                pulse = abs(math.sin(self._t * 4))
                warn_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                pygame.draw.rect(warn_surf, (255, 50, 50, int(60 * pulse)),
                                 (0, 0, SCREEN_W, SCREEN_H), 20)
                self.screen.blit(warn_surf, (0, 0))

    def _draw_gameover(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        winner = max(self.snakes, key=lambda s: s.score)
        txt = self.hud.font(48).render("🏆  FIN DE PARTIDA", True, (255, 210, 50))
        self.screen.blit(txt, txt.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 60)))

        win_txt = self.hud.font(32).render(f"Ganador: {winner.name}  ({winner.score} pts)",
                                           True, (255, 255, 255))
        self.screen.blit(win_txt, win_txt.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 10)))

        sub = self.hud.font(18).render("Volviendo al menú...", True, (180, 180, 200))
        self.screen.blit(sub, sub.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 70)))

    # ------------------------------------------------------------------ #
    #  Red LAN (stubs simples)
    # ------------------------------------------------------------------ #

    def _serialize_state(self) -> dict:
        return {
            "snakes": [
                {"id": s.id, "x": s.head.x, "y": s.head.y,
                 "score": s.score, "alive": s.alive}
                for s in self.snakes
            ]
        }

    def _apply_remote_state(self, state: dict):
        pass