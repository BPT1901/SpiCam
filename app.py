from flask import Flask, Response, render_template_string
import subprocess
import os
import signal
import atexit
import time
import socket
import threading

frame_buffer = None
frame_lock = threading.Lock()


app = Flask(__name__)
PIPE_PATH = "/tmp/vidstream.mjpg"
libcamera_process = None

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>SPiCam Live Stream</title>
    <style>
        body {
            background-color: black;
            color: #ff6ec7;
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
        }
        h1 {
            margin-bottom: 10px;
            color: #ff6ec7;
        }
        .stream-container {
            border: 1px solid #ff6ec7;
        }
    </style>
    <script>
        function updateTime() {
            const now = new Date().toLocaleTimeString('en-AU', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                timeZone: 'Australia/Sydney',
                hour12: false
            });
            document.getElementById("current-time").textContent = now + " AEDT";
        }
        setInterval(updateTime, 1000);
        window.onload = updateTime;
    </script>
</head>
<body>
    <h1>Live Stream – <span id="current-time">...</span></h1>
    <div class="stream-container">
        <img src="{{ url_for('video_feed') }}" width="640" height="360">
    </div>
</body>
</html>
"""



def build_command():
    return [
        "libcamera-vid",
        "-t", "0",
        "--inline",
        "--width", "640",
        "--height", "480",
        "--codec", "mjpeg",
        "-o", PIPE_PATH,
        "--brightness", "0.0",
        "--contrast", "0.9",
        "--saturation", "2.0",
        "--sharpness", "1.5",
        "--gain", "1.0"
    ]

def start_libcamera_stream():
    global libcamera_process
    if os.path.exists(PIPE_PATH):
        os.remove(PIPE_PATH)
    os.mkfifo(PIPE_PATH)
    libcamera_process = subprocess.Popen(build_command())

def stop_libcamera_stream():
    global libcamera_process
    if libcamera_process:
        libcamera_process.send_signal(signal.SIGINT)
        try:
            libcamera_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            libcamera_process.kill()
        libcamera_process = None

atexit.register(stop_libcamera_stream)

def mjpeg_stream_reader():
    global frame_buffer
    buffer = b""

    while True:
        try:
            with socket.create_connection(("127.0.0.1", 8888)) as sock:
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    buffer += chunk
                    while True:
                        start = buffer.find(b'\xff\xd8')
                        end = buffer.find(b'\xff\xd9')
                        if start != -1 and end != -1 and end > start:
                            with frame_lock:
                                frame_buffer = buffer[start:end+2]
                            buffer = buffer[end+2:]
                        else:
                            break
        except (ConnectionRefusedError, OSError):
            time.sleep(1)


@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

def generate_mjpeg():
    while True:
        with frame_lock:
            frame = frame_buffer
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.03)  # ~33 FPS


@app.route('/video_feed')
def video_feed():
    return Response(generate_mjpeg(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    threading.Thread(target=mjpeg_stream_reader, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=False)