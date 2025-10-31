import sys

import serial

class A0221AU:
    def __init__(self, port='/dev/serial0', baudrate=9600, timeout=1):
        self.ser = None
        self.buffer = bytearray()

        try:
            self.ser = serial.Serial(port, baudrate, timeout=timeout)
            print(f"✅ Connected to {port} at {baudrate} baud.")
        except FileNotFoundError:
            print(f"❌ Serial port '{port}' not found. Make sure it exists and is enabled.")
            sys.exit(1)  # exit with error code 1
        except serial.SerialException as e:
            print(f"❌ Failed to open serial port '{port}': {e}")
            sys.exit(1)



    def _read_frame(self):
        """Read and return one complete 4-byte frame [0xFF, 0xFF, high, low]."""
        bytes_to_read = self.ser.in_waiting
        if bytes_to_read:
            self.buffer.extend(self.ser.read(bytes_to_read))

        while len(self.buffer) >= 4:
            if self.buffer[0] == 0xFF and self.buffer[1] == 0xFF:
                frame = self.buffer[:4]
                del self.buffer[:4]
                return frame
            else:
                del self.buffer[0]
        return None

    def read_distance(self):
        """Return distance in centimeters (float) or None if not ready."""
        frame = self._read_frame()
        if frame:
            dist_mm = (frame[2] << 8) + frame[3]
            return dist_mm / 10.0
        return None

    def close(self):
        """Close the serial connection."""
        if self.ser.is_open:
            self.ser.close()
