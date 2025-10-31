import serial
import time

ser = serial.Serial('/dev/serial0', 9600, timeout=1)
buffer = bytearray()

print("Reading A0221AU distance data... Press Ctrl+C to stop.")

try:
    while True:
        bytes_to_read = ser.in_waiting
        if bytes_to_read:
            buffer.extend(ser.read(bytes_to_read))

        while len(buffer) >= 4:
            if buffer[0] == 0xFF and buffer[1] == 0xFF:
                frame = buffer[:4]
                del buffer[:4]

                dist = (frame[2] << 8 ) + frame[3]
                print(f"Distance: {dist/10:.1f} cm")

            else:
                del buffer[0]

        time.sleep(0.01)

except KeyboardInterrupt:
    ser.close()
    print("Stopped.")
