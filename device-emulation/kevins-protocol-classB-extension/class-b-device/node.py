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
                ul_data += str(hex(ind))[2:].zfill(2)
            res = requests.post(self.url + "/uplink", data=json.dumps({"hex": ul_data}))
        self.ack_queue = []
        hex_str = res.content.encode('hex')
        hex_bytes = bytearray.fromhex(hex_str)
        new_seq_num = hex_str[1:4]
        new_opcode = ""
        indices = []
        for i in range(0, len(hex_bytes), 50):
            time.sleep(random.randint(0, 8))  # Random transmission delay simulated
            if i + 50 >= len(hex_bytes) - 1:
                pkt = hex_bytes[i:]
                pkt_hex = hex_str[(i * 2):]
                new_opcode = pkt_hex[0]
                number = random.randint(1, 100)
                # Drop packets based on SF
                if number > self.drop_chance:
                    indices.append(pkt[2])
                else:
                    self.dropped_packets += 1
            else:
                byte = hex_bytes[i:i + 50]
                # Drop packets based on SF
                number = random.randint(1, 100)
                if number > self.drop_chance:
                    indices.append(byte[2])
                else:
                    self.dropped_packets += 1
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
                time.sleep(60 * self.nrx_windows)  # TODO change back to 60 * nrx_windows
            is_start = False
            finished = self.uplink()
            if finished:
                ul_data = self.last_downlink["opcode"] + self.last_downlink["seq_num"]
                for ind in self.ack_queue:
                    ul_data += str(hex(ind))[2:].zfill(2)
                requests.post(self.url + "/uplink", data=json.dumps({"hex": ul_data}))
                end_time = time.asctime(time.localtime(time.time()))
                print(" END TIME: " + end_time)
                print(" UPLINKS:  " + str(self.uplinks))
                print(" DROPS:    " + str(self.dropped_packets))
                print(" EFF ULS:  " + str(self.uplinks - self.dropped_packets))
                print("|---- UPDATE COMPLETE ----|")


dev = KPAClassBDevice("http://localhost:5001", spreading_factor=12, nrx_windows=20)
dev.run()
