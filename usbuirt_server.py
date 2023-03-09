import USBUIRT
from msl.loadlib import Server32
from ctypes import (
    c_int, c_uint, c_ulong, byref, c_ubyte, c_char_p, c_void_p, POINTER,
    WINFUNCTYPE, Structure, GetLastError, create_string_buffer, WinDLL,
    string_at,
)
import datetime
import sys
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

class USB_UIRTserver(Server32):
    def __init__(self, host, port, **kwargs):
        # The Server32 class has a 'lib' property that is a reference to the ctypes.CDLL object
        # Load the 'my_lib' shared-library file using ctypes.CDLL
        super(USB_UIRTserver, self).__init__('uuirtdrv.dll', 'cdll', host, port)
        self.dll = self.lib
        self.__start__()

        # self.version = self.dll.UUIRTGetDrvVersion()


    def __start__(
        self,
        ledRX=True,
        ledTX=True,
        legacyRX=False,
        repeatStopCodes=False,
    ):
        # pydevd.settrace(suspend=False, trace_only_current_thread=True)
        self.args = (ledRX, ledTX, legacyRX, repeatStopCodes)
        self.codeFormat = UUIRTDRV_IRFMT_PRONTO
        # try:
        #     self.dll = WinDLL('uuirtdrv')
        # except:
        #     raise Exception("DriverNotFound")
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
        self.receiveRawProc = UUCALLBACKPROC(self.ReceiveRawCallback)
        res = self.dll.UUIRTSetRawReceiveCallback(
            self.hDrvHandle,
            self.receiveRawProc,
            0
        )
        self.receiveProc = UUCALLBACKPROC(self.ReceiveCallback)
        res = self.dll.UUIRTSetReceiveCallback(
            self.hDrvHandle,
            self.receiveProc,
            0
        )
        if not res:
            self.dll = None
            raise self.Exception("Error calling UUIRTSetRawReceiveCallback")

        self._SetConfig(ledRX, ledTX, legacyRX, repeatStopCodes)
        self.enabled = True