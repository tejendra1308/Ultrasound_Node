import socket
import json
import threading
import time


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def start_broadcaster(service_name, ports: dict, broadcast_port=5003, interval=2.0):
    """
    Broadcast this PC's IP + relevant ports under a named service.
    ports: dict like {"video": 5000, "control": 5001}
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    local_ip = get_local_ip()
    message = json.dumps({
        "service": service_name,
        "ip": local_ip,
        "ports": ports
    }).encode("utf-8")

    def loop():
        while True:
            try:
                sock.sendto(message, ("255.255.255.255", broadcast_port))
            except Exception as e:
                print(f"  [UDP] Broadcast error: {e}")
            time.sleep(interval)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    print(f"  [UDP] Broadcasting '{service_name}' on port {broadcast_port} at {local_ip} {ports}")
    return thread