"""
Cliente de red para multijugador LAN.
"""

import socket
import threading
import json


class GameClient:
    """
    Se conecta al servidor y recibe el estado del juego en tiempo real.
    También envía el input local al servidor.
    """

    def __init__(self, host: str, port: int = 5555):
        self.host = host
        self.port = port
        self._sock: socket.socket | None = None
        self._running = False
        self._lock = threading.Lock()
        self._latest_state: dict | None = None
        self._connected = False

    def connect(self) -> bool:
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(5.0)
            self._sock.connect((self.host, self.port))
            self._sock.settimeout(None)
            self._running = True
            self._connected = True
            t = threading.Thread(target=self._recv_loop, daemon=True)
            t.start()
            print(f"[Client] Conectado a {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"[Client] Error de conexión: {e}")
            self._connected = False
            return False

    def disconnect(self):
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
        print("[Client] Desconectado.")

    def poll_state(self) -> dict | None:
        with self._lock:
            s = self._latest_state
            self._latest_state = None
            return s

    def send_input(self, angle: float, boosting: bool):
        if not self._connected or not self._sock:
            return
        msg = json.dumps({"type": "input", "angle": angle, "boost": boosting}) + "\n"
        try:
            self._sock.sendall(msg.encode())
        except Exception:
            self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def _recv_loop(self):
        buf = ""
        while self._running:
            try:
                data = self._sock.recv(4096).decode(errors="ignore")
                if not data:
                    break
                buf += data
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    try:
                        state = json.loads(line)
                        with self._lock:
                            self._latest_state = state
                    except json.JSONDecodeError:
                        pass
            except Exception:
                break
        self._connected = False
        print("[Client] Conexión perdida.")