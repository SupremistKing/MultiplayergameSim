import socket
import threading
import json
import time
import random

HOST = "127.0.0.1"
PORT = 5000
PLAYER_NAME = "Player 1"

SYNC_INTERVAL = 3.0
LAT_MIN = 0.05
LAT_MAX = 0.5


class LocalClock:
    def __init__(self):
        self.t = 0.0
        self.offset = 0.0
        self.lock = threading.Lock()
        self.running = True

    def start(self):
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        while self.running:
            drift = random.uniform(-0.01, 0.01)
            tick = 0.05 + drift
            with self.lock:
                self.t += tick
            time.sleep(0.05)

    def now(self):
        with self.lock:
            return self.t + self.offset

    def adjust(self, d):
        with self.lock:
            self.offset += d

    def stop(self):
        self.running = False


clock = LocalClock()


def send(sock, obj):
    msg = json.dumps(obj) + "\n"
    sock.sendall(msg.encode())


def receiver(sock):
    buf = ""
    last_t0 = None

    def sync_req():
        nonlocal last_t0
        last_t0 = clock.now()
        send(sock, {"type": "TIME_REQUEST"})

    sync_req()
    last_sync = time.time()

    while True:
        if time.time() - last_sync >= SYNC_INTERVAL:
            last_sync = time.time()
            try:
                sync_req()
            except OSError:
                break

        try:
            sock.settimeout(0.1)
            data = sock.recv(1024)
        except socket.timeout:
            continue
        except OSError:
            break

        if not data:
            break

        buf += data.decode()
        while "\n" in buf:
            line, buf = buf.split("\n", 1)
            if not line.strip():
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue

            mtype = msg.get("type")

            if mtype == "WELCOME":
                print(f"[{PLAYER_NAME}] Connected as Player {msg.get('player_id')}")

            elif mtype == "TIME_RESPONSE":
                t_server = msg.get("server_time")
                if t_server is None or last_t0 is None:
                    continue
                t1 = clock.now()
                rtt = t1 - last_t0
                est_time = t_server + rtt / 2.0
                delta = est_time - t1
                clock.adjust(delta)
                print(f"[{PLAYER_NAME}] Clock sync Δ={delta:.4f} RTT={rtt:.4f}")

            elif mtype == "ACTION_BROADCAST":
                pid = msg.get("player_id")
                action = msg.get("action")
                ts = msg.get("timestamp")
                print(f"[{PLAYER_NAME}] ACTION: Player {pid} -> {action} (ts={ts:.4f})")

    print(f"[{PLAYER_NAME}] Disconnected")


def sender(sock):
    print(f"[{PLAYER_NAME}] Enter actions (move, shoot, pickup). Type 'quit' to exit.")
    while True:
        action = input(f"{PLAYER_NAME}> ").strip()
        if action.lower() == "quit":
            break
        if not action:
            continue

        time.sleep(random.uniform(LAT_MIN, LAT_MAX))

        msg = {
            "type": "ACTION",
            "action": action,
            "timestamp": clock.now()
        }
        try:
            send(sock, msg)
        except OSError:
            break

    print(f"[{PLAYER_NAME}] Exiting...")
    try:
        sock.close()
    except OSError:
        pass


def main():
    clock.start()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    threading.Thread(target=receiver, args=(sock,), daemon=True).start()
    sender(sock)

    clock.stop()


if __name__ == "__main__":
    main()
