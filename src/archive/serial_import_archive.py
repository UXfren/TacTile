import serial.tools.list_ports

# # ports = serial.tools.list_ports.comports()

# serialIsnt = serial.Serial()

# portlist = []

# for onePort in ports:
#     portlist.append(str(onePort))
#     print(str(onePort))

# val = input("select Port: COM")

# print(val)

# for x in range(0,len(portList)):
#     if portList[x].startswith("COM" + str(val)):
#         portVar = "COM" + str(val)
#         print(portList[x])

# serialInst.baudrate = 115200


def readserial(comport, baudrate):
    ser = serial.Serial(comport, baudrate, timeout=0.1)

    while True:
        data = ser.readline().decode().strip()
        if data:
            print(data)


if __name__ == '__main__':
    readserial('/dev/cu.usbmodem126032001', 115200)
