from flask import Flask, Response, send_file
import cv2
import glob
import os

class CameraServer:
    def __init__(self, camera_module, host='0.0.0.0', port=8000):
        self.camera = camera_module
        self.host = host
        self.port = port
        self.app = Flask(__name__)

        @self.app.route('/')
        def index():
            return '''
            <h2>Camera Server Running</h2>
            <p> Live Stream: <a href="/video">/video</a></p>
            <p> Latest Photo: <a href="/latest">/latest</a></p>
            '''

        # Add routes
        self.app.add_url_rule('/video', 'video', self._video_feed)
        self.app.add_url_rule('/latest', 'latest', self._latest_photo)

        print(f"Flask server initialized on port {self.port}")

    def _generate_frames(self):
        """Generate frames for MJPEG video streaming."""
        while True:
            frame = self.camera.capture_frame()
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    def _video_feed(self):
        """Return live video stream."""
        return Response(
            self._generate_frames(),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )

    def _latest_photo(self):
        """Serve the most recently captured photo."""
        files = sorted(glob.glob('captured_images/*.jpg'))
        if files:
            return send_file(files[-1], mimetype='image/jpeg')
        else:
            return "No photo captured yet."

    def start(self):
        print(f"Streaming live at: http://{self.host}:{self.port}/video")
        self.app.run(host=self.host, port=self.port, debug=False, threaded=True)
