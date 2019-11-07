from libs import calc_checksum, calc_data_length


class Packet:
    def __init__(self, payload: bytearray):
        self.payload = payload

    @property
    def header(self) -> bytearray:
        return self.payload[:5]

    @property
    def footer(self) -> int:
        return self.payload[-1]


class RCS380Packet(Packet):
    def __init__(self, payload: bytearray):
        super().__init__(payload)

    @property
    def data_length_as_bytes(self) -> bytearray:
        return self.payload[5:7]

    @property
    def data_length(self) -> int:
        return int.from_bytes(self.payload[5:7], 'little')

    @property
    def data_length_checksum(self) -> int:
        return self.payload[7]

    @property
    def data(self) -> bytearray:
        return self.payload[8:8+self.data_length]

    @property
    def data_checksum(self) -> int:
        return self.payload[8+self.data_length]

    @property
    def format_data(self):
        return " ".join([f"{n:02x}" for n in self.data])


class AckPacket(Packet):
    def __init__(self):
        ack_packet = bytearray([0x00, 0x00, 0xff, 0x00, 0xff, 0x00])
        super().__init__(ack_packet)


class SendPacket(RCS380Packet):
    def __init__(self, data: bytearray):
        header = bytearray([0x00, 0x00, 0xff, 0xff, 0xff])
        data_length = calc_data_length(data)
        data_length_checksum = calc_checksum(data_length)
        data_checksum = calc_checksum(data)
        footer = bytearray([0x00])
        payload = header + data_length + data_length_checksum + data + data_checksum + footer

        super().__init__(payload)


class ReceivedPacket(RCS380Packet):
    def __init__(self, payload):
        super().__init__(payload)


class SuccessPacket(ReceivedPacket):
    def __init__(self, payload):
        super().__init__(payload)


class FailurePacket(ReceivedPacket):
    def __init__(self, payload):
        super().__init__(payload)
