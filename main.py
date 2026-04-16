"""
Slither.io Clone - Pygame Edition
Controles:
  Jugador 1: WASD + SHIFT(boost)
  Jugador 2: Flechas + RSHIFT
  Jugador 3: IJKL + U
  Jugador 4: Numpad 8456 + 0
  ESC: Pausar / Volver al menu
"""

import pygame
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from game.constants import *
from game.menu import Menu
from game.game_state import GameState


def main():
    pygame.init()
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    except pygame.error:
        print("Advertencia: no se pudo inicializar el audio. El juego correra sin sonido.")

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Slither.io - Pygame Edition")
    clock = pygame.time.Clock()

    menu = Menu(screen)
    state = "menu"
    game = None

    while True:
        clock.tick(FPS)

        if state == "menu":
            result = menu.update_and_draw()
            if result == "quit":
                break
            elif result is not None:
                mode, num_players, num_bots, _, _, player_cfgs = result
                game = GameState(screen, mode, num_players, num_bots,
                                 player_configs=player_cfgs)
                state = "game"

        elif state == "game":
            result = game.update(1 / FPS)
            game.draw()
            if result == "menu":
                game = None
                state = "menu"
                menu.reset()

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()