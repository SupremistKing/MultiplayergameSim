import socket
import threading
import json
import time

HOST = "127.0.0.1"
PORT = 5000

clients = {}
clients_lock = threading.Lock()

action_queue = []
queue_lock = threading.Lock()


def send_json(sock, obj):
    try:
        msg = json.dumps(obj) + "\n"
        sock.sendall(msg.encode())
    except OSError:
        pass


def broadcast(obj):
    with clients_lock:
        for sock in clients.values():
            send_json(sock, obj)


def handle_client(sock, addr, player_id):
    print(f"[SERVER] Player {player_id} connected")
    send_json(sock, {"type": "WELCOME", "player_id": player_id})

    buffer = ""
    while True:
        try:
            data = sock.recv(1024)
        except OSError:
            break
        if not data:
            break

        buffer += data.decode()
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            if not line.strip():
                continue

            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")

            if msg_type == "TIME_REQUEST":
                send_json(sock, {
                    "type": "TIME_RESPONSE",
                    "server_time": time.time()
                })

            elif msg_type == "ACTION":
                action = msg.get("action")
                ts = msg.get("timestamp")
                if action is None or ts is None:
                    continue
                with queue_lock:
                    action_queue.append({
                        "player_id": player_id,
                        "action": action,
                        "timestamp": ts,
                        "server_receive_time": time.time()
                    })

    print(f"[SERVER] Player {player_id} disconnected")
    sock.close()


def broadcaster():
    while True:
        time.sleep(0.1)
        to_send = []
        with queue_lock:
            if action_queue:
                action_queue.sort(
                    key=lambda a: (a["timestamp"], a["server_receive_time"])
                )
                to_send = action_queue[:]
                action_queue.clear()

        for act in to_send:
            broadcast({
                "type": "ACTION_BROADCAST",
                "player_id": act["player_id"],
                "action": act["action"],
                "timestamp": act["timestamp"]
            })


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(2)
    print(f"[SERVER] Listening on {HOST}:{PORT}")

    threading.Thread(target=broadcaster, daemon=True).start()

    player_id = 1
    while player_id <= 2:
        sock, addr = server.accept()
        with clients_lock:
            clients[player_id] = sock

        threading.Thread(
            target=handle_client,
            args=(sock, addr, player_id),
            daemon=True
        ).start()

        player_id += 1

    print("[SERVER] Two players connected. Server is running.")

    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
