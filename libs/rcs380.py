import math
from typing import Union

import usb1

from libs.rcs380_packet import AckPacket, SendPacket, ReceivedPacket, FailurePacket, SuccessPacket


class RCS380:
    def __init__(self, handle: usb1.USBDeviceHandle):
        self.__ack_packet = AckPacket()
        self.__max_receive_size = 290
        self.default_protocol = bytearray([
            0x00, 0x18, 0x01, 0x01, 0x02, 0x01, 0x03, 0x00, 0x04, 0x00, 0x05, 0x00, 0x06,
            0x00, 0x07, 0x08, 0x08, 0x00, 0x09, 0x00, 0x0a, 0x00, 0x0b, 0x00, 0x0c, 0x00,
            0x0e, 0x04, 0x0f, 0x00, 0x10, 0x00, 0x11, 0x00, 0x12, 0x00, 0x13, 0x06
        ])
        self.__frame_waiting_time = 2.474516
        self.__delta_frame_waiting_time = 49152 / 13.56e6
        self.timeout = self.__frame_waiting_time + self.__delta_frame_waiting_time
        self.device = handle

    @staticmethod
    def connect(vendor_id: int = 0x054c, product_id: int = 0x06c3):
        usb_context = usb1.USBContext()
        handle = usb_context.openByVendorIDAndProductID(vendor_id, product_id, skip_on_error=True)
        handle.setConfiguration(1)
        handle.claimInterface(0)
        return RCS380(handle)

    def write(self, packet: Union[AckPacket, SendPacket]):
        self.device.bulkWrite(2, packet.payload)

    def read(self) -> ReceivedPacket:
        result: bytearray = self.device.bulkRead(1, self.__max_receive_size)
        error_packet_header = bytearray([0x00, 0x00, 0xff, 0x00, 0xff])
        if result[0:5] == error_packet_header:
            return FailurePacket(bytearray([0x00, 0x00, 0xff, 0x00, 0xff, 0x00, 0x00, 0x00, 0x00]))
        else:
            return SuccessPacket(result)

    def build_command(self, command_code: int, raw_command: bytearray) -> SendPacket:
        header = 0xd6
        command = bytearray(bytearray([header, command_code]) + raw_command)
        return SendPacket(command)

    def parse_timeout(self, timeout_ms: float) -> bytearray:
        hex_timeout = (math.floor(timeout_ms * 1000) + 1) * 10
        return bytearray(hex_timeout.to_bytes(2, 'little'))

    def send_type_b_command_and_receive_result(self, command_code: int, raw_command: bytearray) -> ReceivedPacket:
        command = self.build_command(command_code, raw_command)
        self.write(command)

        self.read()
        return self.read()

    def send_ack(self):
        self.write(self.__ack_packet)

    def set_command_type(self):
        command_type = bytearray([0x01])
        self.send_type_b_command_and_receive_result(0x2a, command_type)

    def switch_rf(self):
        rf = bytearray([0x00])
        self.send_type_b_command_and_receive_result(0x06, rf)

    def in_set_rf(self, rf: bytearray):
        self.send_type_b_command_and_receive_result(0x00, rf)

    def in_set_protocol(self, protocol: bytearray):
        self.send_type_b_command_and_receive_result(0x02, protocol)

    def in_communication_rf(self, data: bytearray, timeout_ms: float) -> ReceivedPacket:
        timeout = self.parse_timeout(timeout_ms)
        command = timeout + data
        return self.send_type_b_command_and_receive_result(0x04, command)

    def send_preparation_commands(self, rf: bytearray, protocol: bytearray):
        self.in_set_rf(rf)
        self.in_set_protocol(self.default_protocol)
        self.in_set_protocol(protocol)

    def init_device(self):
        self.send_ack()
        self.set_command_type()
        self.switch_rf()
        self.switch_rf()

    def disconnect(self):
        self.switch_rf()
        self.send_ack()
        self.device.close()
