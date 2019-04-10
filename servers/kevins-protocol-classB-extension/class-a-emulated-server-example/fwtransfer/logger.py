import json


class Logger:
    def __init__(self, output="stdout"):
        self.total_uplinks = 0
        self.effective_uplinks = 0
        self.ineffective_uplinks = 0
        self.ratio = 0
        self.output = output
        self.has_logged = False

    def log(self):
        self.calc_ratio()
        log_dict = {
            "total_uplinks": self.total_uplinks,
            "effective_uplinks": self.effective_uplinks,
            "ineffective_uplinks": self.ineffective_uplinks,
            "ratio": self.ratio
        }

        if self.output == "stdout":
            print(json.dumps(log_dict))
        else:
            with open(self.output, "w+") as f:
                f.write(json.dumps(log_dict) + "\n")

    def effective_uplink(self):
        self.total_uplinks += 1
        self.effective_uplinks += 1
        self.ratio += 1

    def ineffective_uplink(self):
        self.total_uplinks += 1
        self.ineffective_uplinks += 1
        self.effective_uplinks -= 1

    def ratio_up(self):
        self.ratio += 1

    def ratio_down(self):
        self.ratio -= 2  # Account for the resend, which will increment the ratio

    def calc_ratio(self):
        self.ratio = self.ratio / self.total_uplinks
