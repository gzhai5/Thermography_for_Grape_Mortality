# import usb.core
# import usb.util

# VENDOR_ID = 
# devices = usb.core.find(find_all=True)

# for device in devices:
#     print("VID: {:04x}, PID: {:04x}".format(device.idVendor, device.idProduct))


# import subprocess

# result = subprocess.run(['devcon', 'hwids', '=usb'], capture_output=True, text=True)
# print(result.stdout)


import serial.tools.list_ports

available_ports = list(serial.tools.list_ports.comports())
print(type(available_ports))
print(available_ports)
if not available_ports:
    print("gg")
else:
    for port in available_ports:
        print(port.device)

# import pyudev
# import subprocess

