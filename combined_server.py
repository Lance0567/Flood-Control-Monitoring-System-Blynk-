from flask import Flask, Response, send_from_directory, jsonify, render_template_string
import os
import threading
import cv2
from devices.camera_module import PiCameraModule  # Import your custom camera wrapper


PHOTO_DIR = "/home/jesse/Documents/photos"
VIDEO_DIR = "/home/jesse/Documents/video"
app = Flask(__name__)
camera = None
server_thread = None
stream_running = False

def gen_frames():
    global camera
    while stream_running:
        frame = camera.capture_frame()  # Already (320, 240) for speed!
        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 45])
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/photo_list')
def photo_list():
    try:
        files = sorted(f for f in os.listdir(PHOTO_DIR) if f.lower().endswith('.jpg'))
        return jsonify(files)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/livecam')
def livecam():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    
@app.route('/photos')
def photos():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Flood Control Captured Photos</title>
    <link href="https://fonts.googleapis.com/css?family=Montserrat:700,400" rel="stylesheet">
    <style>
        body {
            background: #f5f6fa;
            color: #222831;
            font-family: 'Montserrat', Arial, sans-serif;
            text-align: center;
            margin: 0;
            padding: 0;
        }
        .gallery-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 98vh;
        }
        h2 {
            margin-bottom: 24px;
            font-weight: 700;
            letter-spacing: 0.03em;
        }
        .slide-img-box {
            position: relative;
            width: 600px;
            max-width: 90vw;
            margin-bottom: 12px;
        }
        #photo {
            width: 100%;
            max-height: 70vh;
            object-fit: contain;
            border-radius: 16px;
            box-shadow: 0 8px 24px rgba(44, 62, 80, 0.13), 0 1.5px 10px rgba(44,62,80,0.09);
            background: #e6e6e6;
            opacity: 0;
            transition: opacity 0.7s;
        }
        #photo.active {
            opacity: 1;
        }
        .gallery-controls {
            margin-bottom: 10px;
        }
        button {
            font-size: 1.4em;
            font-family: inherit;
            padding: 9px 40px;
            background: #3742fa;
            color: #fff;
            border: none;
            border-radius: 30px;
            margin: 0 18px;
            cursor: pointer;
            box-shadow: 0 3px 11px rgba(44, 62, 80, 0.09);
            outline: none;
            transition: background 0.2s;            
        }
        button:active {
            background: #5352ed;
        }
        #counter {
            font-size: 1.2em;
            color: #2e2e2e;
            margin-top: 12px;
            margin-bottom: 28px;
            letter-spacing: 0.02em;
        }
        .thumb-strip {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
        }
        .thumb {
            width: 56px;
            height: 38px;
            margin: 0 5px;
            object-fit: cover;
            border-radius: 7px;
            background: #d2dae2;
            box-shadow: 0 2px 8px rgba(44,62,80,0.06);
            cursor: pointer;
            opacity: 0.6;
            border: 2.5px solid #d2dae2;
            transition: opacity 0.3s, border 0.2s;
        }
        .thumb.selected {
            opacity: 1;
            border: 2.5px solid #3742fa;
        }
        @media (max-width: 800px) {
            .slide-img-box { width: 99vw; }
            #photo { max-height: 56vw; }
        }
    </style>
</head>
<body>
    <div class="gallery-container">
        <h2>Flood Control Photo Slideshow</h2>
        <div class="slide-img-box">
            <img id="photo" src="" alt="No Photo">
        </div>
        <div class="gallery-controls">
            <button id="prev">&lt; Previous</button>
            <button id="next">Next &gt;</button>
        </div>
        <div id="counter"></div>
        <div class="thumb-strip" id="thumbstrip"></div>
    </div>
<script>
let photos = [];
let idx = 0;

function preloadThumbnails(photoList) {
    let thumbBar = document.getElementById('thumbstrip');
    thumbBar.innerHTML = "";
    photoList.forEach((photo, i) => {
        let thumb = document.createElement('img');
        thumb.src = '/photos_img/' + photo;
        thumb.className = 'thumb';
        thumb.onclick = function() {
            idx = i;
            updatePhoto();
        };
        thumbBar.appendChild(thumb);
    });
}

function updatePhoto() {
    if (photos.length) {
        let img = document.getElementById('photo');
        img.classList.remove('active');
        // Preload large image, then fade in
        let temp = new window.Image();
        temp.onload = function() {
            img.src = temp.src;
            setTimeout(() => img.classList.add('active'), 10);
        }
        temp.src = '/photos_img/' + photos[idx];
        document.getElementById('counter').textContent = (idx + 1) + ' / ' + photos.length;
        // thumbnail highlights
        let thumbs = document.getElementsByClassName('thumb');
        for (let i=0; i<thumbs.length; i++) {
            thumbs[i].classList.toggle('selected', i === idx);
        }
    } else {
        document.getElementById('photo').src = '';
        document.getElementById('photo').classList.remove('active');
        document.getElementById('counter').textContent = 'No photos found';
    }
}

document.getElementById('prev').onclick = function() {
    if (photos.length) {
        idx = (idx - 1 + photos.length) % photos.length;
        updatePhoto();
    }
};
document.getElementById('next').onclick = function() {
    if (photos.length) {
        idx = (idx + 1) % photos.length;
        updatePhoto();
    }
};
fetch('/photo_list')
    .then(r => r.json())
    .then(list => {
        photos = list;
        idx = 0;
        preloadThumbnails(photos);
        updatePhoto();
    });
</script>
</body>
</html>
    ''')

@app.route('/photos_img/<filename>')
def photos_img(filename):
    return send_from_directory(PHOTO_DIR, filename)

def start_flask_server():
    global camera, stream_running
    if not stream_running:
        camera = PiCameraModule(width=640, height=480)
        print("Camera object:", camera)
        print("Has start method?", hasattr(camera, 'start'))
        camera.start()
        stream_running = True
        app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)

def stop_flask_server():
    global camera, stream_running
    stream_running = False
    if camera:
        try:
            camera.stop()
        except Exception as e:
            print(f"Error stopping camera: {e}")
        camera = None
    print("Flask server stopped.")