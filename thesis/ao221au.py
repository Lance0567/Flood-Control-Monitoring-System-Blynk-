import serial, time

ser = serial.Serial('/dev/serial0', 9600, timeout=1)

print("Reading A0221AU distance data... Press Ctrl+C to stop.")

try:
    while True:
        # Read one byte at a time
        first = ser.read(1)
        if first != b'\xFF':
            continue  # Not start of frame

        second = ser.read(1)
        if second != b'\xFF':
            continue  # False alarm, not a real frame

        # Now read the remaining two bytes (distance data)
        high = ser.read(1)
        low = ser.read(1)

        if len(high) == 1 and len(low) == 1:
            dist = (high[0] << 8 ) + low[0]
            if 20 <= dist <= 4500:
                print(f"Distance: {dist/10:.1f} cm")
            else:
                print("Out of range or invalid reading")
        else:
            print("Incomplete frame, skipping...")
            time.sleep(0.05)
except KeyboardInterrupt:
    ser.close()
    print("Stopped.")
