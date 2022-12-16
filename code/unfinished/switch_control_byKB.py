import serial
import time

port = 'COM3'
try:
    ser = serial.Serial(port, 9600, timeout=1)
except serial.serialutil.SerialException:
    print("Arduino not connected")

hex_string1 = """A0 01 01 A2"""  #turn on str
some_bytes1 = bytearray.fromhex(hex_string1)
hex_string2 = """A0 01 00 A1"""  #turn off str
some_bytes2 = bytearray.fromhex(hex_string2)

while True:
    input_val = int(input("Press 1 for turn on the switch\nPress 0 for turn off the switch\nPress 9 for Exit\n"))
    if (input_val == 1):
        ser.write(some_bytes1)
        print('Icon On!')
    elif (input_val == 0):
        ser.write(some_bytes2)
        print('Icon OFF!')
    elif (input_val == 9):
        break
    else:
        print("you have pressed the wrong button!!!")

ser.close()
