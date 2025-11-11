# combined_server.py - Flood Control
from flask import Flask, Response, send_from_directory, jsonify, render_template_string, request
import os, threading, cv2, time
import numpy as np
from devices.camera_module import PiCameraModule

PHOTO_DIR = "/home/jesse/Documents/photos"
VIDEO_DIR = "/home/jesse/Documents/video"
app = Flask(__name__)
camera_lock = threading.Lock()
camera = None
streaming_active = False

@app.route('/control_camera', methods=['POST'])
def control_camera():
    global camera, streaming_active
    action = request.json.get('action')
    
    if action == 'start':
        with camera_lock:
            if camera is None:
                try:
                    # Give camera time to be fully released if previously used
                    time.sleep(1)
                    camera = PiCameraModule(width=1000, height=640)
                    streaming_active = True
                    print("Camera started by API control.")
                    return 'Camera started.'
                except Exception as e:
                    print(f"Error starting camera: {e}")
                    camera = None
                    streaming_active = False
                    return f'Error starting camera: {e}', 500
            else:
                return 'Camera already running.'
                
    elif action == 'stop':
        with camera_lock:
            if camera is not None:
                streaming_active = False  # Signal streaming to stop first
                time.sleep(0.5)  # Give time for gen_frames to exit
                try:
                    camera.stop()
                    camera = None
                    print("Camera stopped by API control.")
                    return 'Camera stopped.'
                except Exception as e:
                    print(f"Error stopping camera: {e}")
                    camera = None
                    return f'Camera stopped with warning: {e}'
            else:
                streaming_active = False
                return 'Camera already stopped.'
    
    return 'Unknown action.'

def gen_frames():
    global camera, streaming_active
    
    print("gen_frames: Stream generator started")
    
    while streaming_active:
        try:
            with camera_lock:
                if camera is not None and streaming_active:
                    frame = camera.capture_frame()
                    _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 45])
                    frame_bytes = buffer.tobytes()
                else:
                    # Camera not available, send black frame
                    black_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    _, buffer = cv2.imencode('.jpg', black_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 45])
                    frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(0.03)  # ~30 fps
            
        except GeneratorExit:
            print("gen_frames: Client disconnected")
            break
        except Exception as e:
            print(f"Error in gen_frames: {e}")
            break
    
    print("gen_frames: Stream generator stopped")

@app.route('/livecam')
def livecam():
    """Live camera stream endpoint"""
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/photo_list')
def photo_list():
    try:
        files = sorted(f for f in os.listdir(PHOTO_DIR) if f.lower().endswith('.jpg'))
        return jsonify(files)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/photos')
def photos():
    # Grab 'level' parameter from query string, default to 'all'
    level = request.args.get('level', 'all')

    # Folder mapping
    folder_map = {
        'all': [
            PHOTO_DIR,
            os.path.join(PHOTO_DIR, 'yellow'),
            os.path.join(PHOTO_DIR, 'orange'),
            os.path.join(PHOTO_DIR, 'red'),
        ],
        'yellow': [os.path.join(PHOTO_DIR, 'yellow')],
        'orange': [os.path.join(PHOTO_DIR, 'orange')],
        'red': [os.path.join(PHOTO_DIR, 'red')],
    }
    selected_folders = folder_map.get(level, folder_map['all'])

    # Walk selected folders and collect photo filepaths (relative to /photos_img/)
    files = []
    for folder in selected_folders:
        if os.path.isdir(folder):
            for fname in sorted(os.listdir(folder)):
                if fname.lower().endswith('.jpg'):
                    rel_path = os.path.relpath(os.path.join(folder, fname), PHOTO_DIR)
                    files.append(rel_path.replace("\\", "/"))  # for Windows paths

    # Render template with current 'level' and files list
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Flood Control Captured Photos</title>
    <link href="https://fonts.googleapis.com/css?family=Montserrat:700,400" rel="stylesheet">
    <style>
        body { background: #f5f6fa; color: #222831; font-family: 'Montserrat', Arial, sans-serif; text-align: center; margin: 0; padding: 0;}
        .gallery-container { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 98vh;}
        h2 { margin-bottom: 24px; font-weight: 700; letter-spacing: 0.03em;}
        .slide-img-box { position: relative; width: 600px; max-width: 90vw; margin-bottom: 12px;}
        #photo { width: 100%; max-height: 70vh; object-fit: contain; border-radius: 16px;
            box-shadow: 0 8px 24px rgba(44, 62, 80, 0.13), 0 1.5px 10px rgba(44,62,80,0.09);
            background: #e6e6e6; opacity: 0; transition: opacity 0.7s;}
        #photo.active { opacity: 1;}
        .gallery-controls { margin-bottom: 10px;}
        button { font-size: 1.4em; font-family: inherit; padding: 9px 40px; background: #3742fa; color: #fff; border: none; border-radius: 30px; margin: 0 18px; cursor: pointer; box-shadow: 0 3px 11px rgba(44, 62, 80, 0.09); outline: none; transition: background 0.2s;}
        button:active { background: #5352ed;}
        #counter { font-size: 1.2em; color: #2e2e2e; margin-top: 12px; margin-bottom: 28px; letter-spacing: 0.02em;}
        .thumb-strip { display: flex; justify-content: center; flex-wrap: wrap;}
        .thumb { width: 56px; height: 38px; margin: 0 5px; object-fit: cover; border-radius: 7px; background: #d2dae2;
            box-shadow: 0 2px 8px rgba(44,62,80,0.06); cursor: pointer; opacity: 0.6; border: 2.5px solid #d2dae2;
            transition: opacity 0.3s, border 0.2s;}
        .thumb.selected { opacity: 1; border: 2.5px solid #3742fa;}
        .dropdown-bar { margin-bottom: 20px; }
        @media (max-width: 800px) {
            .slide-img-box { width: 99vw; }
            #photo { max-height: 56vw; }
        }
    </style>
</head>
<body>
    <div class="gallery-container">
        <h2>Flood Monitoring Captured Photos</h2>
        <div class="dropdown-bar">
            <label for="level-select"><b>Show:</b></label>
            <select id="level-select">
                <option value="all" {% if level == 'all' %}selected{% endif %}>All Photos</option>
                <option value="yellow" {% if level == 'yellow' %}selected{% endif %}>Yellow Warning Level</option>
                <option value="orange" {% if level == 'orange' %}selected{% endif %}>Orange Warning Level</option>
                <option value="red" {% if level == 'red' %}selected{% endif %}>Red Warning Level</option>
            </select>
        </div>
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
let photos = {{ files|tojson }};
let idx = 0;

// handle dropdown change
document.addEventListener("DOMContentLoaded", function() {
    document.getElementById('level-select').addEventListener('change', function() {
        let selected = this.value;
        window.location = "/photos?level=" + selected;
    });
});

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

preloadThumbnails(photos);
updatePhoto();
</script>
</body>
</html>
    ''', files=files, level=level)

def start_camera_streaming_thread():
    global stream_thread
    if stream_thread is None:
        stream_thread = threading.Thread(target=some_function_that_runs_gen_frames)
        stream_thread.start()

def stop_camera_streaming_thread():
    global stream_thread
    global streaming_active
    streaming_active = False
    if stream_thread:
        stream_thread.join()
        stream_thread = None