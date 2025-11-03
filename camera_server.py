from flask import Flask, Response
import cv2

class CameraServer:
    def __init__(self, camera_module, host='0.0.0.0', port=8000):
        self.camera = camera_module
        self.host = host
        self.port = port
        self.app = Flask(__name__)

        @self.app.route('/')
        def index():
            return '<h2>Camera Server Running</h2><p>Go to <a href="/video">/video</a> to view live stream.</p>'

        self.app.add_url_rule('/video', 'video', self._video_feed)
        print(f"Flask server initialized on port {self.port}")

    def _generate_frames(self):
        while True:
            frame = self.camera.capture_array()  # Picamera2 frame
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    def _video_feed(self):
        return Response(self._generate_frames(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    def start(self):
        print(f"Streaming live at: http://{self.host}:{self.port}/video")
        self.app.run(host=self.host, port=self.port, debug=False, threaded=True)
