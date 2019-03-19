from fwtransfer.BundleTimer import BundleTimer
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


class ClassBFWUpdate(FWUpdateBase):
    def __init__(self, update_contents, dev_eui, api_instance, timeout, num_rx_windows=1):
        super(ClassBFWUpdate, self).__init__(update_contents, dev_eui, api_instance)
        self.nrx_windows = num_rx_windows
        self.timer = BundleTimer(self.nack, timeout=timeout)
        self.expected_acks = []

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
        self.__package_update()
        self.queue_pos = 0
        self.timer.start()
        last_opcode = '1' if self.queue_pos >= (len(self.update_queue) - 1) else '0'
        for i in range(0, self.queue_pos + self.nrx_windows):
            # Make the segment packet
            opcode = last_opcode if i == self.queue_pos + self.nrx_windows else '0'
            seq_num = self.update_queue[i]["seq_num"]
            index = self.update_queue[i]["index"]
            header = opcode + seq_num
            preamble = bytearray.fromhex(header + index)
            packet_arr = preamble + self.update_queue[i]["data"]
            packet = bytes(packet_arr)
            self.timer.resend_pkts.append(index)
            self.expected_acks.append(int(index))
            self.api.send_downlink(self.device, packet)
            self.queue_pos += 1

    def next(self):
        # Cancel the timer from the previous bundle, as there has been an UL
        self.timer.stop()
        self.queue_pos = self.queue_pos + 1
        last_opcode = '1' if self.queue_pos >= (len(self.update_queue) - 1) else '0'
        # Start the timer for this downlink bundle
        self.timer.start()
        for i in range(self.queue_pos, (self.queue_pos + self.nrx_windows)):
            # Make the segment packet
            opcode = last_opcode if i == self.queue_pos + self.nrx_windows else '0'
            seq_num = self.update_queue[i]["seq_num"]
            index = self.update_queue[i]["index"]
            header = opcode + seq_num
            preamble = bytearray.fromhex(header + index)
            packet_arr = preamble + self.update_queue[i]["data"]
            packet = bytes(packet_arr)
            self.timer.resend_pkts.append(index)
            self.expected_acks.append(int(index, 16))
            self.api.send_downlink(self.device, packet)
            self.queue_pos += 1

    # Returns true or false, indicating that next does or does not need to be called
    def check_acks(self, uplink_contents):
        # Seq number not needed for now
        opcode = int(uplink_contents[0])
        data = bytearray.fromhex(uplink_contents)[2:]
        rcvd_acks = []
        for ind in data:
            rcvd_acks.append(int(ind))

        unacked = list(set(self.expected_acks) - set(rcvd_acks))
        self.expected_acks = []

        for ind in unacked:
            self.nack(ind)

        if len(unacked) == 0 and opcode == 1:
            return False
        else:
            return True

    def nack(self, index):
        self.update_queue.append(self.update_segments[index])
