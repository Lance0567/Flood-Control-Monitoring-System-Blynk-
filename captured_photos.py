#!/home/jesse/blynk_env/bin/python
from flask import Flask, render_template_string, send_from_directory
from picamera2 import Picamera2
from pyngrok import ngrok
import os
from datetime import datetime

app = Flask(__name__)

# Start Ngrok tunnel
public_url = ngrok.connect(5000)
print(f"?? Public Photo Gallery URL: {public_url.public_url}/photos")

photo_folder = "/home/jesse/Documents/photos"
os.makedirs(photo_folder, exist_ok=True)
picam2 = Picamera2()

@app.route('/capture')
def capture_photo():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    photo_path = os.path.join(photo_folder, f"photo_{timestamp}.jpg")
    picam2.start()
    picam2.capture_file(photo_path)
    picam2.stop()
    return f"Captured photo saved as {photo_path}"

@app.route('/photos')
def show_photos():
    files = sorted(os.listdir(photo_folder), reverse=True)
    html = """
    <html>
        <head>
            <title>?? Captured Photos</title>
            <style>
                body { background:#111; color:white; font-family:Arial; text-align:center; }
                img { width:45%; margin:10px; border-radius:10px; box-shadow:0 0 10px #000; }
                .date { font-size:18px; margin-top:5px; color:#aaa; }
                .photo-container { display:inline-block; margin:20px; }
            </style>
        </head>
        <body>
            <h2>?? Captured Photos</h2>
            {% for file in files %}
                <div class="photo-container">
                    <img src="/photo/{{ file }}" alt="photo">
                    <div class="date">{{ file[6:-4] }}</div>
                </div>
            {% endfor %}
        </body>
    </html>
    """
    return render_template_string(html, files=files)

@app.route('/photo/<filename>')
def photo(filename):
    return send_from_directory(photo_folder, filename)

if __name__ == '__main__':
    print("?? Local URL: http://192.168.1.120:5000/photos")
    app.run(host='0.0.0.0', port=5000)
