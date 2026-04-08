"""
Slither.io Clone - Pygame Edition
==================================
Controles:
  Jugador 1: WASD
  Jugador 2: Flechas del teclado
  Jugador 3: IJKL
  Jugador 4: Numpad 8456
  ESC: Pausar / Volver al menú
"""

import pygame
import sys
import os

# Aseguramos que los imports relativos funcionen
sys.path.insert(0, os.path.dirname(__file__))

from constants import *
from game_menu import Menu
from game_state import GameState
from network_server import GameServer
from network_client import GameClient

def main():
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("🐍 Slither.io - Pygame Edition")
    clock = pygame.time.Clock()

    # Icono
    icon_surf = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.circle(icon_surf, (80, 220, 80), (16, 16), 14)
    pygame.draw.circle(icon_surf, (40, 160, 40), (16, 16), 10)
    pygame.display.set_icon(icon_surf)

    menu = Menu(screen)
    state = "menu"
    game = None
    server = None
    client = None

    while True:
        dt = clock.tick(FPS) / 1000.0

        if state == "menu":
            result = menu.update_and_draw()
            if result == "quit":
                break
            elif result is not None:
                mode, num_players, num_bots, net_role, net_addr = result
                if net_role == "server":
                    server = GameServer(net_addr[1])
                    server.start()
                    game = GameState(screen, mode, num_players, num_bots, server=server)
                elif net_role == "client":
                    client = GameClient(net_addr[0], net_addr[1])
                    client.connect()
                    game = GameState(screen, mode, num_players, num_bots, client=client)
                else:
                    game = GameState(screen, mode, num_players, num_bots)
                state = "game"

        elif state == "game":
            result = game.update(dt)
            game.draw()
            if result == "menu":
                if server:
                    server.stop()
                    server = None
                if client:
                    client.disconnect()
                    client = None
                game = None
                state = "menu"
                menu.reset()

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()