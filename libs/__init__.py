def calc_data_length(b: bytearray) -> bytearray:
    raw_length = len(b).to_bytes(2, 'little')
    return bytearray(raw_length)


def calc_checksum(b: bytearray) -> bytearray:
    checksum = (256 - sum(b)) % 256
    return bytearray([checksum])
