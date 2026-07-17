"""
MicrUs Ultrasound -> Quest 3 streaming server.

Just wiring: WindowCapture (grabs frames) -> VideoStreamServer (sends them)
-> ServiceBroadcaster (lets Unity find us). All the actual logic lives in
core/. All the tunable numbers live in config/.
"""

from config.settings import SETTINGS
from core.window_capture import WindowCapture
from core.video_stream import VideoStreamServer
from core.discovery import ServiceBroadcaster


def main():
    print("=" * 50)
    print("   MicrUs Ultrasound -> Quest 3 Streaming Server")
    print("=" * 50)

    cfg = SETTINGS
    print(f"\nOutput : {cfg.video.output_width}x{cfg.video.output_height} "
          f"@ {cfg.video.fps}FPS  JPEG={cfg.video.jpeg_quality}")

    print("\nLooking for target window...")
    capture = WindowCapture(
        title_hint=cfg.window.title_hint,
        crop=(cfg.window.crop_left, cfg.window.crop_right,
              cfg.window.crop_top, cfg.window.crop_bottom),
        output_size=(cfg.video.output_width, cfg.video.output_height),
    )
    capture.find()

    print(f"\nPort : {cfg.video.port}")

    if cfg.discovery.enabled:
        ServiceBroadcaster(
            service_name=cfg.discovery.service_name,
            ports={"video": cfg.video.port, "control": cfg.command.port},
            multicast_group=cfg.discovery.multicast_group,
            broadcast_port=cfg.discovery.broadcast_port,
            interval=cfg.discovery.interval_seconds,
        ).start()

    print("Make sure the receiving device is on the same network.\n")

    server = VideoStreamServer(
        frame_provider=capture.capture,
        is_source_alive=capture.is_valid,
        port=cfg.video.port,
        fps=cfg.video.fps,
        jpeg_quality=cfg.video.jpeg_quality,
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
