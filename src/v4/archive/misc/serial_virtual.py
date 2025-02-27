import serial
import time
import random

# Set up a virtual serial port (you'll need to adjust this to your actual port later)
SERIAL_PORT = '/dev/ttys016'  # Change this to the virtual port path you set up
BAUD_RATE = 9600

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
except SerialException:
    ser = None  # No serial port, fallback to console output
    print(f"Serial port {SERIAL_PORT} not found. Running in simulation mode.")


def send_data():
    # Generate and format the 10x20 matrix
    matrix = [[random.randint(0, 1023) for _ in range(20)] for _ in range(10)]
    data_line = '\t'.join(
        map(str, [val for row in matrix for val in row])) + '\n'

    # Send or print the data line
    if ser:
        ser.write(data_line.encode('utf-8'))
    else:
        print(data_line)  # Print to console instead of serial


try:
    while True:
        send_data()
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Stopping simulation.")
finally:
    if ser:
        ser.close()
