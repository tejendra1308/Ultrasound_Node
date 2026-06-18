# Ultrasound_Node

A ROS2-based real-time ultrasound streaming system that captures ultrasound images from the EchoWave-II application running on Windows and distributes them to multiple ROS2 subscribers over a network.

## Overview

This project enables real-time ultrasound image sharing between systems using TCP sockets and ROS2.

The system captures ultrasound frames from the EchoWave-II application, streams them through a TCP connection, publishes them as ROS2 image topics, and allows multiple ROS2 nodes to visualize the same ultrasound feed simultaneously.

---

## System Architecture

```text
EchoWave-II
     │
     ▼
Windows PC
(us_system.py)
     │
 TCP Socket
 Port: 5000
     │
     ▼
ROS2 Publisher
(us_publisher.py)
     │
     ▼
/ultrasound/image_raw
     │
 ┌───┼───────────────┐
 │   │               │
 ▼   ▼               ▼
Subscriber 1   Subscriber 2   Subscriber N
(image.py)     (image.py)     (image.py)
```

---

## Features

- Real-time ultrasound streaming
- ROS2 image publishing
- Multi-subscriber support
- TCP-based image transfer
- Cross-machine ROS2 communication
- Compatible with ROS2 Jazzy
- Suitable for AR/VR medical visualization pipelines

---

## Repository Structure

```text
Ultrasound_Node/
│
├── us_system.py
│   └── Captures ultrasound feed from EchoWave-II
│       and streams frames through TCP.
│
├── us_publisher.py
│   └── Receives TCP frames and publishes
│       them to ROS2 topic:
│       /ultrasound/image_raw
│
├── image.py
│   └── ROS2 subscriber used for visualizing
│       the incoming ultrasound stream.
│
└── README.md
```

---

## Requirements

### Operating Systems

- Windows 10/11
- Ubuntu 24.04 (ROS2 Jazzy)

### ROS2

- ROS2 Jazzy

### Python Packages

```bash
pip3 install opencv-python numpy
```

### ROS Packages

```bash
sudo apt update

sudo apt install -y \
ros-jazzy-rclpy \
ros-jazzy-cv-bridge \
ros-jazzy-sensor-msgs
```

---

## Running the System

### Step 1: Start Ultrasound Capture

On Windows:

```bash
python us_system.py
```

This creates a TCP server on:

```text
PORT 5000
```

---

### Step 2: Start ROS2 Publisher

On Ubuntu (ROS2 Jazzy):

```bash
source /opt/ros/jazzy/setup.bash

python3 us_publisher.py \
  --ros-args \
  -p pc_ip:=<WINDOWS_IP> \
  -p port:=5000
```

Example:

```bash
python3 us_publisher.py \
  --ros-args \
  -p pc_ip:=172.18.17.234 \
  -p port:=5000
```

---

### Step 3: Start Subscriber

```bash
source /opt/ros/jazzy/setup.bash

python3 image.py
```

---

## ROS Topic

Published Topic:

```text
/ultrasound/image_raw
```

Message Type:

```text
sensor_msgs/msg/Image
```

---

## Verifying Communication

Check available topics:

```bash
ros2 topic list
```

Check topic frequency:

```bash
ros2 topic hz /ultrasound/image_raw
```

Check topic bandwidth:

```bash
ros2 topic bw /ultrasound/image_raw
```

Check publisher/subscriber count:

```bash
ros2 topic info /ultrasound/image_raw
```

---

## Multi-System Streaming

Multiple ROS2 systems can subscribe to the same ultrasound stream.

Requirements:

- Same WiFi / LAN network
- Same ROS_DOMAIN_ID
- ROS2 discovery working correctly

Example:

```bash
export ROS_DOMAIN_ID=0
```

on all systems.

---

## Future Applications

- AR-guided ultrasound visualization
- Meta Quest 3 integration
- Medical training simulators
- Robotic ultrasound systems
- Telemedicine visualization

---

## Contributors

- Ayush Kumar
- Tejendra Vijayvargiya

---

## License

This project is intended for academic and research purposes.