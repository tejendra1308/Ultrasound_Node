"""
Dual Publisher — ROS 2 + Unity TCP  (Ubuntu / Linux)
=====================================================
Connects to the Windows TCP server (pc_server.py) as a CLIENT,
reads JPEG frames, then simultaneously:
  1. Publishes sensor_msgs/Image on /ultrasound/image_raw  (ROS 2)
  2. Streams JPEG frames over TCP to Unity Quest 3

This script runs on Ubuntu. The Windows pc_server.py is unchanged.

Dependencies:
    pip3 install opencv-python "numpy<2" --user
    sudo apt install ros-humble-cv-bridge ros-humble-rclpy

Run:
    source /opt/ros/humble/setup.bash
    python3 dual_publisher.py --ros-args -p pc_ip:=<WINDOWS_IP> -p port:=5000

If running WSL2, get WINDOWS_IP with:
    cat /etc/resolv.conf | grep nameserver
"""

import socket
import struct
import threading

import cv2
import numpy as np

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge


# ── Config ────────────────────────────────────────────────────────────────────
ROS_TOPIC    = "/ultrasound/image_raw"
UNITY_PORT   = 5001          # Unity listens on this port (different from Windows server)
JPEG_QUALITY = 90
# ─────────────────────────────────────────────────────────────────────────────


# ── TCP frame reader (reads from Windows pc_server.py) ───────────────────────

def read_exact(sock, n):
    """Read exactly n bytes from socket."""
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Windows server closed connection.")
        buf += chunk
    return buf


def connect_to_windows(ip, port):
    """Keep retrying until Windows server is reachable."""
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port))
            print(f"[dual_publisher] Connected to Windows server at {ip}:{port}")
            return s
        except OSError as e:
            print(f"[dual_publisher] Cannot reach {ip}:{port} — retrying... ({e})")
            import time; time.sleep(2)


# ── Unity TCP streamer (pushes to Quest 3) ───────────────────────────────────

class UnityStreamer:
    """
    Accepts one Unity client at a time on UNITY_PORT.
    Call push(jpeg_bytes) to forward the raw JPEG to Unity.
    Protocol matches CameraFeedReceiver.cs: 4-byte big-endian size + JPEG data.
    """

    def __init__(self, port):
        self._port = port
        self._lock = threading.Lock()
        self._conn = None
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _accept_loop(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", self._port))
        server.listen(1)
        print(f"[UnityStreamer] Listening on TCP :{self._port} — waiting for Quest 3")
        while True:
            conn, addr = server.accept()
            print(f"[UnityStreamer] Quest 3 connected from {addr}")
            with self._lock:
                if self._conn:
                    try: self._conn.close()
                    except OSError: pass
                self._conn = conn

    def push(self, jpeg_bytes):
        """Forward raw JPEG bytes to Unity with 4-byte header."""
        with self._lock:
            conn = self._conn
        if conn is None:
            return
        header = struct.pack(">I", len(jpeg_bytes))
        try:
            conn.sendall(header + jpeg_bytes)
        except OSError:
            print("[UnityStreamer] Quest 3 disconnected.")
            with self._lock:
                self._conn = None


# ── ROS 2 node ────────────────────────────────────────────────────────────────

class DualPublisher(Node):
    def __init__(self):
        super().__init__("dual_publisher")

        # ROS 2 parameters — set via --ros-args -p pc_ip:=X.X.X.X
        self.declare_parameter("pc_ip",  "172.28.16.1")   # WSL2 default gateway
        self.declare_parameter("port",   5000)

        pc_ip = self.get_parameter("pc_ip").get_parameter_value().string_value
        port  = self.get_parameter("port").get_parameter_value().integer_value

        self._bridge  = CvBridge()
        self._unity   = UnityStreamer(port=UNITY_PORT)
        self._pub     = self.create_publisher(Image, ROS_TOPIC, qos_profile=10)

        self.get_logger().info(
            f"Connecting to Windows server at {pc_ip}:{port}\n"
            f"  ROS 2  -> {ROS_TOPIC}\n"
            f"  Unity  -> TCP :{UNITY_PORT}"
        )

        # Connect to Windows server and start receive thread
        self._win_sock = connect_to_windows(pc_ip, port)
        self._recv_thread = threading.Thread(
            target=self._receive_loop, daemon=True
        )
        self._recv_thread.start()

    def _receive_loop(self):
        """
        Runs in background thread.
        Reads JPEG frames from Windows TCP server and dispatches them.
        """
        while rclpy.ok():
            try:
                # 1. Read 4-byte big-endian frame size (matches pc_server.py)
                header = read_exact(self._win_sock, 4)
                size   = struct.unpack(">I", header)[0]

                if size <= 0 or size > 10_000_000:
                    self.get_logger().warn(f"Bad frame size {size}, skipping.")
                    continue

                # 2. Read full JPEG
                jpeg_bytes = read_exact(self._win_sock, size)

            except ConnectionError as e:
                self.get_logger().error(f"Windows server disconnected: {e}")
                break

            # 3. Decode JPEG → BGR numpy array
            frame = cv2.imdecode(
                np.frombuffer(jpeg_bytes, dtype=np.uint8),
                cv2.IMREAD_COLOR
            )
            if frame is None:
                continue

            # 4. Publish to ROS 2
            msg = self._bridge.cv2_to_imgmsg(frame, encoding="bgr8")
            msg.header.stamp    = self.get_clock().now().to_msg()
            msg.header.frame_id = "ultrasound_camera"
            self._pub.publish(msg)

            # 5. Forward raw JPEG to Unity (no re-encode needed)
            self._unity.push(jpeg_bytes)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    rclpy.init()
    node = DualPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

