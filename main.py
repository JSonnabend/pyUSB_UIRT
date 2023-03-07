# coding=utf-8
# This is a sample Python script.
import time

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import USBUIRT

def dataReceived(data):
    print(data)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    usbuirt = USBUIRT.USB_UIRT()
    usbuirt.__start__()
    usbuirt.onReceive = dataReceived
    usbuirt.TransmitIR(u'0000 006E 0000 0022 00A9 00AB 0015 0040 0015 0040 0015 0040 0015 0016 0015 0016 0015 0015 0015 0016 0015 0016 0015 0040 0015 0040 0015 0040 0015 0015 0015 0016 0015 0016 0015 0016 0015 0016 0015 0016 0015 0040 0015 0016 0015 0016 0015 0016 0015 0016 0015 0016 0015 0015 0015 0040 0015 0016 0015 0040 0015 0040 0015 0040 0015 0040 0015 0040 0015 0040 0015 06E6', 1, 500)
    while True:
        time.sleep(1)



