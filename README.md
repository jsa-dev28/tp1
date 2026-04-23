# Slither.io — Pygame

Mi proyecto consiste en una versión del juego Slither.io usando la librería Pygame. El proyecto incluye gran parte de las funciones del juego original, agregando funciones nuevas como pantalla dividida, habilidades especiales (power-ups), IA para los bots y generación de sonidos.

## Descripción general

El juego consiste en controlar una serpiente dentro de un mapa de 3000x3000 píxeles. El objetivo es crecer lo máximo posible comiendo pelotitas de comida dispersas por el mundo, evitando chocar contra el cuerpo de otras serpientes. Cuando una serpiente muere, suelta toda su comida acumulada en el mapa, que puede ser recogida por los demás jugadores.
La partida termina cuando todos los jugadores humanos mueren, o cuando queda una sola serpiente viva en el mapa.

## Modos de juego

El juego ofrece tres modos de juego seleccionables:

**Solo vs IA**
Un jugador humano contra bots controlados por inteligencia artificial. Se puede configurar la cantidad de bots entre 0 y 12.

**Cooperativo**
Hasta 4 jugadores humanos comparten una partida contra bots de IA. Cada jugador tiene su propio viewport en una pantalla dividida.

**Versus**
Hasta 4 jugadores humanos compiten entre ellos sin bots. También usa pantalla dividida.

## Configuración de jugadores

Antes de iniciar una partida, cada jugador puede personalizar:

- **Nombre** — Campo de texto editable, Se hace clic sobre el campo y se escribe directamente. Aparece en pantalla durante el juego.
- **Color de la serpiente** — Se elige entre 10 opciones usando las flechas "<" y ">" que aparecen. El color afecta al cuerpo, la cabeza y las partículas de brillo.

## Mecánicas de juego

**Movimiento**
La serpiente gira continuamente en la dirección que se indique. No se puede detener. Cuando la serpiente sale por un borde del mundo, reaparece por el lado opuesto.

**Crecimiento**
Al comer una pelotita de comida, la serpiente aumenta su longitud y suma puntos. La comida grande (menos frecuente) vale el triple.

**Turbo**
Mantener presionada la tecla de turbo aumenta la velocidad en un 75%. A cambio, la serpiente pierde segmentos de cola gradualmente mientras lo usa. El turbo no puede usarse si la serpiente tiene una longitud demasiado corta.

**Muerte**
Una serpiente muere si su cabeza choca contra el cuerpo de otra. Al morir, suelta comida a lo largo de su cuerpo, que puede ser recogida por los demás jugadores. El jugador que provoca la muerte recibe puntos de bonificación proporcionales a la longitud de la víctima.

## Power-ups

Aparecen en el mapa cada algunos segundos en forma de hexágonos giratorios. Al pasar encima se recogen automáticamente y duran 7 segundos.

- **Velocidad** - Aumenta la velocidad base en un 50%
- **Fantasma** - Permite atravesar el cuerpo de otras serpientes sin morir
- **Imán** - Atrae la comida cercana hacia la cabeza automáticamente
- **Escudo** - Absorbe un golpe fatal. Al activarse, otorga 1.5 segundos de invencibilidad para alejarse del peligro
- **Puntuación doble** - La comida y los kills valen el doble de puntos y longitud

Los power-ups activos se muestran en la parte inferior del pantalla de cada jugador con su nombre, ícono y una barra de tiempo restante. Cuando quedan menos de 2 segundos parpadean como advertencia.

## Inteligencia artificial

Los bots reciben un nivel de dificultad aleatorio entre 0.8 y 1.6 al inicio de cada partida, que afecta la velocidad de sus decisiones y la precisión de sus giros.

Cada bot toma decisiones según un árbol de prioridades:

1. **Huir** — Si detecta una serpiente más grande o un segmento corporal dentro de su radio de peligro (150 px), gira en dirección opuesta con una variación aleatoria para no ser predecible.
2. **Cazar power-ups** — Si hay un power-up dentro de su radio de visión (200 px), se dirige hacia él.
3. **Buscar comida** — Si hay comida dentro de su radio de visión (250 px), se dirige hacia la más cercana.
4. **Deambular** — Si no hay ningún objetivo cercano, elige un punto aleatorio del mapa y se mueve hacia él. Cambia de destino cada 3 a 8 segundos.

## Pantalla dividida

En partidas con más de un jugador humano, la pantalla se divide automáticamente:

- **2 jugadores** — División vertical. Cada jugador ocupa la mitad izquierda o derecha.
- **3 jugadores** — Los dos primeros ocupan la mitad superior dividida verticalmente, el tercero ocupa todo el ancho de la mitad inferior.
- **4 jugadores** — Cuadrícula de 2x2.

Cada viewport tiene su propia cámara que sigue a su jugador de forma independiente, y su propio HUD mínimo con score, longitud y kills.

## HUD e interfaz

**Por viewport (cada jugador):**
- Score, longitud y kills en la esquina inferior izquierda
- Barra de power-ups activos centrada en la parte inferior
- Indicador "TURBO" cuando el boost está activo
- Nombre del jugador en la esquina superior izquierda

**Compartido (sobre toda la pantalla):**
- Leaderboard en tiempo real en la esquina superior derecha, con hasta 10 posiciones
- Minimapa en la esquina inferior derecha que muestra todo el mundo, incluyendo serpientes, comida, power-ups y el área visible de cada cámara
- Kill feed con las últimas eliminaciones, que se desvanece con el tiempo
- Advertencia visual (borde rojo pulsante) al acercarse al límite del mundo

## Efectos visuales y sonido

El juego genera todos sus sonidos matemáticamente al iniciar, sin depender de archivos de audio externos. Esto permite que funcione en cualquier entorno que tenga pygame instalado. Hay efectos para comer, turbo, muerte, kill, recoger power-ups, escudo absorbiendo un golpe y la cuenta regresiva inicial.

Los efectos visuales incluyen un sistema de partículas para explosiones de muerte, estela de turbo, destellos al comer y al recoger ítems. Cada segmento del cuerpo tiene partículas de brillo animado, y la comida pulsa con una fase aleatoria para que no todas lo hagan al mismo tiempo.

## Parámetros configurables

Todos los valores del juego están centralizados en "game/constants.py". Los más relevantes para ajustar la experiencia son:

- **WORLD_W / WORLD_H** - Tamaño del mundo, por def. 3000 x 3000 
- **SPEED_BASE** - Velocidad normal, por def. 160 px/s 
- **SPEED_BOOST** - Velocidad con turbo, por def.  280 px/s 
- **BOOST_DRAIN** - Cola perdida por segundo de turbo, por def. 5 segmentos/s 
- **FOOD_COUNT_TARGET** - Comida máxima en el mapa, por def.  250 
- **POWERUP_SPAWN_INTERVAL** - Segundos entre power-ups, por def.  8 s 
- **POWERUP_DURATION** - Duración de los efectos, por def.  7 s 
- **AI_SIGHT_RADIUS** -  Radio de visión de los bots, por def.  250 px 
- **AI_DANGER_RADIUS** - Radio de peligro de los bots, por def.  150 px 

## Investigación

Investigué principalmente sobre cómo implementar efectos de sonido, los implementé usando la librería array, que viene instalada como librería estándar de Python, y genera todos los sonidos matemáticamente, para que no haga falta usar archivos de audio externos. También investigué sobre como dibujar una pantalla dividida, cómo hacer que una serpiente suelte comida cuando muera, o cómo simular el comportamiento de la IA. 