"""
Multicast service discovery broadcaster.

Kept dependency-free and copy-paste portable on purpose — sibling projects
(e.g. a CT node) may vendor this exact file. The public function API
(`start_broadcaster`) is unchanged from the original shared_discovery.py so
nothing else needs to change if you copy this file elsewhere.
"""

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


class ServiceBroadcaster:
    def __init__(self, service_name, ports: dict, multicast_group="239.255.42.42",
                 broadcast_port=5003, interval=2.0):
        self.service_name = service_name
        self.ports = ports
        self.multicast_group = multicast_group
        self.broadcast_port = broadcast_port
        self.interval = interval
        self._thread = None

    def start(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

        local_ip = get_local_ip()
        # Force multicast out through the adapter with the real LAN IP —
        # otherwise Windows may pick Ethernet/VPN/virtual adapters instead of WiFi.
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(local_ip))

        message = json.dumps({
            "service": self.service_name,
            "ip": local_ip,
            "ports": self.ports,
        }).encode("utf-8")

        def loop():
            while True:
                try:
                    sock.sendto(message, (self.multicast_group, self.broadcast_port))
                except Exception as e:
                    print(f"  [UDP] Multicast error: {e}")
                time.sleep(self.interval)

        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()
        print(f"  [Multicast] Broadcasting '{self.service_name}' from {local_ip} "
              f"-> {self.multicast_group}:{self.broadcast_port}")
        return self._thread


def start_broadcaster(service_name, ports: dict, broadcast_port=5003, interval=2.0,
                       multicast_group="239.255.42.42"):
    """Backward-compatible function API matching the original shared_discovery.py."""
    return ServiceBroadcaster(
        service_name, ports, multicast_group, broadcast_port, interval
    ).start()
