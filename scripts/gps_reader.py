import time
import serial
import pynmea2

SERIAL_PORT = "/dev/serial0"
BAUD_RATE = 9600


def get_gps_data(timeout_seconds=3):
    """
    Try to get valid GPS coordinates within a timeout.
    Returns (lat, lon) or (None, None).
    """
    start_time = time.time()

    try:
        ser = serial.Serial(SERIAL_PORT, baudrate=BAUD_RATE, timeout=1)

        while time.time() - start_time < timeout_seconds:
            line = ser.readline().decode("ascii", errors="replace").strip()

            if not line:
                continue

            if "$GPRMC" in line or "$GNRMC" in line:
                try:
                    msg = pynmea2.parse(line)
                    if msg.latitude and msg.longitude:
                        ser.close()
                        return float(msg.latitude), float(msg.longitude)
                except pynmea2.ParseError:
                    continue

        ser.close()

    except Exception as e:
        print(f"GPS warning: {e}")

    return None, None