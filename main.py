import sys
import time
sys.path.append('/home/jesse/blynk-library-python')
from BlynkLib import Blynk
from captured_photos import handle_take_photo
from combined_server import start_flask_server, stop_flask_server, start_hls_stream, stop_hls_stream

BLYNK_AUTH = "wZ5IP73LpgMdLK1PDRnGEFBLHzDagQZq"
blynk = Blynk(BLYNK_AUTH)

camera = None
streaming_active = False  # This should track V1 state changes

@blynk.on("connected")
def blynk_connected(*args, **kwargs):   # Accepts any arguments
    print("/ Raspberry Pi Connected to Blynk")
    blynk.set_property(1, "url", "https://pi.ustfloodcontrol.site/video/index.m3u8")

@blynk.on("V0")
def on_v0(value):
    global camera, streaming_active
    val = int(value[0])
    if val == 1:
        if streaming_active:
            stop_hls_stream()
            stop_flask_server()
            streaming_active = False
            blynk.virtual_write(1, 0)
        from picamera2 import Picamera2
        camera = Picamera2()
        camera.configure(camera.create_preview_configuration(main={"size": (840, 560), "format": "RGB888"}))
        camera.start()
        handle_take_photo(blynk, camera)
        camera.stop()
        camera.close()
        camera = None
    else:
        if camera:
            camera.stop()
            camera.close()
            camera = None

@blynk.on("V1")
def on_v1(value, *args, **kwargs):
    global streaming_active
    val = int(value[0])
    if val == 1:
        start_flask_server()
        start_hls_stream()
        streaming_active = True
        blynk.set_property(1, "url", "https://pi.ustfloodcontrol.site/video/index.m3u8")
    else:
        stop_hls_stream()
        stop_flask_server()
        streaming_active = False

try:
    while True:
        blynk.run()
except KeyboardInterrupt:
    if camera:
        camera.stop()
    print("Exiting cleanly.")
