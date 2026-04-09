"""
Módulo de la serpiente (jugador y bot).
"""

import math
import random
import pygame

from .constants import (
    WORLD_W, WORLD_H, SEGMENT_RADIUS, SEGMENT_GAP,
    INITIAL_LENGTH, SPEED_BASE, SPEED_BOOST, BOOST_DRAIN,
    GROW_PER_FOOD, TURN_SPEED,
    PU_SPEED, PU_GHOST, PU_MAGNET, PU_SHIELD, PU_DOUBLE,
    POWERUP_DURATION, AI_REACTION_TIME
)


class Segment:
    """Un segmento del cuerpo."""
    __slots__ = ("x", "y")

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y


class Snake:
    """
    Serpiente genérica.  Subclasificada por PlayerSnake y BotSnake.
    """

    def __init__(self, color_info: dict, snake_id: int, x=None, y=None):
        self.id = snake_id
        self.color_info = color_info
        self.body_color = color_info["body"]
        self.head_color = color_info["head"]
        self.glow_color  = color_info.get("glow", (*color_info["body"][:3], 60))
        self.name = color_info["name"]

        # Posición inicial aleatoria si no se especifica
        cx = x if x is not None else random.randint(300, WORLD_W - 300)
        cy = y if y is not None else random.randint(300, WORLD_H - 300)
        self.angle = random.uniform(0, 2 * math.pi)

        # Cuerpo
        self.segments: list[Segment] = []
        for i in range(INITIAL_LENGTH):
            sx = cx - i * SEGMENT_GAP * math.cos(self.angle)
            sy = cy - i * SEGMENT_GAP * math.sin(self.angle)
            self.segments.append(Segment(sx, sy))

        self.target_length = INITIAL_LENGTH
        self.alive = True
        self.boosting = False

        # Score / estadísticas
        self.score = 0
        self.kills = 0
        self.foods_eaten = 0

        # Power-ups activos  {tipo: tiempo_restante}
        self.powerups: dict[str, float] = {}

        # Animación de muerte
        self.death_timer = 0.0

        # Serpiente que te mató (para crédito de kill)
        self.killed_by: "Snake | None" = None

        # Tiempo vivo
        self.lifetime = 0.0

        # Partículas de movimiento
        self._boost_particle_timer = 0.0

    # ------------------------------------------------------------------ #
    #  Propiedades derivadas
    # ------------------------------------------------------------------ #

    @property
    def head(self) -> Segment:
        return self.segments[0]

    @property
    def length(self) -> int:
        return len(self.segments)

    @property
    def speed(self) -> float:
        base = SPEED_BOOST if self.boosting else SPEED_BASE
        if PU_SPEED in self.powerups:
            base *= 1.5
        return base

    @property
    def has_ghost(self) -> bool:
        return PU_GHOST in self.powerups

    @property
    def has_shield(self) -> bool:
        return PU_SHIELD in self.powerups

    @property
    def double_score(self) -> bool:
        return PU_DOUBLE in self.powerups

    @property
    def has_magnet(self) -> bool:
        return PU_MAGNET in self.powerups

    # ------------------------------------------------------------------ #
    #  Actualización
    # ------------------------------------------------------------------ #

    def update(self, dt: float):
        if not self.alive:
            return

        self.lifetime += dt

        # Mover cabeza
        spd = self.speed
        new_x = self.head.x + spd * dt * math.cos(self.angle)
        new_y = self.head.y + spd * dt * math.sin(self.angle)

        # Wrap-around del mundo
        new_x = new_x % WORLD_W
        new_y = new_y % WORLD_H

        self.segments.insert(0, Segment(new_x, new_y))

        # Ajustar longitud
        while len(self.segments) > self.target_length:
            self.segments.pop()

        # Consumo de boost
        if self.boosting and self.target_length > INITIAL_LENGTH + 3:
            self.target_length -= BOOST_DRAIN * dt

        # Power-ups: descontar tiempo
        expired = [k for k, v in self.powerups.items() if v <= 0]
        for k in expired:
            del self.powerups[k]
        for k in list(self.powerups):
            self.powerups[k] -= dt

        self._boost_particle_timer -= dt

    def grow(self, amount: int = GROW_PER_FOOD):
        mult = 2 if self.double_score else 1
        self.target_length += amount * mult
        self.score += 10 * mult
        self.foods_eaten += 1

    def add_powerup(self, pu_type: str):
        self.powerups[pu_type] = POWERUP_DURATION

    def die(self, killer: "Snake | None" = None):
        self.alive = False
        self.killed_by = killer
        if killer and killer is not self:
            killer.kills += 1
            killer.score += max(50, self.length * 2)

    # ------------------------------------------------------------------ #
    #  Colisiones
    # ------------------------------------------------------------------ #

    def head_rect(self) -> pygame.Rect:
        r = SEGMENT_RADIUS
        return pygame.Rect(self.head.x - r, self.head.y - r, r * 2, r * 2)

    def collides_with_segment(self, sx: float, sy: float, radius: float = SEGMENT_RADIUS) -> bool:
        dx = self.head.x - sx
        dy = self.head.y - sy
        return (dx * dx + dy * dy) < (SEGMENT_RADIUS + radius) ** 2

    def collides_with_snake(self, other: "Snake", skip_head: bool = True) -> bool:
        """¿La cabeza de self choca con el cuerpo de other?"""
        if self.has_ghost:
            return False
        start = 1 if (other is self or skip_head) else 0
        hx, hy = self.head.x, self.head.y
        for seg in other.segments[start:]:
            dx = hx - seg.x
            dy = hy - seg.y
            if dx * dx + dy * dy < (SEGMENT_RADIUS * 2) ** 2:
                return True
        return False

    # ------------------------------------------------------------------ #
    #  Dibujo
    # ------------------------------------------------------------------ #

    def draw(self, surface: pygame.Surface, camera_x: float, camera_y: float,
             alpha_override: int = 255):
        if not self.segments:
            return

        n = len(self.segments)
        body_c = self.body_color
        head_c = self.head_color
        glow_c = self.glow_color

        # Opacidad para ghost
        ghost_alpha = 120 if self.has_ghost else alpha_override

        for i in range(n - 1, -1, -1):
            seg = self.segments[i]
            sx = int(seg.x - camera_x)
            sy = int(seg.y - camera_y)

            # Tamaño varía un poco (cabeza más grande)
            t = 1 - (i / n) * 0.3   # 1.0 en cabeza → 0.7 en cola
            r = max(4, int(SEGMENT_RADIUS * t))

            # Color interpolado
            if i == 0:
                color = head_c
            else:
                ratio = i / max(1, n - 1)
                color = (
                    int(head_c[0] * (1 - ratio) + body_c[0] * ratio),
                    int(head_c[1] * (1 - ratio) + body_c[1] * ratio),
                    int(head_c[2] * (1 - ratio) + body_c[2] * ratio),
                )

            # Glow (halo exterior)
            if i == 0 or i % 4 == 0:
                glow_surf = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
                ga = int(glow_c[3] * (ghost_alpha / 255))
                pygame.draw.circle(glow_surf, (*glow_c[:3], ga), (r * 2, r * 2), r * 2)
                surface.blit(glow_surf, (sx - r * 2, sy - r * 2))

            # Cuerpo
            if ghost_alpha < 255:
                seg_surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(seg_surf, (*color, ghost_alpha), (r + 1, r + 1), r)
                surface.blit(seg_surf, (sx - r - 1, sy - r - 1))
            else:
                pygame.draw.circle(surface, color, (sx, sy), r)
                # Highlight
                pygame.draw.circle(surface, (
                    min(255, color[0] + 60),
                    min(255, color[1] + 60),
                    min(255, color[2] + 60)
                ), (sx - r // 3, sy - r // 3), max(2, r // 3))

        # Ojos en la cabeza
        self._draw_eyes(surface, camera_x, camera_y)

        # Indicador de shield
        if self.has_shield:
            hx = int(self.head.x - camera_x)
            hy = int(self.head.y - camera_y)
            shield_surf = pygame.Surface((SEGMENT_RADIUS * 5, SEGMENT_RADIUS * 5), pygame.SRCALPHA)
            pygame.draw.circle(shield_surf, (80, 220, 255, 80),
                               (SEGMENT_RADIUS * 2 + 2, SEGMENT_RADIUS * 2 + 2),
                               SEGMENT_RADIUS * 2 + 2)
            surface.blit(shield_surf,
                         (hx - SEGMENT_RADIUS * 2 - 2, hy - SEGMENT_RADIUS * 2 - 2))

    def _draw_eyes(self, surface, cam_x, cam_y):
        hx = int(self.head.x - cam_x)
        hy = int(self.head.y - cam_y)
        r = SEGMENT_RADIUS

        eye_offset = r * 0.6
        perp = self.angle + math.pi / 2
        ex1 = hx + eye_offset * math.cos(perp)
        ey1 = hy + eye_offset * math.sin(perp)
        ex2 = hx - eye_offset * math.cos(perp)
        ey2 = hy - eye_offset * math.sin(perp)

        eye_r = max(2, r // 3)
        pygame.draw.circle(surface, (255, 255, 255), (int(ex1), int(ey1)), eye_r)
        pygame.draw.circle(surface, (255, 255, 255), (int(ex2), int(ey2)), eye_r)
        # Pupila
        pupil_r = max(1, eye_r // 2)
        px = math.cos(self.angle) * pupil_r * 0.5
        py = math.sin(self.angle) * pupil_r * 0.5
        pygame.draw.circle(surface, (10, 10, 20),
                           (int(ex1 + px), int(ey1 + py)), pupil_r)
        pygame.draw.circle(surface, (10, 10, 20),
                           (int(ex2 + px), int(ey2 + py)), pupil_r)

    def draw_name(self, surface: pygame.Surface, camera_x: float, camera_y: float,
                  font: pygame.font.Font):
        if not self.alive:
            return
        hx = int(self.head.x - camera_x)
        hy = int(self.head.y - camera_y)
        label = font.render(self.name, True, (255, 255, 255))
        rect = label.get_rect(center=(hx, hy - SEGMENT_RADIUS * 2 - 4))
        surface.blit(label, rect)

    def get_food_drops(self) -> list[tuple[float, float]]:
        """Devuelve posiciones donde soltar comida al morir."""
        drops = []
        step = max(1, len(self.segments) // 20)
        for i, seg in enumerate(self.segments[::step]):
            drops.append((seg.x, seg.y))
        return drops


# ------------------------------------------------------------------ #
#  Serpiente controlada por un humano
# ------------------------------------------------------------------ #

class PlayerSnake(Snake):
    def __init__(self, color_info, snake_id, keys: dict, x=None, y=None):
        super().__init__(color_info, snake_id, x, y)
        self.keys = keys
        self.is_human = True

    def handle_input(self, pressed):
        """Ajusta el ángulo según teclas presionadas."""
        turning = False
        if pressed[self.keys["left"]]:
            self.angle -= TURN_SPEED * (1 / 60)
            turning = True
        if pressed[self.keys["right"]]:
            self.angle += TURN_SPEED * (1 / 60)
            turning = True
        self.boosting = pressed[self.keys["boost"]]

    def handle_input_dt(self, pressed, dt: float):
        if pressed[self.keys["left"]]:
            self.angle -= TURN_SPEED * dt
        if pressed[self.keys["right"]]:
            self.angle += TURN_SPEED * dt
        self.boosting = pressed[self.keys["boost"]]


# ------------------------------------------------------------------ #
#  Serpiente controlada por IA
# ------------------------------------------------------------------ #

class BotSnake(Snake):
    """IA con tres comportamientos: buscar comida, evitar peligros, perseguir."""

    BEHAVIOR_WANDER  = "wander"
    BEHAVIOR_HUNT    = "hunt"
    BEHAVIOR_FLEE    = "flee"

    def __init__(self, color_info, snake_id, difficulty: float = 1.0, x=None, y=None):
        super().__init__(color_info, snake_id, x, y)
        self.is_human = False
        self.difficulty = difficulty   # 0.5 (fácil) … 2.0 (difícil)

        self._react_timer = 0.0
        self._target_angle = self.angle
        self._behavior = self.BEHAVIOR_WANDER
        self._wander_target: tuple[float, float] | None = None
        self._wander_timer = 0.0

    def ai_update(self, dt: float, food_list: list, snakes: list["Snake"],
                  powerups: list):
        """Toma decisiones de IA y actualiza el ángulo."""
        self._react_timer -= dt
        self._wander_timer -= dt

        if self._react_timer > 0:
            # Suavizar giro hacia objetivo
            self._smooth_turn(dt)
            self.update(dt)
            return

        self._react_timer = AI_REACTION_TIME / self.difficulty

        hx, hy = self.head.x, self.head.y

        # ── 1. Detección de peligros cercanos ──
        danger_angle = self._find_danger(snakes)
        if danger_angle is not None:
            self._behavior = self.BEHAVIOR_FLEE
            flee_angle = danger_angle + math.pi + random.uniform(-0.4, 0.4)
            self._target_angle = flee_angle
            self.boosting = True
            self._smooth_turn(dt)
            self.update(dt)
            return

        self.boosting = False

        # ── 2. Buscar power-up cercano ──
        pu_target = self._find_nearest_powerup(powerups)
        if pu_target:
            self._behavior = self.BEHAVIOR_HUNT
            self._target_angle = math.atan2(pu_target[1] - hy, pu_target[0] - hx)
            self._smooth_turn(dt)
            self.update(dt)
            return

        # ── 3. Buscar comida más cercana ──
        food_target = self._find_nearest_food(food_list)
        if food_target:
            self._behavior = self.BEHAVIOR_WANDER
            self._target_angle = math.atan2(food_target[1] - hy, food_target[0] - hx)
            self._smooth_turn(dt)
            self.update(dt)
            return

        # ── 4. Deambular ──
        if self._wander_target is None or self._wander_timer <= 0:
            self._wander_target = (
                random.uniform(200, WORLD_W - 200),
                random.uniform(200, WORLD_H - 200),
            )
            self._wander_timer = random.uniform(3, 8)
        tx, ty = self._wander_target
        self._target_angle = math.atan2(ty - hy, tx - hx)
        self._smooth_turn(dt)
        self.update(dt)

    def _smooth_turn(self, dt: float):
        """Gira gradualmente hacia _target_angle."""
        diff = (self._target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi
        max_turn = TURN_SPEED * dt * self.difficulty
        if abs(diff) < max_turn:
            self.angle = self._target_angle
        else:
            self.angle += max_turn * (1 if diff > 0 else -1)

    def _find_danger(self, snakes: list) -> float | None:
        """Devuelve el ángulo hacia el peligro si existe uno cercano."""
        from .constants import AI_DANGER_RADIUS
        hx, hy = self.head.x, self.head.y
        closest_dist = AI_DANGER_RADIUS * AI_DANGER_RADIUS

        for snake in snakes:
            if snake is self or not snake.alive:
                continue
            # Peligro: cabeza de otro bot/jugador más grande
            if snake.length > self.length * 0.8:
                dx = snake.head.x - hx
                dy = snake.head.y - hy
                d2 = dx * dx + dy * dy
                if d2 < closest_dist:
                    closest_dist = d2
                    return math.atan2(dy, dx)
            # Peligro: segmento corporal de cualquier serpiente
            for seg in snake.segments[5:]:
                dx = seg.x - hx
                dy = seg.y - hy
                d2 = dx * dx + dy * dy
                if d2 < (AI_DANGER_RADIUS * 0.6) ** 2:
                    return math.atan2(dy, dx)
        return None

    def _find_nearest_food(self, food_list) -> tuple[float, float] | None:
        from .constants import AI_SIGHT_RADIUS
        hx, hy = self.head.x, self.head.y
        best = None
        best_d2 = AI_SIGHT_RADIUS ** 2
        for f in food_list:
            dx = f.x - hx
            dy = f.y - hy
            d2 = dx * dx + dy * dy
            if d2 < best_d2:
                best_d2 = d2
                best = (f.x, f.y)
        return best

    def _find_nearest_powerup(self, powerups) -> tuple[float, float] | None:
        from .constants import AI_SIGHT_RADIUS
        hx, hy = self.head.x, self.head.y
        best = None
        best_d2 = (AI_SIGHT_RADIUS * 0.8) ** 2
        for pu in powerups:
            dx = pu.x - hx
            dy = pu.y - hy
            d2 = dx * dx + dy * dy
            if d2 < best_d2:
                best_d2 = d2
                best = (pu.x, pu.y)
        return best