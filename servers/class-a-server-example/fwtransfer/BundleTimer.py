class BundleTimer:
    def __init__(self, timeout_callback):
        self.callback = timeout_callback
        self.ind_start = 0
        self.ind_end = 0


    def start(self, queue_start, queue_end):
        self.ind_start = queue_start
        self.ind_end = queue_end

