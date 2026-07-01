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


MULTICAST_GROUP = "239.255.42.42"  # fixed multicast address, same on all scripts

def start_broadcaster(service_name, ports: dict, broadcast_port=5003, interval=2.0):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

    local_ip = get_local_ip()
    message = json.dumps({
        "service": service_name,
        "ip": local_ip,
        "ports": ports
    }).encode("utf-8")

    def loop():
        while True:
            try:
                sock.sendto(message, (MULTICAST_GROUP, broadcast_port))
            except Exception as e:
                print(f"  [UDP] Multicast error: {e}")
            time.sleep(interval)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
    print(f"  [Multicast] Broadcasting '{service_name}' → {MULTICAST_GROUP}:{broadcast_port}")
    return thread