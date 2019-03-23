import requests
import time
import random
import json


class InvalidSpreadingFactorException(Exception):
    pass


# Kevin's Protocol Adapted
class KPAClassBDevice:
    def __init__(self, url, spreading_factor=12, nrx_windows=20):
        self.start_time = 0
        self.end_time = 0
        self.url = url
        self.drop_chance = 0
        self.dropped_packets = 0
        self.ack_queue = []
        self.packets = []
        self.last_downlink = None
        self.data_str = ""
        self.nrx_windows = nrx_windows
        self.uplinks = 0
        if spreading_factor not in [7, 8, 9, 10, 11, 12]:
            raise InvalidSpreadingFactorException("Spreading factor must be either: 7, 8, 9, 10, 11 or 12")

        if spreading_factor == 7:
            self.drop_chance = 15
        elif spreading_factor == 8:
            self.drop_chance = 11
        elif spreading_factor == 9:
            self.drop_chance = 24
        elif spreading_factor == 10:
            self.drop_chance = 40
        elif spreading_factor == 11:
            self.drop_chance = 6
        else:
            self.drop_chance = 9

    def uplink(self):
        self.uplinks += 1
        if self.last_downlink is None:
            res = requests.post(self.url + "/uplink", data=json.dumps({"hex": "0000"}))
        else:
            ul_data = self.last_downlink["opcode"] + self.last_downlink["seq_num"]
            for ind in self.ack_queue:
                ul_data += ind
            res = requests.post(self.url + "/uplink", data=json.dumps({"hex": ul_data}))
        self.ack_queue = []

        # Need to process the pkts better - get the hexstring as a byte arr and loop through individual packets
        res_bytes = res.content
        hex_str = res_bytes.encode('hex')
        new_opcode = hex_str[0]
        new_seq_num = hex_str[1:4]
        indices_str = hex_str[4:]
        indices = []
        print(new_opcode)
        for i in range(0, len(indices_str), 2):
            if random.randint(0, 100) > self.drop_chance:
                indices.append(indices_str[i:i + 2])
        self.ack_queue = indices
        self.last_downlink = {"opcode": new_opcode, "seq_num": new_seq_num, "index": indices}
        return new_opcode is "1"

    def run(self):
        self.start_time = time.asctime(time.localtime(time.time()))
        print("|---- DEVICE STARTED ----|")
        print(" TIME:     " + self.start_time)
        print(" SF:       " + str(self.drop_chance) + "% drop likelihood")
        is_start = True
        while True:
            if not is_start:
                time.sleep(1 * self.nrx_windows)
            is_start = False
            finished = self.uplink()
            if finished:
                ul_data = self.last_downlink["opcode"] + self.last_downlink["seq_num"]
                for ind in self.ack_queue:
                    ul_data += ind
                requests.post(self.url + "/uplink", data=json.dumps({"hex": ul_data}))
                end_time = time.asctime(time.localtime(time.time()))
                print(" END TIME: " + end_time)
                print(" UPLINKS:  " + str(self.uplinks))
                print(" DROPS:    " + str(self.dropped_packets))
                print(" EFF ULS:  " + str(self.uplinks - self.dropped_packets))
                print("|---- UPDATE COMPLETE ----|")


dev = KPAClassBDevice("http://localhost:5001", spreading_factor=12)
dev.run()
