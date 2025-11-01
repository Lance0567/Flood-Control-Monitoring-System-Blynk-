import threading
import subprocess
import time
import cv2
from flask import Flask, Response

live_app = Flask("live_server")

server_thread = None
ngrok_process = None
stop_event = threading.Event()

@live_app.route('/video')
def video_feed():
    from main import camera  # PATCH: You may pass camera as argument IF circular import occurs, do not use this, pass camera as below!
    def generate():
        while not stop_event.is_set():
            frame = camera.capture_array()
            _, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

def run_flask():
    live_app.run(host='0.0.0.0', port=80, debug=False, threaded=True)

def start_ngrok(port=80):
    global ngrok_process
    ngrok_process = subprocess.Popen(['ngrok', 'http', str(port)])
    time.sleep(2)
    print("ngrok tunnel started for /video.")

def stop_ngrok():
    global ngrok_process
    if ngrok_process:
        ngrok_process.terminate()
        ngrok_process = None
        print("ngrok tunnel stopped.")

def handle_start_live_stream(camera):
    global server_thread, stop_event
    stop_event.clear()

    # PATCH below: To give camera to Flask, you'll need to attach it
    def video_feed_override():
        def generate():
            while not stop_event.is_set():
                frame = camera.capture_array()
                _, buffer = cv2.imencode('.jpg', frame)
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
    live_app.view_functions['video_feed'] = video_feed_override

    if not server_thread or not server_thread.is_alive():
        server_thread = threading.Thread(target=run_flask)
        server_thread.daemon = True
        server_thread.start()
        start_ngrok(80)
    else:
        print("Live streaming server already running.")

def handle_stop_live_stream():
    stop_event.set()
    stop_ngrok()
    print("Live streaming stopped (Flask server may persist until manual stop).")
