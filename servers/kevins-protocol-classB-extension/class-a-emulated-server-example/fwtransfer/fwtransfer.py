from collections import defaultdict
from fwtransfer.logger import Logger


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


class KPAdaptedClassB:
    def __init__(self, update_contents, num_rx_windows=1, logger_file="test.json"):
        self.nrx_windows = num_rx_windows
        self.expected_acks = []
        self.acks_rcvd = set()
        self.update_segments = defaultdict()
        self.update_queue = []
        self.update_contents = bytearray.fromhex(update_contents)
        self.queue_pos = 0
        self.logger = Logger(output=logger_file)

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
        last_opcode = '1' if self.queue_pos >= (len(self.update_queue) - 1) else '0'
        for i in range(0, self.queue_pos + self.nrx_windows):
            # Make the segment packet
            opcode = last_opcode if i == self.queue_pos + self.nrx_windows else '0'
            seq_num = self.update_queue[i]["seq_num"]
            index = self.update_queue[i]["index"]
            header = opcode + seq_num
            preamble = bytearray.fromhex(header + index)
            packet_arr = preamble + self.update_queue[i]["data"]
            packets += packet_arr
            self.expected_acks.append(int(index))
            self.queue_pos += 1
            self.logger.ratio_up()
        self.logger.effective_uplink()
        return packets

    def next(self):
        packets = bytearray()
        last_opcode = '1' if self.queue_pos >= (len(self.update_queue) - 1) else '0'
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
                self.logger.ratio_up()
        self.logger.effective_uplink()
        return packets

    # Returns true or false, indicating that next does or does not need to be called
    def check_acks(self, uplink_contents):
        # Seq number not needed for now
        opcode = int(uplink_contents[0])
        data = bytearray.fromhex(uplink_contents)[2:]
        print(data)
        rcvd_acks = []
        for ind in data:
            rcvd_acks.append(int(ind))
            self.acks_rcvd.add(ind)

        print(rcvd_acks, self.expected_acks)
        unacked = []
        if not len(rcvd_acks) == 0:
            unacked = list(set(self.expected_acks) - set(rcvd_acks))
            self.expected_acks = []
            print(unacked)

            for ind in unacked:
                if ind not in self.acks_rcvd:
                    self.logger.ratio_down()
                    self.nack(ind)

        if len(unacked) == 0 and opcode == 1:
            if not self.logger.has_logged:
                self.logger.log()
                self.logger.has_logged = True
            return False
        else:
            return True

    def nack(self, index):
        print("---X NACK: %s X---" % index)
        # Add it to reschedule queue
        self.update_queue.append(self.update_segments[index])
        print(self.update_queue)
