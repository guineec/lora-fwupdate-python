from collections import defaultdict


# Functions and classes for the designed protocol
class FWUpdateBase:
    """
    ABSTRACT class used to define the behaviour an update protocol should expose.
    This might be useful when designing/testing several different protocols as we can rely, when calling them in
    the server's code, on the fact that they will all behave in the same way.
    """

    # Update contents should be passed in as a hex string
    def __init__(self, update_contents, dev_eui, api_instance):
        self.update_contents = bytearray.fromhex(update_contents)
        self.device = dev_eui
        self.api = api_instance
        self.update_segments = defaultdict()
        self.update_queue = []
        self.queue_pos = 0

    def __package_update(self):
        raise NotImplementedError("Abstract method 'FWUpdateBase.__package_update' not implemented.")

    def start_update(self):
        raise NotImplementedError("Abstract method 'FWUpdateBase.init_update' not implemented.")

    def next(self):
        raise NotImplementedError("Abstract method 'FWUpdateBase.next' not implemented.")

    def nack(self, index):
        raise NotImplementedError("Abstract method 'FWUpdateBase.nack' not implemented.")


class TrueSelectiveRepeat:
    def __init__(self, update_contents, num_rx_windows=1):
        self.nrx_windows = num_rx_windows
        self.expected_acks = []
        self.acks_rcvd = set()
        self.update_segments = []
        self.window = []
        self.send_queue = []
        self.update_contents = bytearray.fromhex(update_contents)
        self.queue_pos = 0
        self.tx_total = 0
        self.pkts_sent = 0
        self.retransmits = 0
        self.seq_sent = 0

    def __package_update(self):
        num_packets = len(self.update_contents) / 48
        remainder = len(self.update_contents) % 48
        num_packets = int(num_packets) + 1 if remainder > 0 else int(num_packets)
        for i in range(0, num_packets):
            # Segment update contents
            seq_num = str(hex(int(i / self.nrx_windows)))
            seq_num = seq_num[2:].zfill(3)
            index = str(hex(i))[2:].zfill(2)
            seg_start = i * 48
            seg_end = seg_start + 47
            if seg_end >= (len(self.update_contents) - 1):
                firmware_segment = self.update_contents[seg_start:]
            else:
                firmware_segment = self.update_contents[seg_start:seg_end]
            self.update_segments.append({"data": None, "seq_num": None, "index": None})
            self.update_segments[i]['data'] = bytes(firmware_segment)
            self.update_segments[i]["seq_num"] = seq_num
            self.update_segments[i]["index"] = index

    def start_update(self):
        # Load the first m packets
        packets = bytearray()
        self.__package_update()
        self.queue_pos = 0
        self.seq_sent = 0
        for i in range(0, self.nrx_windows):
            # Ensure not out of range
            if not (self.is_last() and i >= len(self.send_queue)):
                # Make the segment packet
                opcode = '1' if self.is_last() and i == len(self.send_queue) - 1 else '0'
                seq_num = '000'
                index = self.update_segments[i]["index"]
                header = opcode + seq_num
                preamble = bytearray.fromhex(str(header) + str(index))
                packet_arr = preamble + self.update_segments[i]["data"]
                packets += packet_arr
                self.pkts_sent += 1
                self.expected_acks.append(int(index, 16))
        self.seq_sent += 1
        self.tx_total += 1
        print(packets)
        return packets

    def next(self):
        if not self.queue_pos == -1:
            self.seq_sent += 1
            packets = bytearray()
            for c, i in enumerate(self.send_queue):
                # Ensure not out of range
                if not (self.is_last() and c >= len(list(self.send_queue))):
                    # Make seg packet
                    opcode = '1' if self.is_last() and c == len(self.send_queue) - 1 else '0'

                    seq_num = str(hex(self.seq_sent))[2:].zfill(3)
                    index = i["index"]
                    header = opcode + seq_num
                    preamble = bytearray.fromhex(header + index)
                    packet_arr = preamble + i["data"]
                    packets += packet_arr
                    self.expected_acks.append(int(index, 16))
                    self.pkts_sent += 1
            self.seq_sent += 1
            self.tx_total += 1
            self.send_queue = []
            return packets
        else:
            return []

    # Returns true or false, indicating that next does or does not need to be called
    def check_acks(self, uplink_contents):
        if self.queue_pos == -1:
            return False
        # Seq number not needed for now
        opcode = int(uplink_contents[0], 16) if len(uplink_contents) > 1 else 1
        data = bytearray.fromhex(uplink_contents)[2:]
        rcvd_acks = []
        for ind in data:
            rcvd_acks.append(int(ind))
            self.acks_rcvd.add(ind)

        self.window = self.update_segments[self.queue_pos:self.queue_pos + self.nrx_windows]

        unacked = []
        print(rcvd_acks, self.expected_acks)
        exp = self.expected_acks
        exp.sort()
        if not len(rcvd_acks) == 0:
            unacked = list(set(self.expected_acks) - set(rcvd_acks))
            self.expected_acks = []
            print(unacked)

            for ind in unacked:
                if ind not in self.acks_rcvd:
                    print("----X NACK %s X----" % ind)
                    self.retransmits += 1
                    self.send_queue.append(self.update_segments[ind])

        unacked.sort()
        if len(unacked) > 0:
            self.queue_pos = unacked[0]
        elif len(exp) > 0:
            self.queue_pos = exp[-1] + 1
        else:
            self.queue_pos = -1
        self.send_queue += self.update_segments[self.queue_pos:self.queue_pos + self.nrx_windows]
        send_queue_list = [int(v["index"], 16) for v in self.send_queue]
        self.send_queue = list(set(send_queue_list) - self.acks_rcvd)
        self.send_queue.sort()
        self.send_queue = [self.update_segments[i] for i in self.send_queue]

        if len(unacked) == 0 and opcode == 1:
            return False
        else:
            return True

    def is_last(self):
        last = len(self.update_segments) - len(list(self.acks_rcvd)) <= self.nrx_windows
        return last
