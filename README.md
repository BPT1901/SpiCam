# SpiCam Live Stream

This project turns a Raspberry Pi 4 with a Pi Camera into a low-latency, live MJPEG video stream accessible for example via a secure Cloudflare Tunnel.

Ideal for live monitoring in venues where direct line-of-sight is blocked, e.g. backstage video feeds during live events.

---

## Features

✅ Live MJPEG video stream  
✅ Very low latency (uses `libcamera-vid` and TCP streaming)  
✅ Accessible anywhere via Cloudflare Tunnel (no static IP needed)  
✅ Auto-starts on boot  
✅ Headless operation (no monitor or keyboard required)

---

## Hardware Requirements

- Raspberry Pi 4
- Pi Camera (compatible with libcamera)
- Ethernet or Wi-Fi internet connection

---

## Software Requirements

- Raspberry Pi OS Lite (64-bit recommended)
- Python 3
- Virtualenv (optional but recommended)
- Cloudflared (Cloudflare Tunnel client)

Python packages:

Install with:

`pip install flask`

## How It Works
- Video streaming:
  libcamera-vid captures MJPEG frames and sends them to a TCP socket.

- Flask app:
  Reads the MJPEG stream from the socket and serves it over HTTP.

- Cloudflare Tunnel:
  Exposes the Flask app securely to the internet via a custom domain
