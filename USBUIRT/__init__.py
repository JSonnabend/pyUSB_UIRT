from ctypes import (
    c_int, c_uint, c_ulong, byref, c_ubyte, c_char_p, c_void_p, POINTER,
    WINFUNCTYPE, Structure, GetLastError, create_string_buffer, WinDLL,
    string_at,
)
import datetime
import threading
import pydevd

INVALID_HANDLE_VALUE = -1
UINT32 = c_uint


class UUINFO(Structure):
    _fields_ = (
        ('fwVersion',   c_uint),
        ('protVersion', c_uint),
        ('fwDateDay',   c_ubyte),
        ('fwDateMonth', c_ubyte),
        ('fwDateYear',  c_ubyte),
    )
PUUINFO = POINTER(UUINFO)

UUIRTDRV_ERR_NO_DEVICE = 0x20000001
UUIRTDRV_ERR_NO_RESP = 0x20000002
UUIRTDRV_ERR_NO_DLL = 0x20000003
UUIRTDRV_ERR_VERSION = 0x20000004

UUIRTDRV_CFG_LEDRX = 0x0001
UUIRTDRV_CFG_LEDTX = 0x0002
UUIRTDRV_CFG_LEGACYRX = 0x0004

UUIRTDRV_IRFMT_UUIRT = 0x0000
UUIRTDRV_IRFMT_PRONTO = 0x0010

UUIRTDRV_IRFMT_LEARN_FORCERAW = 0x0100
UUIRTDRV_IRFMT_LEARN_FORCESTRUC    = 0x0200
UUIRTDRV_IRFMT_LEARN_FORCEFREQ = 0x0400
UUIRTDRV_IRFMT_LEARN_FREQDETECT    = 0x0800


UUCALLBACKPROC = WINFUNCTYPE(c_int, POINTER(c_ubyte), c_ulong, c_ulong)
LEARNCALLBACKPROC = WINFUNCTYPE(c_int, c_uint, c_uint, c_ulong, c_void_p)


class USB_UIRT():
    receiveCallback = None
    learnSuccessCallback = None
    learnProgressCallback = None

    @property
    def onReceive(self):
        return self.receiveCallback
    @onReceive.setter
    def onReceive(self, callback):
        self.receiveCallback = callback

    @property
    def onLearnProgress(self):
        return self.learnProgressCallback
    @onLearnProgress.setter
    def onLearnProgress(self, callback):
        self.learnProgressCallback = callback

    @property
    def onLearnSuccess(self):
        return self.learnSuccessCallback
    @onLearnSuccess.setter
    def onLearnSuccess(self, callback):
        self.learnSuccessCallback = callback

    def __init__(self):
        self.dll = None
        self.enabled = False


    def __close__(self):
        self.dll.UUIRTClose(self.hDrvHandle)


    def __start__(
        self,
        ledRX=True,
        ledTX=True,
        legacyRX=False,
        repeatStopCodes=False,
    ):
        self.args = (ledRX, ledTX, legacyRX, repeatStopCodes)
        self.codeFormat = UUIRTDRV_IRFMT_PRONTO
        try:
            self.dll = WinDLL('uuirtdrv')
        except:
            raise Exception("DriverNotFound")
        puDrvVersion = c_uint(0)
        if not self.dll.UUIRTGetDrvInfo(byref(puDrvVersion)):
            raise Exception("Unable to retrieve uuirtdrv version!")
        if puDrvVersion.value != 0x0100:
            raise Exception("Invalid uuirtdrv version!")

        # if self.info.evalName[-1].isdigit():
        #     self.deviceStr = "USB-UIRT-%s" % self.info.evalName[-1]
        # else:
        #     self.deviceStr = "USB-UIRT"
        self.deviceStr = "USB-UIRT"
        self.hDrvHandle = self.dll.UUIRTOpenEx(self.deviceStr, 0, 0, 0)
        if self.hDrvHandle == INVALID_HANDLE_VALUE:
            err = GetLastError()
            if err == UUIRTDRV_ERR_NO_DLL:
                raise self.Exceptions.DriverNotFound
            elif err == UUIRTDRV_ERR_NO_DEVICE:
                raise self.Exceptions.DeviceNotFound
            elif err == UUIRTDRV_ERR_NO_RESP:
                raise self.Exceptions.DeviceInitFailed
            else:
                raise self.Exceptions.DeviceInitFailed

        puuInfo = UUINFO()
        if not self.dll.UUIRTGetUUIRTInfo(self.hDrvHandle, byref(puuInfo)):
            raise self.Exceptions.DeviceInitFailed
        self.firmwareVersion = "%d.%d" % (
            puuInfo.fwVersion >> 8,
            puuInfo.fwVersion & 0xFF
        )
        self.protocolVersion = "%d.%d" % (
            puuInfo.protVersion >> 8,
            puuInfo.protVersion & 0xFF
        )
        self.firmwareDate = datetime.date(
            puuInfo.fwDateYear+2000,
            puuInfo.fwDateMonth,
            puuInfo.fwDateDay
        )
        self.receiveProc = UUCALLBACKPROC(self.ReceiveCallback)
        res = self.dll.UUIRTSetRawReceiveCallback(
            self.hDrvHandle,
            self.receiveProc,
            0
        )
        if not res:
            self.dll = None
            raise self.Exception("Error calling UUIRTSetRawReceiveCallback")

        self._SetConfig(ledRX, ledTX, legacyRX, repeatStopCodes)
        self.enabled = True


    def __stop__(self):
        if self.dll:
            if not self.dll.UUIRTClose(self.hDrvHandle):
                raise Exception("Error calling UUIRTClose")

            # fix for USB-UIRT driver bug, See OnComputerSuspend for details.
            self.hDrvHandle = self.dll.UUIRTOpenEx(self.deviceStr, 0, 0, 0)
            # without the UUIRTSetUUIRTConfig call, the driver seems to need
            # much more time to close.
            self.dll.UUIRTSetReceiveCallback(self.hDrvHandle, None, 0)
            self.dll.UUIRTClose(self.hDrvHandle)
            self.dll = None


    #this is old code from eventghost
    def OnComputerSuspend(self, suspendType):
        # The USB-UIRT driver seems to have a bug, that prevents the wake-up
        # from standby feature to work, if UUIRTSetRawReceiveCallback was used.
        # To workaround the problem, we re-open the device with
        # UUIRTSetReceiveCallback just before the system goes into standby and
        # later do the reverse once the system comes back from standby.
        if self.dll is None:
            return
        self.dll.UUIRTClose(self.hDrvHandle)
        self.hDrvHandle = dll.UUIRTOpenEx(self.deviceStr, 0, 0, 0)
        self.dll.UUIRTSetReceiveCallback(self.hDrvHandle, None, 0)


    #this is old code from eventghost
    def OnComputerResume(self, suspendType):
        if self.dll is None:
            return
        self.dll.UUIRTClose(self.hDrvHandle)
        self.hDrvHandle = dll.UUIRTOpenEx(self.deviceStr, 0, 0, 0)
        self.dll.UUIRTSetRawReceiveCallback(self.hDrvHandle, self.receiveProc, 0)


    #this is old code from eventghost
    def OnDeviceRemoved(self, event):
        if event.payload[0].split("#")[1] == 'Vid_0403&Pid_f850':
            if self.dll:
                if not self.dll.UUIRTClose(self.hDrvHandle):
                    raise self.Exception("Error calling UUIRTClose")
                self.dll = None

    #this is old code from eventghost
    def OnDeviceAttached(self, event):
        if event.payload[0].split("#")[1] == 'Vid_0403&Pid_f850':
            if self.enabled:
                self.__start__(*self.args)


    def _SetConfig(self, ledRX, ledTX, legacyRX, repeatStopCodes=False):
        value = 0
        if ledRX:
            value |= UUIRTDRV_CFG_LEDRX
        if ledTX:
            value |= UUIRTDRV_CFG_LEDTX
        if legacyRX:
            value |= UUIRTDRV_CFG_LEGACYRX
        if repeatStopCodes:
            value |= 16
        if not self.dll.UUIRTSetUUIRTConfig(self.hDrvHandle, UINT32(value)):
            self.dll = None
            raise self.Exception("Error calling UUIRTSetUUIRTConfig")


    def ReceiveCallback(self, buf, length, userdata):
        pydevd.settrace(suspend=False, trace_only_current_thread=True)
        data = []
        for i in range(2, 1024):
            value = buf[i]
            data.append(value)
            if value == 255:
                if self.onReceive:
                    self.onReceive(data)
                break
        return 0

    def TransmitIR(self, code='', repeatCount=4, inactivityWaitTime=0):
        if self.dll is None:
            return
        if len(code) > 5:
            start = 0
            if code[0] == "Z":
                start = 2
            if code[start+3] == "R":
                codeFormat = UUIRTDRV_IRFMT_UUIRT
            elif code[start+4] == " ":
                codeFormat = UUIRTDRV_IRFMT_PRONTO
            else:
                codeFormat = UUIRTDRV_IRFMT_LEARN_FORCESTRUC
        else:
            repeatCount = 0
            codeFormat = UUIRTDRV_IRFMT_PRONTO
            code = ""
        if not self.dll.UUIRTTransmitIR(
            self.hDrvHandle,    # hHandle
            c_char_p(code),     # IRCode
            codeFormat,         # codeFormat
            repeatCount,        # repeatCount
            inactivityWaitTime, # inactivityWaitTime
            0,                  # hEvent
            0,                  # reserved1
            0                   # reserved2
        ):
            raise Exception("DeviceNotReady")

    def IRLearnInit(self):
        self.codeFormat = UUIRTDRV_IRFMT_PRONTO
        self.StartLearnIR()


    def SetRawMode(self, flag=True):
        if flag:
            self.codeFormat = UUIRTDRV_IRFMT_LEARN_FORCERAW
        else:
            self.codeFormat = UUIRTDRV_IRFMT_PRONTO


    def StartLearnIR(self):
        self.learnThreadAbortEvent = threading.Event()
        self.bAbortLearn = c_int(0)
        self.learnThread = threading.Thread(target=self.LearnThread)
        self.learnThread.start()


    def AbortLearnThread(self):
        self.bAbortLearn.value = True


    def AbortLearnThreadWait(self):
        self.bAbortLearn.value = True
        self.learnThreadAbortEvent.wait(10)


    def AcceptBurst(self):
        self.bAbortLearn.value = -1


    def LearnThread(self):
        pydevd.settrace(suspend=False, trace_only_current_thread=True)
        learnBuffer = create_string_buffer('\000' * 2048)
        self.dll.UUIRTLearnIR(
            self.hDrvHandle,                       # hHandle
            self.codeFormat,                       # codeFormat
            learnBuffer,                           # IRCode buffer
            LEARNCALLBACKPROC(self.LearnCallback), # progressProc
            0x5a5a5a5a,                            # userData
            byref(self.bAbortLearn),               # *pAbort
            0,                                     # param1
            0,                                     # reserved0
            0                                      # reserved1
        )
        if self.bAbortLearn.value != 1:
            self.OnLearnSuccess(learnBuffer.value)
        self.learnThreadAbortEvent.set()
        self.AbortLearnThread()


    def LearnCallback(self, progress, sigQuality, carrierFreq, userData):
        pydevd.settrace(suspend=False, trace_only_current_thread=True)
        # print ("progress: %s\tsigQuality: %s\tcarrierFre-q: %s\tuserData: %s" % (progress,sigQuality,carrierFreq,userData))
        if self.onLearnProgress:
            self.onLearnProgress(progress, sigQuality, carrierFreq, userData)
        # if progress > 0:
        #     self.burstButton.Enable(True)
        # self.progressCtrl.SetValue(progress)
        # self.sigQualityCtrl.SetValue(sigQuality)
        # self.carrierFreqCtrl.SetLabel(
        #     "%d.%03d kHz" % (carrierFreq / 1000, carrierFreq % 1000)
        # )
        return 0


    def OnLearnSuccess(self, code):
        pydevd.settrace(suspend=False, trace_only_current_thread=True)
        # print('learned code: %s' % code)
        if self.onLearnSuccess:
            self.onLearnSuccess(code)


    def OnRawBox(self, event):
        self.AbortLearnThreadWait()
        self.SetRawMode(self.forceRawCtrl.GetValue())
        # self.burstButton.Enable(False)
        # self.progressCtrl.SetValue(0)
        # self.sigQualityCtrl.SetValue(0)
        self.StartLearnIR()


    def OnAcceptBurst(self, event):
        self.AcceptBurst()


    def OnClose(self, event):
        self.AbortLearnThread()
        event.Skip()
        self.Destroy()


    def OnCancel(self, event):
        self.AbortLearnThread()
