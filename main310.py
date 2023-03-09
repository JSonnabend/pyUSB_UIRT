# coding=utf-8
# This is a sample Python script.
import time
import keyboard

import usbuirt_server
from usbuirt_client import USB_UIRTclient

def dataReceivedRaw(data):
    print('data raw:')
    print(data)
    hexdata = ''
    for decimal in data:
        hexdata += hex(decimal) + ' '
    print(hexdata)

def dataReceived(data):
    print('data:')
    print(data)
    hexdata = ''
    for decimal in data:
        hexdata += hex(decimal) + ' '
    print(hexdata)

def learnProgress(progress, sigQuality, carrierFreq, userData):
    print("progress: %s\tsigQuality: %s\tcarrierFreq: %s\tuserData: %s" % (progress,sigQuality,carrierFreq,userData))

def learnSuccess(code):
    print('learned code: %s' % code)

def onKeyPress(event):
    if event.name == 'l':
        usbuirt.SetRawMode(False)
        usbuirt.StartLearnIR()

if __name__ == '__main__':
    try:
        _server = usbuirt_server.USB_UIRTserver(host='127.0.0.1', port=15000)
        usbuirt = USB_UIRTclient()
        print(usbuirt.version())
    finally:
        pass



