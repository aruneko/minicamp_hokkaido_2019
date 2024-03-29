from itertools import chain
from typing import List

from libs.rcs380 import RCS380
from libs.rcs380_packet import ReceivedPacket


class ServiceCode:
    def __init__(self, code: int):
        self.__raw_code = code
        self._number = code >> 6
        self._attribute = code & 0x3f
        self.key_version = bytearray()

    @property
    def number(self):
        return self._number.to_bytes(3, 'big')

    @property
    def attribute(self):
        return self._attribute.to_bytes(2, 'big')

    @property
    def code(self):
        return self.__raw_code.to_bytes(2, 'little')


class BlockCode:
    def __init__(self, code: int, service_offset: int, access_code: int = 0):
        self.__raw_code = code
        self.__service_offset = service_offset
        self.__access_code = access_code

    @property
    def code(self) -> bytearray:
        n, am, so = self.__raw_code, self.__access_code, self.__service_offset
        return bytearray(
            [bool(n < 256) << 7 | (am & 0x7) << 4 | (so & 0xf)]
        ) + (bytearray([n]) if n < 256 else n.to_bytes(2, 'little'))


class Type3Tag:
    def __init__(self, rcs380: RCS380):
        self.__protocol = bytearray([0x00, 0x18])
        self.__rf = bytearray([0x01, 0x01, 0x0f, 0x01])
        self.idm = bytearray()
        self.pmm = bytearray()
        self.__bitrate_type = bytearray([0x21, 0x2F])
        self.rcs380 = rcs380

    @staticmethod
    def connect():
        device = RCS380.connect()
        return Type3Tag(device)

    def send_sense_type3_command(self) -> ReceivedPacket:
        command = bytearray([0x00, 0xff, 0xff, 0x01, 0x00])
        payload = bytearray([len(command) + 1]) + command
        return self.rcs380.in_communication_rf(payload, 0.01)

    def send_type3_command(self, command_code: int, data: bytearray, timeout: float) -> ReceivedPacket:
        command = bytearray([2 + len(self.idm) + len(data), command_code]) + self.idm + data
        timeout_msec = max(min(int(timeout * 1000), 0xFFFF), 1) / 1000
        self.rcs380.in_set_rf(bytearray([0x01, 0x01, 0x0F, 0x01]))
        self.rcs380.in_set_protocol(self.rcs380.default_protocol)
        return self.rcs380.in_communication_rf(command, timeout_msec)

    def polling(self) -> ReceivedPacket:
        while True:
            self.rcs380.send_preparation_commands(self.__rf, self.__protocol)
            result = self.send_sense_type3_command()
            data = result
            if len(result.payload) == 37:
                break
        return data

    def request_system_code(self) -> ReceivedPacket:
        a = self.pmm[3] & 7
        e = self.pmm[3] >> 6
        timeout = max(302E-6 * (a + 1) * 4 ** e, 0.002)
        response = self.send_type3_command(0x0C, bytearray(), timeout)
        return response

    def request_service(self, service_codes: List[ServiceCode]) -> ReceivedPacket:
        a = self.pmm[2] & 7
        b = self.pmm[2] >> 3 & 7
        e = self.pmm[2] >> 6
        timeout = 302E-6 * ((b + 1) * len(service_codes) + a + 1) * 4 ** e
        payload = bytearray([len(service_codes)]) + bytearray(chain.from_iterable([sc.code for sc in service_codes]))
        response = self.send_type3_command(0x02, payload, timeout)
        return response

    def read_without_encryption(self, service_codes: List[ServiceCode], blocks: List[BlockCode]) -> ReceivedPacket:
        a = self.pmm[5] & 7
        b = self.pmm[5] >> 3 & 7
        e = self.pmm[5] >> 6
        timeout = 302.1E-6 * ((b + 1) * len(blocks) + a + 1) * 4 ** e
        payload = bytearray([len(service_codes)]) \
            + bytearray(chain.from_iterable([sc.code for sc in service_codes])) \
            + bytearray([len(blocks)]) \
            + bytearray(chain.from_iterable([bc.code for bc in blocks]))
        response = self.send_type3_command(0x06, payload, timeout)
        return response

    def set_idm_and_pmm(self, polling_response: ReceivedPacket):
        self.idm = polling_response.data[9:17]
        self.pmm = polling_response.data[17:25]

    def disconnect(self):
        self.rcs380.disconnect()
