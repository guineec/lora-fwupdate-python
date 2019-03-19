from threading import Timer


class BundleTimer:
    def __init__(self, timeout, timeout_callback):
        self.callback = timeout_callback
        self.resend_pkts = []
        self.timeout = timeout
        self.timer = None

    def __on_timeout(self):
        print("TIMEOUT")
        for index in self.resend_pkts:
            print("NACKING " + str(index))
            self.callback(index)
        self.resend_pkts = []

    def start(self):
        self.timer = Timer(self.timeout, self.__on_timeout)

    def stop(self):
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None
        self.resend_pkts = []
