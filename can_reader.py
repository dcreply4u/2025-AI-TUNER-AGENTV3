"""
CAN Reader Module
Handles reading and decoding CAN bus messages
"""

import can


class CANReader:
    """CAN bus reader with signal decoding"""
    
    def __init__(self, channel, bustype, mapper):
        self.bus = can.interface.Bus(channel=channel, bustype=bustype)
        self.mapper = mapper

    def read(self):
        """Read and decode a CAN message"""
        msg = self.bus.recv(timeout=1)
        if msg:
            decoded_list = self.mapper.decode(msg)
            return msg, decoded_list
        return None, None

