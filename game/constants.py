"""
Constantes globales del juego.
"""

# Pantalla
SCREEN_W = 1280
SCREEN_H = 720
FPS = 60

# Mundo (más grande que la pantalla → scroll de cámara)
WORLD_W = 3000
WORLD_H = 3000

# Serpiente
SEGMENT_RADIUS = 10
SEGMENT_GAP = 8          # distancia entre centros de segmentos
INITIAL_LENGTH = 10      # segmentos al comenzar
SPEED_BASE = 160         # px/s
SPEED_BOOST = 280        # px/s al usar boost
BOOST_DRAIN = 1.5        # segmentos que se pierden por segundo de boost
GROW_PER_FOOD = 5        # segmentos que se ganan por comida
TURN_SPEED = 3.5         # rad/s

# Comida
FOOD_COUNT_TARGET = 250  # cantidad de comida en el mapa en todo momento
FOOD_RADIUS = 6
FOOD_GLOW_SPEED = 2.0    # ciclos por segundo

# IA
AI_SIGHT_RADIUS = 250    # radio de visión de los bots
AI_DANGER_RADIUS = 150   # radio de peligro (evita colisiones)
AI_REACTION_TIME = 0.12  # segundos entre decisiones
BOT_COUNT_DEFAULT = 5    # bots cuando no hay multijugador humano

# Power-ups
POWERUP_SPAWN_INTERVAL = 8.0   # segundos
POWERUP_DURATION = 7.0         # segundos que dura el efecto
POWERUP_RADIUS = 12

# Colores — paleta principal
C_BG        = (8,  14,  28)
C_GRID      = (14, 22,  45)
C_WHITE     = (240, 240, 255)
C_BLACK     = (0,   0,   0)
C_HUD_BG    = (0,   0,   0,  160)

# Colores de jugadores (cuerpo, cabeza)
PLAYER_COLORS = [
    {"body": (50, 200, 100),  "head": (80,  255, 130),  "glow": (50, 200, 80,  60),  "name": "Verde"},
    {"body": (60, 140, 220),  "head": (100, 180, 255),  "glow": (60, 140, 220, 60),  "name": "Azul"},
    {"body": (220, 70,  70),  "head": (255, 110, 110),  "glow": (220, 70,  70,  60),  "name": "Rojo"},
    {"body": (200, 160, 30),  "head": (255, 210, 50),   "glow": (200, 160, 30, 60),  "name": "Amarillo"},
]

# Colores de bots (hasta 12 bots)
BOT_COLORS = [
    {"body": (160, 60,  200), "head": (200, 100, 255), "glow": (160, 60,  200, 50), "name": "Bot Púrpura"},
    {"body": (200, 110, 40),  "head": (255, 150, 80),  "glow": (200, 110, 40, 50),  "name": "Bot Naranja"},
    {"body": (40,  190, 190), "head": (80,  240, 240), "glow": (40,  190, 190, 50), "name": "Bot Cyan"},
    {"body": (210, 210, 80),  "head": (255, 255, 130), "glow": (210, 210, 80, 50),  "name": "Bot Lima"},
    {"body": (190, 60,  120), "head": (240, 100, 160), "glow": (190, 60,  120, 50), "name": "Bot Rosa"},
    {"body": (80,  130, 200), "head": (120, 170, 240), "glow": (80,  130, 200, 50), "name": "Bot Celeste"},
    {"body": (120, 200, 60),  "head": (160, 240, 100), "glow": (120, 200, 60, 50),  "name": "Bot Menta"},
    {"body": (200, 80,  80),  "head": (240, 120, 120), "glow": (200, 80,  80, 50),  "name": "Bot Coral"},
    {"body": (100, 100, 200), "head": (140, 140, 240), "glow": (100, 100, 200, 50), "name": "Bot Índigo"},
    {"body": (180, 140, 60),  "head": (220, 180, 100), "glow": (180, 140, 60, 50),  "name": "Bot Ocre"},
    {"body": (60,  180, 140), "head": (100, 220, 180), "glow": (60,  180, 140, 50), "name": "Bot Esmeralda"},
    {"body": (170, 80,  170), "head": (210, 120, 210), "glow": (170, 80,  170, 50), "name": "Bot Magenta"},
]

# Tipos de power-up
PU_SPEED    = "speed"
PU_GHOST    = "ghost"
PU_MAGNET   = "magnet"
PU_SHIELD   = "shield"
PU_DOUBLE   = "double"

POWERUP_COLORS = {
    PU_SPEED:   (255, 220, 50),
    PU_GHOST:   (180, 180, 255),
    PU_MAGNET:  (255, 120, 200),
    PU_SHIELD:  (80,  220, 255),
    PU_DOUBLE:  (255, 160, 60),
}

POWERUP_ICONS = {
    PU_SPEED:  "⚡",
    PU_GHOST:  "👻",
    PU_MAGNET: "🧲",
    PU_SHIELD: "🛡",
    PU_DOUBLE: "×2",
}

# Teclas (jugadores humanos)
# Usamos los valores enteros directamente para no depender de pygame aquí.
# Equivalencias: w=119, s=115, a=97, d=100, LSHIFT=304, RSHIFT=303
# UP=273, DOWN=274, LEFT=276, RIGHT=275
# i=105, k=107, j=106, l=108, u=117
# KP8=264, KP5=261, KP4=260, KP6=262, KP0=256
PLAYER_KEYS = [
    # Jugador 1: WASD
    {
        "up":    119,   # K_w
        "down":  115,   # K_s
        "left":  97,    # K_a
        "right": 100,   # K_d
        "boost": 304,   # K_LSHIFT
    },
    # Jugador 2: Flechas
    {
        "up":    273,   # K_UP
        "down":  274,   # K_DOWN
        "left":  276,   # K_LEFT
        "right": 275,   # K_RIGHT
        "boost": 303,   # K_RSHIFT
    },
    # Jugador 3: IJKL
    {
        "up":    105,   # K_i
        "down":  107,   # K_k
        "left":  106,   # K_j
        "right": 108,   # K_l
        "boost": 117,   # K_u
    },
    # Jugador 4: Numpad
    {
        "up":    264,   # K_KP8
        "down":  261,   # K_KP5
        "left":  260,   # K_KP4
        "right": 262,   # K_KP6
        "boost": 256,   # K_KP0
    },
]