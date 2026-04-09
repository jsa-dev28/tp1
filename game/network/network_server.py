"""
Servidor de red para multijugador LAN.
Usa sockets TCP simples + JSON para comunicarse.
"""

import socket
import threading
import json
import time


class GameServer:
    """
    Servidor TCP que acepta hasta 4 clientes y difunde el estado del juego.
    Protocolo: líneas JSON terminadas en \\n.
    """

    def __init__(self, port: int = 5555):
        self.port = port
        self._sock: socket.socket | None = None
        self._clients: list[socket.socket] = []
        self._lock = threading.Lock()
        self._running = False
        self._state: dict = {}

    def start(self):
        self._running = True
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self._sock.bind(("0.0.0.0", self.port))
            self._sock.listen(4)
            self._sock.settimeout(1.0)
        except OSError as e:
            print(f"[Server] Error al iniciar: {e}")
            self._running = False
            return

        t = threading.Thread(target=self._accept_loop, daemon=True)
        t.start()
        print(f"[Server] Escuchando en puerto {self.port}")

    def stop(self):
        self._running = False
        with self._lock:
            for c in self._clients:
                try:
                    c.close()
                except Exception:
                    pass
            self._clients.clear()
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
        print("[Server] Detenido.")

    def broadcast_state(self, state: dict):
        self._state = state
        data = (json.dumps(state) + "\n").encode()
        with self._lock:
            dead = []
            for c in self._clients:
                try:
                    c.sendall(data)
                except Exception:
                    dead.append(c)
            for c in dead:
                self._clients.remove(c)

    def _accept_loop(self):
        while self._running:
            try:
                conn, addr = self._sock.accept()
                print(f"[Server] Cliente conectado: {addr}")
                with self._lock:
                    self._clients.append(conn)
                # Enviar bienvenida
                conn.sendall((json.dumps({"type": "welcome", "port": self.port}) + "\n").encode())
                # Hilo para recibir input del cliente
                t = threading.Thread(target=self._recv_client,
                                     args=(conn, addr), daemon=True)
                t.start()
            except socket.timeout:
                continue
            except Exception:
                break

    def _recv_client(self, conn: socket.socket, addr):
        buf = ""
        while self._running:
            try:
                data = conn.recv(1024).decode(errors="ignore")
                if not data:
                    break
                buf += data
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    try:
                        msg = json.loads(line)
                        self._handle_client_msg(msg, conn)
                    except json.JSONDecodeError:
                        pass
            except Exception:
                break
        print(f"[Server] Cliente desconectado: {addr}")
        with self._lock:
            if conn in self._clients:
                self._clients.remove(conn)
        try:
            conn.close()
        except Exception:
            pass

    def _handle_client_msg(self, msg: dict, conn: socket.socket):
        """Procesa mensajes de input de clientes (extensible)."""
        # Por ahora solo logueamos
        pass