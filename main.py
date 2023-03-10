# coding=utf-8
# This is a sample Python script.
import time
import keyboard
import USBUIRT
usbuirt = USBUIRT.USB_UIRT()

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


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    try:
        keyboard.on_press(onKeyPress)
        usbuirt.__start__()
        usbuirt.onReceiveRaw = dataReceivedRaw
        usbuirt.onReceive = dataReceived
        usbuirt.onLearnProgress = learnProgress
        usbuirt.onLearnSuccess = learnSuccess
        usbuirt.IRLearnInit()
        usbuirt.TransmitIR(u'0000 006E 0000 0022 00A9 00AB 0015 0040 0015 0040 0015 0040 0015 0016 0015 0016 0015 0015 0015 0016 0015 0016 0015 0040 0015 0040 0015 0040 0015 0015 0015 0016 0015 0016 0015 0016 0015 0016 0015 0016 0015 0040 0015 0016 0015 0016 0015 0016 0015 0016 0015 0016 0015 0015 0015 0040 0015 0016 0015 0040 0015 0040 0015 0040 0015 0040 0015 0040 0015 0040 0015 06E6', 1, 500)
        while True:
            time.sleep(1)
    finally:
        usbuirt.__close__()



