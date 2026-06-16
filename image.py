"""
ROS 2 Image Subscriber
Subscribes to /ultrasound/image_raw and displays live feed with OpenCV.

Run:
    source /opt/ros/humble/setup.bash
    python3 image_subscriber.py
"""

import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge


TOPIC       = "/ultrasound/image_raw"
WINDOW_NAME = "Ultrasound Live Feed"


class ImageSubscriber(Node):
    def __init__(self):
        super().__init__("image_subscriber")
        self._bridge = CvBridge()
        self._sub = self.create_subscription(
            Image,
            TOPIC,
            self._frame_callback,
            qos_profile=10,
        )
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        self.get_logger().info(f"Subscribed to {TOPIC} — press Q to quit.")

    def _frame_callback(self, msg: Image):
        try:
            frame = self._bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except Exception as exc:
            self.get_logger().error(f"cv_bridge decode failed: {exc}")
            return

        cv2.imshow(WINDOW_NAME, frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            self.get_logger().info("Shutting down.")
            rclpy.shutdown()


def main():
    rclpy.init()
    node = ImageSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
