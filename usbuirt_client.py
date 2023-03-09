from msl.loadlib import Client64

class USB_UIRTclient(Client64):
    """Call a function in 'uuirtdrv.dll' via the 'USB_UIRTserver' wrapper."""

    def __init__(self):
        # Specify the name of the Python module to execute on the 32-bit server (i.e., 'my_server')
        super(USB_UIRTclient, self).__init__(module32='usbuirt_server', timeout=4)

    def version(self):
        # Get the version
        return self.request32('version')