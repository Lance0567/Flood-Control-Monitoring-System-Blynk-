# main.py
import time
from devices.ultra_sonic_sensor import A0221AU
from devices.camera_module import PiCameraModule
from camera_server import CameraServer

sensor = None

def init_sensor():
    global sensor
    sensor = A0221AU('/dev/serial0', 9600)
    print("A0221AU sensor initialized.")
    print("Press Ctrl+C to stop.\n")

def init_camera():
    camera = PiCameraModule(width=640, height=480)

    try:
        # Initialize and start camera
        camera.start()

        # Initialize and start server
        server = CameraServer(camera_module=camera, port=8000)
        server.start()

    except KeyboardInterrupt:
        camera.stop()
        print("⚙️ Stream manually stopped.")

def run_sensor():
    global sensor
    if sensor is None:
        raise RuntimeError("Sensor not initialized. Call start() first.")
    try:
        while True:
            distance = sensor.read_distance()
            if distance is not None:
                print(f"Distance: {distance:.1f} cm")
            time.sleep(0.01)
    except KeyboardInterrupt:
        sensor.close()
        print("\nStopped.")


def start():
    init_camera()


def loop():
    pass



def main():
    start()
    loop()


if __name__ == "__main__":
    main()
