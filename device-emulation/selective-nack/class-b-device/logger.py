import json

class Logger:
    def __init__(self, nrx_windows, output="stdout"):
        self.total_uplinks = 0
        self.effective_uplinks = 0
        self.ineffective_uplinks = 0
        self.ratio = -1
        self.output = output
        self.has_logged = False
        self.seen = set()
        self.nrx_windows = nrx_windows

    def write(self):
        if not self.has_logged:
            self.calc_ratio()
            log_dict = {
                "total_uplinks": self.effective_uplinks + self.ineffective_uplinks,
                "effective_uplinks": self.effective_uplinks,
                "ineffective_uplinks": self.ineffective_uplinks,
                "ratio": self.ratio
            }

            if self.output == "stdout":
                print(json.dumps(log_dict))
            else:
                with open(self.output, "w+") as f:
                    f.write(json.dumps(log_dict) + "\n")

    def uplink_rcvd(self, inds):
        self.total_uplinks += 1
        for ind in inds:
            if ind not in self.seen:
                self.effective_uplinks += 1
                self.ratio += 1
                self.seen.add(ind)
            else:
                self.ineffective_uplinks += 1

    # def effective_uplink(self):
    #     self.total_uplinks += 1
    #     self.effective_uplinks += 1

    def ineffective_uplink(self):
        self.total_uplinks += 1
        self.ineffective_uplinks += 1
        self.effective_uplinks -= 1

    # def ratio_up(self):
    #     self.ratio += 1

    # def ratio_down(self):
    #     self.ratio -= 1  # Account for the resend, which will increment the ratio

    def calc_ratio(self):
        self.ratio = self.ratio / self.total_uplinks
        self.ratio += 1