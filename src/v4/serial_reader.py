import serial.tools.list_ports
import serial


def read_serial(comport, baudrate):
    ser = serial.Serial(comport, baudrate, timeout=0.1)
    while True:
        data = serial.Serial(
            comport, baudrate, timeout=0.1).readline().decode()
        if data:
            values = list(map(int, data.split()))
            if len(values) == 200:
                sensor_data = values

                return sensor_data
            else:
                continue
        else:
            continue


if __name__ == '__main__':
    read_serial('/dev/cu.usbmodem126032001', 115200)
