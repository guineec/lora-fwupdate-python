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


class SRNackClassB:
    def __init__(self, update_contents, num_rx_windows=1):
        self.nrx_windows = num_rx_windows
        self.expected_acks = []
        self.acks_rcvd = set()
        self.update_segments = defaultdict()
        self.update_queue = []
        self.update_contents = bytearray.fromhex(update_contents)
        self.queue_pos = 0

    def __package_update(self):
        num_packets = len(self.update_contents) / 48
        remainder = len(self.update_contents) % 48
        num_packets = int(num_packets) + 1 if remainder > 0 else int(num_packets)
        for i in range(0, num_packets):
            # Segment update contents
            seq_num = str(hex(i))
            seq_num = seq_num[2:].zfill(3)
            index = str(hex(i))[2:].zfill(2)
            seg_start = i * 48
            seg_end = seg_start + 47
            if seg_end >= (len(self.update_contents) - 1):
                firmware_segment = self.update_contents[seg_start:]
            else:
                firmware_segment = self.update_contents[seg_start:seg_end]
            self.update_segments[i] = {"data": None, "seq_num": None, "index": None}
            self.update_segments[i]['data'] = bytes(firmware_segment)
            self.update_segments[i]["seq_num"] = seq_num
            self.update_segments[i]["index"] = index
            packet = self.update_segments[i]
            self.update_queue.append(packet)

    def start_update(self):
        # Load the first m packets
        packets = bytearray()
        self.__package_update()
        self.queue_pos = 0
        limit = len(self.update_queue) if self.queue_pos + self.nrx_windows >= len(
            self.update_queue) - 1 else self.queue_pos + self.nrx_windows + 1
        for i in range(0, limit):
            # Make the segment packet
            opcode = '1' if (i == limit - 1) and (self.queue_pos == (len(self.update_queue) - 1)) else '0'
            seq_num = self.update_queue[i]["seq_num"]
            index = self.update_queue[i]["index"]
            header = opcode + seq_num
            preamble = bytearray.fromhex(header + index)
            packet_arr = preamble + self.update_queue[i]["data"]
            packets += packet_arr
            self.expected_acks.append(int(index, 16))
            self.queue_pos += 1
        return packets

    def next(self):
        packets = bytearray()
        last_opcode = '1' if self.queue_pos + self.nrx_windows >= (len(self.update_queue) - 1) else '0'
        print(last_opcode)
        for i in range(self.queue_pos, (self.queue_pos + self.nrx_windows)):
            if i < len(self.update_queue):
                # Make the segment packet
                opcode = last_opcode if i == len(self.update_queue) - 1 else '0'
                seq_num = self.update_queue[i]["seq_num"]
                index = self.update_queue[i]["index"]
                header = opcode + seq_num
                preamble = bytearray.fromhex(header + index)
                packet_arr = preamble + self.update_queue[i]["data"]
                self.expected_acks.append(
                    int(self.update_queue[self.queue_pos]["index"], 16)) if not self.queue_pos == 0 else 0
                packets += packet_arr
                self.queue_pos += 1
        return packets

    # Returns true or false, indicating that next does or does not need to be called
    def check_acks(self, uplink_contents):
        # Seq number not needed for now
        opcode = int(uplink_contents[0], 16) if len(uplink_contents) > 1 else 1
        data = bytearray.fromhex(uplink_contents)[2:]
        print(data)
        unacked = []

        for ind in data:
            unacked.append(int(ind))

        acked = list(set(self.expected_acks) - set(unacked))
        self.expected_acks = []
        self.acks_rcvd.update(acked)
        print(acked)

        for ind in unacked:
            if ind not in self.acks_rcvd:
                self.nack(ind)

        if len(unacked) == 0 and opcode == 1:
            return False
        else:
            return True

    def nack(self, index):
        print("---X NACK: %s X---" % index)
        # Add it to reschedule queue
        self.update_queue.append(self.update_segments[index])
        print(self.update_queue)
