import serial.tools.list_ports


def readserial(comport, baudrate):
    ser = serial.Serial(comport, baudrate, timeout=0.1)

    while True:
        data = ser.readline().decode()
        if data:
            print(data)


if __name__ == '__main__':
    readserial('/dev/cu.usbmodem126032001', 115200)
