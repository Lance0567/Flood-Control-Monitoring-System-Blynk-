#!/home/jesse/blynk_env/bin/python
from flask import Flask, Response
from picamera2 import Picamera2
from pyngrok import ngrok
import cv2
import os

app = Flask(__name__)

# Start Ngrok tunnel
public_url = ngrok.connect(5000)
print(f"?? Public Live Stream URL: {public_url.public_url}/video")

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"size": (640, 480)}))
picam2.start()

def generate_frames():
    while True:
        frame = picam2.capture_array()
        _, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/video')
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print("?? Local URL: http://192.168.1.120:5000/video")
    app.run(host='0.0.0.0', port=5000)
