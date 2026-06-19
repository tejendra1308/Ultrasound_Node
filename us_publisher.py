#!/usr/bin/env python3

import socket
import struct
import time

import cv2
import numpy as np

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

ROS_TOPIC = "/ultrasound/image_raw"


def read_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Windows server closed connection.")
        buf += chunk
    return buf


def connect_to_windows(ip, port):
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port))
            print(f"[Publisher] Connected to Windows server at {ip}:{port}")
            return s
        except OSError as e:
            print(f"[Publisher] Cannot reach {ip}:{port} — retrying... ({e})")
            time.sleep(2)


class UltrasoundPublisher(Node):

    def __init__(self):
        super().__init__("ultrasound_publisher")

        self.declare_parameter("pc_ip", "172.18.17.234")
        self.declare_parameter("port", 5000)

        pc_ip = self.get_parameter("pc_ip").get_parameter_value().string_value
        port = self.get_parameter("port").get_parameter_value().integer_value

        self._bridge = CvBridge()
        self._pub = self.create_publisher(Image, ROS_TOPIC, 10)

        self.get_logger().info(
            f"Connecting to Windows server at {pc_ip}:{port}"
        )

        self._sock = connect_to_windows(pc_ip, port)
        self._timer = self.create_timer(0.001, self.receive_frame)

    def receive_frame(self):
        try:
            header = read_exact(self._sock, 4)
            size = struct.unpack(">I", header)[0]

            if size <= 0 or size > 10000000:
                return

            jpeg_bytes = read_exact(self._sock, size)

            frame = cv2.imdecode(
                np.frombuffer(jpeg_bytes, dtype=np.uint8),
                cv2.IMREAD_COLOR
            )

            if frame is None:
                return

            msg = self._bridge.cv2_to_imgmsg(frame, encoding="bgr8")
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = "ultrasound_camera"

            self._pub.publish(msg)

        except ConnectionError as e:
            self.get_logger().error(f"Connection lost: {e}")
        except Exception as e:
            self.get_logger().error(f"Stream error: {e}")


def main():
    rclpy.init()
    node = UltrasoundPublisher()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
