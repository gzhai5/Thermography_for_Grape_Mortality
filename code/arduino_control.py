import pyfirmata
import time

port = 'COM3'
relay_pin = 12
try:
    board = pyfirmata.Arduino('COM3')
except IOError:
    print("Ardino not found connected at port " + port)

while True:
    input_val = int(input("Press 1 for turn on the switch\nPress 0 for turn off the switch\nPress 9 for Exit\n"))
    if (input_val == 1):
        board.digital[relay_pin].write(1)
        print('Icon On!')
    elif (input_val == 0):
        board.digital[relay_pin].write(0)
        print('Icon OFF!')
    elif (input_val == 9):
        break
    else:
        print("you have pressed the wrong button!!!")




